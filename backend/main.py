import secrets
import string
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import init_db, get_db, async_session
from models import Game, GameStatus, Color
from schemas import (
    CreateGameResponse,
    SubmitPromptRequest,
    SubmitPromptResponse,
    GameResponse,
    PromptSubmittedEvent,
)
from sse_manager import sse_manager
from game_engine import run_game

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="VibeChess API",
    description="A chess game where AI plays on your behalf based on your prompts",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_game_code(length: int = 6) -> str:
    """Generate a random alphanumeric game code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "vibechess"}


@app.post("/games", response_model=CreateGameResponse)
async def create_game(db: AsyncSession = Depends(get_db)):
    """Create a new game and return the game code for sharing."""
    # Generate unique game code
    while True:
        game_code = generate_game_code()
        existing = await db.execute(select(Game).where(Game.game_code == game_code))
        if not existing.scalar_one_or_none():
            break

    game = Game(game_code=game_code)
    db.add(game)
    await db.commit()

    logger.info(f"Created new game: {game_code}")
    return CreateGameResponse(game_code=game_code)


@app.post("/games/{game_code}/prompt", response_model=SubmitPromptResponse)
async def submit_prompt(
    game_code: str,
    request: SubmitPromptRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a prompt for a player (white or black)."""
    result = await db.execute(select(Game).where(Game.game_code == game_code))
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != GameStatus.WAITING_FOR_PROMPTS:
        raise HTTPException(status_code=400, detail="Game has already started")

    # Check if prompt already submitted for this color
    if request.color == Color.WHITE:
        if game.white_prompt is not None:
            raise HTTPException(status_code=400, detail="White prompt already submitted")
        game.white_prompt = request.prompt
    else:
        if game.black_prompt is not None:
            raise HTTPException(status_code=400, detail="Black prompt already submitted")
        game.black_prompt = request.prompt

    await db.commit()

    # Broadcast prompt submitted event
    await sse_manager.broadcast(
        game_code,
        PromptSubmittedEvent(color=request.color)
    )

    logger.info(f"Game {game_code}: {request.color.value} prompt submitted")

    # Check if both prompts are now submitted
    game_started = False
    if game.white_prompt is not None and game.black_prompt is not None:
        game_started = True
        # Start the game in a background task
        async def start_game():
            async with async_session() as session:
                await run_game(game_code, session)

        background_tasks.add_task(start_game)
        logger.info(f"Game {game_code}: Both prompts submitted, starting game")

    return SubmitPromptResponse(
        message=f"{request.color.value.capitalize()} prompt submitted successfully",
        game_started=game_started
    )


@app.get("/games/{game_code}", response_model=GameResponse)
async def get_game(game_code: str, db: AsyncSession = Depends(get_db)):
    """Get the current state of a game."""
    result = await db.execute(
        select(Game)
        .where(Game.game_code == game_code)
        .options(selectinload(Game.moves))
    )
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Sort moves by move_number and color
    sorted_moves = sorted(game.moves, key=lambda m: (m.move_number, m.color != Color.WHITE))

    return GameResponse(
        game_code=game.game_code,
        status=game.status,
        white_prompt=game.white_prompt,
        black_prompt=game.black_prompt,
        board_fen=game.board_fen,
        current_turn=game.current_turn,
        result=game.result,
        moves=sorted_moves,
        created_at=game.created_at
    )


@app.get("/games/{game_code}/events")
async def game_events(
    game_code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events endpoint for real-time game updates.

    Subscribe to this endpoint to receive move events, game over events, etc.
    If the game was paused (no viewers), this will resume it.
    """
    # Verify game exists
    result = await db.execute(select(Game).where(Game.game_code == game_code))
    game = result.scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Resume paused game when viewer connects
    if game.is_paused and game.status == GameStatus.IN_PROGRESS:
        logger.info(f"Game {game_code}: Viewer connected, resuming paused game")
        # Mark as not paused immediately to prevent duplicate restarts
        game.is_paused = False
        await db.commit()

        # Restart the game loop
        async def resume_game():
            async with async_session() as session:
                await run_game(game_code, session)

        background_tasks.add_task(resume_game)

    async def event_generator():
        async for event in sse_manager.subscribe(game_code):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
