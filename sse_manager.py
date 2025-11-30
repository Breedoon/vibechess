import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator
from pydantic import BaseModel


class SSEManager:
    """Manages Server-Sent Events connections and broadcasting."""

    def __init__(self):
        # game_code -> list of asyncio.Queue
        self._connections: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def subscribe(self, game_code: str) -> AsyncGenerator[str, None]:
        """Subscribe to events for a game. Yields SSE-formatted strings."""
        queue: asyncio.Queue = asyncio.Queue()
        self._connections[game_code].append(queue)

        try:
            while True:
                event = await queue.get()
                if event is None:  # Shutdown signal
                    break
                yield event
        finally:
            self._connections[game_code].remove(queue)
            if not self._connections[game_code]:
                del self._connections[game_code]

    async def broadcast(self, game_code: str, event: BaseModel | dict) -> None:
        """Broadcast an event to all subscribers of a game."""
        if game_code not in self._connections:
            return

        if isinstance(event, BaseModel):
            data = event.model_dump_json()
        else:
            data = json.dumps(event)

        sse_message = f"data: {data}\n\n"

        for queue in self._connections[game_code]:
            await queue.put(sse_message)

    async def close_game(self, game_code: str) -> None:
        """Close all connections for a game."""
        if game_code not in self._connections:
            return

        for queue in self._connections[game_code]:
            await queue.put(None)

    def get_subscriber_count(self, game_code: str) -> int:
        """Get the number of active subscribers for a game."""
        return len(self._connections.get(game_code, []))


# Global SSE manager instance
sse_manager = SSEManager()
