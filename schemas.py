from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from models import GameStatus, Color


# Request schemas
class CreateGameResponse(BaseModel):
    game_code: str


class SubmitPromptRequest(BaseModel):
    color: Color
    prompt: str = Field(min_length=1, max_length=2000)


class SubmitPromptResponse(BaseModel):
    message: str
    game_started: bool = False


# Response schemas
class MoveResponse(BaseModel):
    move_number: int
    color: Color
    move_uci: str
    move_san: str
    comment: Optional[str]
    was_fallback: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GameResponse(BaseModel):
    game_code: str
    status: GameStatus
    white_prompt: Optional[str]
    black_prompt: Optional[str]
    board_fen: str
    current_turn: Color
    result: Optional[str]
    moves: List[MoveResponse]
    created_at: datetime

    class Config:
        from_attributes = True


# SSE event schemas
class MoveEvent(BaseModel):
    type: str = "move"
    move_number: int
    color: Color
    move_uci: str
    move_san: str
    comment: Optional[str]
    was_fallback: bool
    board_fen: str
    board_ascii: str


class GameOverEvent(BaseModel):
    type: str = "game_over"
    result: str
    termination: str


class PromptSubmittedEvent(BaseModel):
    type: str = "prompt_submitted"
    color: Color


class GameStartedEvent(BaseModel):
    type: str = "game_started"
