from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Enum, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class GameStatus(str, enum.Enum):
    WAITING_FOR_PROMPTS = "waiting_for_prompts"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Color(str, enum.Enum):
    WHITE = "white"
    BLACK = "black"


class Game(Base):
    __tablename__ = "games"

    game_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus), default=GameStatus.WAITING_FOR_PROMPTS
    )
    white_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    black_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    white_session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    black_session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    board_fen: Mapped[str] = mapped_column(
        String(100),
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )
    current_turn: Mapped[Color] = mapped_column(Enum(Color), default=Color.WHITE)
    result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    moves: Mapped[List["Move"]] = relationship(back_populates="game", cascade="all, delete-orphan")


class Move(Base):
    __tablename__ = "moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_code: Mapped[str] = mapped_column(ForeignKey("games.game_code"))
    move_number: Mapped[int] = mapped_column(Integer)
    color: Mapped[Color] = mapped_column(Enum(Color))
    move_uci: Mapped[str] = mapped_column(String(10))
    move_san: Mapped[str] = mapped_column(String(10))
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    was_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="moves")
