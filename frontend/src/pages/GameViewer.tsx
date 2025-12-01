import { useParams } from "react-router-dom";
import { Chessboard } from "react-chessboard";
import { useGameEvents, ChatMessage } from "@/hooks/useGameEvents";
import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Loader2, Users } from "lucide-react";
import { API_BASE_URL } from "@/config/api";

interface GameInfo {
  game_code: string;
  status: string;
  white_prompt: string | null;
  black_prompt: string | null;
}

const GameViewer = () => {
  const { gameCode } = useParams<{ gameCode: string }>();
  const { messages, gameState, isConnected } = useGameEvents(gameCode || "");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [gameInfo, setGameInfo] = useState<GameInfo | null>(null);
  const [isWaiting, setIsWaiting] = useState(true);
  // Fetch game info and check waiting status
  useEffect(() => {
    if (!gameCode) return;

    const checkGameStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/games/${gameCode}`);
        if (response.ok) {
          const data: GameInfo = await response.json();
          setGameInfo(data);
          // Check if both prompts are submitted
          const bothPromptsSubmitted = data.white_prompt !== null && data.black_prompt !== null;
          setIsWaiting(!bothPromptsSubmitted);
        }
      } catch (error) {
        console.error("Error checking game status:", error);
      }
    };

    // Initial check
    checkGameStatus();

    // Poll while waiting for opponent
    const interval = setInterval(() => {
      if (isWaiting) {
        checkGameStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [gameCode, isWaiting]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Guard for missing gameCode (after all hooks)
  if (!gameCode) {
    return <div className="min-h-screen flex items-center justify-center">Game code not found</div>;
  }

  const waitingForColor = gameInfo?.white_prompt === null ? "white" : "black";
  const joinLink = `${window.location.origin}/join/${gameCode}`;

  // Show waiting state if opponent hasn't joined
  if (isWaiting && gameInfo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20 flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
              <Users className="w-8 h-8 text-primary" />
            </div>
            <h1 className="text-2xl font-bold">Waiting for Opponent</h1>
            <p className="text-muted-foreground">
              Share the code below with your opponent to start the game
            </p>
          </div>

          {/* Game Code */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">Game Code</label>
            <input
              type="text"
              readOnly
              value={gameCode}
              className="w-full bg-secondary rounded-lg px-4 py-3 font-mono text-2xl tracking-wider text-center select-all cursor-text"
              onClick={(e) => (e.target as HTMLInputElement).select()}
            />
          </div>

          {/* Join Link */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">Or share this link</label>
            <input
              type="text"
              readOnly
              value={joinLink}
              className="w-full bg-secondary rounded-lg px-3 py-2 font-mono text-sm select-all cursor-text"
              onClick={(e) => (e.target as HTMLInputElement).select()}
            />
          </div>

          {/* Status */}
          <div className="flex items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Waiting for {waitingForColor} player to join...</span>
          </div>
        </Card>
      </div>
    );
  }

  const renderMessage = (msg: ChatMessage) => {
    const isWhite = msg.player === "white";

    return (
      <div
        key={msg.id}
        className={`flex ${isWhite ? "justify-start" : "justify-end"} mb-4`}
      >
        <div
          className={`max-w-[80%] rounded-2xl px-4 py-3 ${
            isWhite
              ? "bg-blue-100 text-blue-900"
              : "bg-gray-800 text-white"
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{isWhite ? "♔" : "♚"}</span>
            <span className="font-semibold text-sm">
              {isWhite ? "White" : "Black"}
            </span>
            <span className="text-xs opacity-70">
              {msg.timestamp.toLocaleTimeString()}
            </span>
          </div>

          <div className="flex items-start gap-2">
            {msg.type === "thinking" && <span>💭</span>}
            {msg.type === "action" && <span>♟️</span>}
            {msg.type === "game_over" && <span>🏁</span>}
            <p className={msg.type === "thinking" ? "italic" : "font-medium"}>
              {msg.message}
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 text-center space-y-2">
          <h1 className="text-3xl font-bold">Game: {gameCode}</h1>
          <div className="flex items-center justify-center gap-2">
            <Badge variant={isConnected ? "default" : "destructive"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
            {gameState?.status && (
              <Badge variant="outline">{gameState.status}</Badge>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-[1fr_400px] gap-6">
          {/* Chess Board */}
          <div className="space-y-4">
            <div className="bg-card rounded-xl p-6 border border-border">
              <Chessboard
                position={gameState?.fen || "start"}
                arePiecesDraggable={false}
                animationDuration={200}
              />
            </div>

            {/* Move History */}
            {gameState?.pgn && (
              <div className="bg-card rounded-xl p-6 border border-border">
                <h3 className="font-semibold mb-2">Move History</h3>
                <p className="text-sm text-muted-foreground font-mono">
                  {gameState.pgn}
                </p>
              </div>
            )}
          </div>

          {/* Chat Panel */}
          <div className="bg-card rounded-xl border border-border overflow-hidden flex flex-col h-[calc(100vh-200px)]">
            <div className="p-4 border-b border-border">
              <h2 className="font-semibold text-lg">Agent Reasoning</h2>
              <p className="text-sm text-muted-foreground">
                {messages.length} messages
              </p>
            </div>

            <ScrollArea className="flex-1 p-4">
              {messages.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  Waiting for agents to start thinking...
                </div>
              ) : (
                <>
                  {messages.map(renderMessage)}
                  <div ref={messagesEndRef} />
                </>
              )}
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameViewer;
