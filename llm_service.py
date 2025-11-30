from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from Claude Code CLI."""
    text: str
    session_id: str | None
    error: str | None = None


async def call_claude_cli(
    prompt: str,
    session_id: str | None = None,
    system_prompt: str | None = None
) -> LLMResponse:
    """
    Call Claude Code CLI with a prompt.

    Args:
        prompt: The prompt to send to Claude
        session_id: Optional session ID to resume a conversation
        system_prompt: Optional system prompt for first message in session

    Returns:
        LLMResponse with the text response and session ID
    """
    cmd = ["claude", "-p", prompt, "--output-format", "json"]

    if session_id:
        cmd.extend(["--resume", session_id])
    elif system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    logger.info(f"Calling Claude CLI: {' '.join(cmd[:4])}...")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Claude CLI error: {error_msg}")
            return LLMResponse(text="", session_id=session_id, error=error_msg)

        response_text = stdout.decode()

        try:
            response_data = json.loads(response_text)
            return LLMResponse(
                text=response_data.get("result", ""),
                session_id=response_data.get("session_id", session_id)
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, treat the whole output as text
            logger.warning("Failed to parse Claude CLI JSON response, using raw text")
            return LLMResponse(text=response_text, session_id=session_id)

    except FileNotFoundError:
        error_msg = "Claude CLI not found. Please install claude-code."
        logger.error(error_msg)
        return LLMResponse(text="", session_id=None, error=error_msg)
    except Exception as e:
        error_msg = f"Error calling Claude CLI: {str(e)}"
        logger.error(error_msg)
        return LLMResponse(text="", session_id=session_id, error=error_msg)


def build_chess_prompt(
    color: str,
    user_strategy: str,
    board_ascii: str,
    legal_moves: List[str]
) -> str:
    """Build the prompt for asking Claude to make a chess move."""
    return f"""You are playing chess as {color}.
Your strategy: {user_strategy}

Current board position:
{board_ascii}

Legal moves available: {', '.join(legal_moves)}

Respond with your move and brief reasoning in this exact format:
MOVE: <move in SAN notation like e4, Nf3, O-O>
COMMENT: <brief explanation of your reasoning>

IMPORTANT: Your MOVE must be one of the legal moves listed above."""


def build_system_prompt(color: str) -> str:
    """Build the system prompt for a new chess game session."""
    return f"""You are a chess AI playing as {color}. You will be given the current board state and asked to make moves.

Rules:
1. Always respond with a legal move in SAN notation (e.g., e4, Nf3, Bxc6, O-O)
2. Format your response as:
   MOVE: <your move>
   COMMENT: <brief reasoning>
3. Play according to the strategy provided by your player
4. Consider the opponent's possible responses

You will receive the board as ASCII art where:
- Uppercase letters = White pieces (K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn)
- Lowercase letters = Black pieces
- Dots (.) = Empty squares"""
