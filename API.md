# VibeChess API Reference

**Base URL:** `http://44.201.8.210`

---

## Endpoints

### 1. Health Check

```
GET /
```

**Response:**
```json
{"status": "ok", "service": "vibechess"}
```

---

### 2. Create Game

```
POST /games
```

**Request:** (no body)

**Response:**
```json
{
  "game_code": "QJCXX2"
}
```

---

### 3. Submit Prompt

```
POST /games/{game_code}/prompt
Content-Type: application/json
```

**Request:**
```json
{
  "color": "white",
  "prompt": "Play aggressively, control the center, aim for quick checkmate"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `color` | string | `"white"` or `"black"` |
| `prompt` | string | Strategy instructions (1-2000 characters) |

**Response:**
```json
{
  "message": "White prompt submitted successfully",
  "game_started": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Confirmation message |
| `game_started` | boolean | `true` when both prompts submitted, game begins |

**Errors:**
- `404`: Game not found
- `400`: "Game has already started" or "White/Black prompt already submitted"

---

### 4. Get Game State

```
GET /games/{game_code}
```

**Response:**
```json
{
  "game_code": "QJCXX2",
  "status": "in_progress",
  "white_prompt": "Play aggressively...",
  "black_prompt": "Play defensively...",
  "board_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "current_turn": "black",
  "result": null,
  "moves": [
    {
      "move_number": 1,
      "color": "white",
      "move_uci": "e2e4",
      "move_san": "e4",
      "comment": "Opening with King's Pawn to control the center.",
      "was_fallback": false,
      "created_at": "2025-11-30T21:41:28.696425"
    }
  ],
  "created_at": "2025-11-30T21:40:00.000000"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `game_code` | string | 6-character game identifier |
| `status` | string | `"waiting_for_prompts"` \| `"in_progress"` \| `"completed"` |
| `white_prompt` | string \| null | White player's strategy prompt |
| `black_prompt` | string \| null | Black player's strategy prompt |
| `board_fen` | string | Current board state in FEN notation |
| `current_turn` | string | `"white"` \| `"black"` |
| `result` | string \| null | `null` \| `"white_wins"` \| `"black_wins"` \| `"draw"` |
| `moves` | array | List of moves played |
| `created_at` | string | ISO 8601 timestamp |

**Move Object:**

| Field | Type | Description |
|-------|------|-------------|
| `move_number` | integer | Move number (increments after black's turn) |
| `color` | string | `"white"` \| `"black"` |
| `move_uci` | string | Move in UCI notation (e.g., `"e2e4"`) |
| `move_san` | string | Move in SAN notation (e.g., `"e4"`) |
| `comment` | string \| null | LLM's reasoning for the move |
| `was_fallback` | boolean | `true` if LLM gave invalid move, random legal move used |
| `created_at` | string | ISO 8601 timestamp |

---

### 5. SSE Events Stream

```
GET /games/{game_code}/events
Accept: text/event-stream
```

Subscribe to real-time game updates via Server-Sent Events.

**Event Types:**

#### Prompt Submitted
Sent when a player submits their prompt.
```json
{"type": "prompt_submitted", "color": "white"}
```

#### Game Started
Sent when both prompts are submitted and game begins.
```json
{"type": "game_started"}
```

#### Move Made
Sent after each move is played.
```json
{
  "type": "move",
  "move_number": 1,
  "color": "white",
  "move_uci": "e2e4",
  "move_san": "e4",
  "comment": "Opening with King's Pawn to control the center.",
  "was_fallback": false,
  "board_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "board_ascii": "r n b q k b n r\np p p p p p p p\n. . . . . . . .\n. . . . . . . .\n. . . . P . . .\n. . . . . . . .\nP P P P . P P P\nR N B Q K B N R"
}
```

#### Game Over
Sent when the game ends.
```json
{
  "type": "game_over",
  "result": "white_wins",
  "termination": "checkmate"
}
```

| Termination | Description |
|-------------|-------------|
| `checkmate` | King is in check with no legal moves |
| `stalemate` | No legal moves but not in check |
| `insufficient_material` | Neither side can checkmate |
| `fifty_moves` | 50 moves without pawn move or capture |
| `threefold_repetition` | Same position occurred 3 times |
| `fivefold_repetition` | Same position occurred 5 times |
| `seventyfive_moves` | 75 moves without pawn move or capture |

---

## Full Example Flow

```bash
# 1. Create game
curl -X POST http://44.201.8.210/games
# {"game_code":"ABC123"}

# 2. Player 1 submits white prompt
curl -X POST http://44.201.8.210/games/ABC123/prompt \
  -H "Content-Type: application/json" \
  -d '{"color": "white", "prompt": "Play the Italian Game opening, then attack kingside"}'
# {"message":"White prompt submitted successfully","game_started":false}

# 3. Player 2 submits black prompt
curl -X POST http://44.201.8.210/games/ABC123/prompt \
  -H "Content-Type: application/json" \
  -d '{"color": "black", "prompt": "Play solid defense, castle early, look for counterattack"}'
# {"message":"Black prompt submitted successfully","game_started":true}

# 4. Subscribe to events (in browser or with curl)
curl -N http://44.201.8.210/games/ABC123/events

# 5. Or poll game state
curl http://44.201.8.210/games/ABC123
```

---

## Data Types Summary

| Type | Values |
|------|--------|
| **Color** | `"white"` \| `"black"` |
| **GameStatus** | `"waiting_for_prompts"` \| `"in_progress"` \| `"completed"` |
| **Result** | `null` \| `"white_wins"` \| `"black_wins"` \| `"draw"` |
| **Termination** | `"checkmate"` \| `"stalemate"` \| `"insufficient_material"` \| `"fifty_moves"` \| `"threefold_repetition"` \| `"fivefold_repetition"` \| `"seventyfive_moves"` |
