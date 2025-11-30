import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Loader2, Crown, Sparkles } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/config/api";

type Color = "white" | "black";

const GameSetup = () => {
  const [selectedColor, setSelectedColor] = useState<Color>("white");
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleCreateGame = async () => {
    if (!prompt.trim()) {
      toast({
        title: "Missing Prompt",
        description: "Please provide a prompt for your agent",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      // Create game
      const createResponse = await fetch(`${API_BASE_URL}/games`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!createResponse.ok) throw new Error("Failed to create game");

      const { game_code } = await createResponse.json();

      // Submit prompt for selected color
      const promptResponse = await fetch(
        `${API_BASE_URL}/games/${game_code}/prompt`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            color: selectedColor,
            prompt: prompt,
          }),
        }
      );

      if (!promptResponse.ok) throw new Error("Failed to submit prompt");

      // Navigate to game viewer (will show waiting state)
      navigate(`/game/${game_code}`);
    } catch (error) {
      console.error("Error creating game:", error);
      toast({
        title: "Error",
        description: "Failed to create game. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20 flex items-center justify-center p-4">
      <div className="w-full max-w-xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <header className="text-center space-y-3">
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            Create New Game
          </h1>
          <p className="text-muted-foreground text-lg">
            Choose your color and define your agent's strategy
          </p>
        </header>

        <Card className="p-6 space-y-6 border-2">
          {/* Color Selection */}
          <div className="space-y-3">
            <Label className="text-lg font-semibold">Choose Your Color</Label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setSelectedColor("white")}
                className={`p-4 rounded-lg border-2 transition-all duration-200 flex items-center gap-3 ${
                  selectedColor === "white"
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="w-12 h-12 rounded-lg bg-background border flex items-center justify-center">
                  <Crown className="w-6 h-6 text-foreground" />
                </div>
                <div className="text-left">
                  <p className="font-semibold">White</p>
                  <p className="text-sm text-muted-foreground">Move first</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setSelectedColor("black")}
                className={`p-4 rounded-lg border-2 transition-all duration-200 flex items-center gap-3 ${
                  selectedColor === "black"
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="w-12 h-12 rounded-lg bg-foreground flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-background" />
                </div>
                <div className="text-left">
                  <p className="font-semibold">Black</p>
                  <p className="text-sm text-muted-foreground">Respond second</p>
                </div>
              </button>
            </div>
          </div>

          {/* Prompt Input */}
          <div className="space-y-2">
            <Label htmlFor="prompt" className="text-lg font-semibold">
              Your Agent's Strategy
            </Label>
            <Textarea
              id="prompt"
              placeholder={selectedColor === "white"
                ? "e.g., Play aggressively, focus on early attacks..."
                : "e.g., Play defensively, focus on solid positioning..."
              }
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-[200px] resize-none text-base"
              disabled={isLoading}
            />
          </div>
        </Card>

        <div className="flex gap-4 justify-center">
          <Button
            variant="outline"
            size="lg"
            onClick={() => navigate("/")}
            disabled={isLoading}
            className="min-w-[140px]"
          >
            Cancel
          </Button>
          <Button
            size="lg"
            onClick={handleCreateGame}
            disabled={isLoading || !prompt.trim()}
            className="min-w-[200px] bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              "Create Game"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default GameSetup;
