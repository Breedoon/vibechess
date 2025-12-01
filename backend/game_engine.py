from __future__ import annotations
import asyncio
import random
import re
import logging
from typing import List, Tuple, Optional
import chess
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models import Game, Move, GameStatus, Color
from schemas import MoveEvent, GameOverEvent, GameStartedEvent
from sse_manager import sse_manager
from llm_service import call_claude_cli, build_chess_prompt, build_system_prompt, parse_chess_response
from commentary_service import commentary_service

logger = logging.getLogger(__name__)


def parse_llm_response(response_text: str) -> tuple[str | None, str | None]:
    """
    Parse the LLM response to extract move and comment.

    Returns:
        (move, comment) tuple. Move may be None if parsing fails.
    """
    move = None
    comment = None

    # Try to find MOVE: pattern
    move_match = re.search(r'MOVE:\s*([A-Za-z0-9\-+#=xO]+)', response_text, re.IGNORECASE)
    if move_match:
        move = move_match.group(1).strip()

    # Try to find COMMENT: pattern
    comment_match = re.search(r'COMMENT:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE | re.DOTALL)
    if comment_match:
        comment = comment_match.group(1).strip()

    # If no structured format, try to extract just the first word that looks like a move
    if not move:
        # Common chess move patterns
        potential_moves = re.findall(r'\b([KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|O-O(?:-O)?)\b', response_text)
        if potential_moves:
            move = potential_moves[0]

    return move, comment


def get_legal_moves_san(board: chess.Board) -> List[str]:
    """Get all legal moves in SAN notation."""
    return [board.san(move) for move in board.legal_moves]


def validate_and_get_move(board: chess.Board, move_str: str | None) -> chess.Move | None:
    """
    Validate a move string and return the chess.Move object.

    Returns None if the move is invalid.
    """
    if not move_str:
        return None

    try:
        # Try parsing as SAN first
        return board.parse_san(move_str)
    except chess.InvalidMoveError:
        pass
    except chess.AmbiguousMoveError:
        pass

    try:
        # Try parsing as UCI
        return board.parse_uci(move_str)
    except chess.InvalidMoveError:
        pass

    return None


def get_random_legal_move(board: chess.Board) -> chess.Move:
    """Get a random legal move."""
    return random.choice(list(board.legal_moves))


def get_game_result(board: chess.Board) -> tuple[str, str]:
    """
    Get the game result and termination reason.

    Returns:
        (result, termination) tuple
    """
    outcome = board.outcome()
    if outcome is None:
        return "unknown", "unknown"

    if outcome.winner is None:
        result = "draw"
    elif outcome.winner:
        result = "white_wins"
    else:
        result = "black_wins"

    termination_map = {
        chess.Termination.CHECKMATE: "checkmate",
        chess.Termination.STALEMATE: "stalemate",
        chess.Termination.INSUFFICIENT_MATERIAL: "insufficient_material",
        chess.Termination.SEVENTYFIVE_MOVES: "seventyfive_moves",
        chess.Termination.FIVEFOLD_REPETITION: "fivefold_repetition",
        chess.Termination.FIFTY_MOVES: "fifty_moves",
        chess.Termination.THREEFOLD_REPETITION: "threefold_repetition",
    }
    termination = termination_map.get(outcome.termination, "unknown")

    return result, termination


async def run_game(game_code: str, db: AsyncSession) -> None:
    """
    Run the main game loop for a chess game.

    This function is called as a background task when both players have submitted prompts.
    """
    logger.info(f"Starting game loop for game {game_code}")

    # Load game from database with moves eagerly loaded
    result = await db.execute(
        select(Game)
        .where(Game.game_code == game_code)
        .options(selectinload(Game.moves))
    )
    game = result.scalar_one_or_none()

    if not game:
        logger.error(f"Game {game_code} not found")
        return

    # Initialize board from FEN
    board = chess.Board(game.board_fen)

    # Broadcast game started event
    await sse_manager.broadcast(game_code, GameStartedEvent())

    # Update game status - mark as running (not paused)
    game.status = GameStatus.IN_PROGRESS
    game.is_paused = False
    await db.commit()

    # Get current move number from existing moves
    move_count_result = await db.execute(
        select(func.count(Move.id)).where(Move.game_code == game_code)
    )
    existing_moves = move_count_result.scalar() or 0
    move_number = existing_moves // 2 + 1

    # Wait for at least one SSE subscriber to connect before starting
    # Poll every 100ms for up to 10 seconds
    max_wait = 100  # 10 seconds (100 * 100ms)
    for _ in range(max_wait):
        if sse_manager.get_subscriber_count(game_code) > 0:
            break
        await asyncio.sleep(0.1)
    else:
        # No subscribers connected after 10 seconds - pause immediately
        logger.info(f"Game {game_code}: No viewers connected after 10s wait, pausing game loop")
        game.is_paused = True
        await db.commit()
        return

    while not board.is_game_over():
        # Exit if no viewers - mark as paused so it can be resumed later
        if sse_manager.get_subscriber_count(game_code) == 0:
            logger.info(f"Game {game_code}: All viewers disconnected, pausing game loop")
            game.is_paused = True
            await db.commit()
            return  # Exit entirely - will be resumed when someone reconnects

        current_color = Color.WHITE if board.turn else Color.BLACK
        is_white = current_color == Color.WHITE

        # Get the right prompt and session
        user_strategy = game.white_prompt if is_white else game.black_prompt
        session_id = game.white_session_id if is_white else game.black_session_id

        # Build prompt for LLM
        prompt = build_chess_prompt(
            color=current_color.value,
            user_strategy=user_strategy,
            board_ascii=str(board),
            legal_moves=get_legal_moves_san(board)
        )

        # Call Claude CLI
        if session_id:
            llm_response = await call_claude_cli(prompt, session_id=session_id)
        else:
            # First move for this color - include system prompt
            system_prompt = build_system_prompt(current_color.value)
            llm_response = await call_claude_cli(prompt, system_prompt=system_prompt)

        # Update session ID if we got a new one
        if llm_response.session_id:
            if is_white:
                game.white_session_id = llm_response.session_id
            else:
                game.black_session_id = llm_response.session_id

        # Parse LLM response using new parser
        parsed = parse_chess_response(llm_response.text)
        move_str = parsed.move
        comment = parsed.comment
        commentary = parsed.commentary
        my_emotion = parsed.my_emotion
        opponent_emotion = parsed.opponent_emotion

        # Validate move
        move = validate_and_get_move(board, move_str)
        was_fallback = False

        if move is None:
            logger.warning(f"Invalid move from LLM: '{move_str}', using random fallback")
            move = get_random_legal_move(board)
            was_fallback = True
            if comment:
                comment = f"[FALLBACK - LLM suggested invalid move '{move_str}'] {comment}"
            else:
                comment = f"[FALLBACK - LLM suggested invalid move '{move_str}']"

        # Get SAN before pushing (board state changes after push)
        move_san = board.san(move)
        move_uci = move.uci()

        # Apply move
        board.push(move)

        # Update game state
        game.board_fen = board.fen()
        game.current_turn = Color.BLACK if is_white else Color.WHITE

        # Record move in database
        db_move = Move(
            game_code=game_code,
            move_number=move_number,
            color=current_color,
            move_uci=move_uci,
            move_san=move_san,
            comment=comment,
            was_fallback=was_fallback
        )
        db.add(db_move)
        await db.commit()

        # Generate commentary audio if available
        commentary_audio = None
        if commentary:
            commentary_audio = await commentary_service.generate_audio(commentary)

        # Broadcast move event
        move_event = MoveEvent(
            move_number=move_number,
            color=current_color,
            move_uci=move_uci,
            move_san=move_san,
            comment=comment,
            was_fallback=was_fallback,
            board_fen=board.fen(),
            board_ascii=str(board),
            commentary=commentary,
            commentary_audio=commentary_audio,
            my_emotion=my_emotion,
            opponent_emotion=opponent_emotion
        )
        await sse_manager.broadcast(game_code, move_event)

        # Increment move number after black's turn
        if not is_white:
            move_number += 1

        logger.info(f"Game {game_code}: {current_color.value} played {move_san}")

    # Game over
    result, termination = get_game_result(board)
    game.status = GameStatus.COMPLETED
    game.result = result
    await db.commit()

    # Broadcast game over event
    game_over_event = GameOverEvent(result=result, termination=termination)
    await sse_manager.broadcast(game_code, game_over_event)

    logger.info(f"Game {game_code} completed: {result} by {termination}")
