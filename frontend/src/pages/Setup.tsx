import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Loader2, Crown, Sparkles } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/config/api";

const GameSetup = () => {
  const [whitePrompt, setWhitePrompt] = useState("");
  const [blackPrompt, setBlackPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleStartGame = async () => {
    if (!whitePrompt.trim() || !blackPrompt.trim()) {
      toast({
        title: "Missing Prompts",
        description: "Please provide prompts for both agents",
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

      // Submit white prompt
      const whiteResponse = await fetch(
        `${API_BASE_URL}/games/${game_code}/prompt`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            color: "white",
            prompt: whitePrompt,
          }),
        }
      );

      if (!whiteResponse.ok) throw new Error("Failed to submit white prompt");

      // Submit black prompt
      const blackResponse = await fetch(
        `${API_BASE_URL}/games/${game_code}/prompt`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            color: "black",
            prompt: blackPrompt,
          }),
        }
      );

      if (!blackResponse.ok) throw new Error("Failed to submit black prompt");

      // Navigate to game viewer
      navigate(`/game/${game_code}`);
    } catch (error) {
      console.error("Error starting game:", error);
      toast({
        title: "Error",
        description: "Failed to start game. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <header className="text-center space-y-3">
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            Configure AI Agents
          </h1>
          <p className="text-muted-foreground text-lg">
            Define the strategic personalities of your chess agents
          </p>
        </header>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-6 space-y-4 border-2 hover:border-primary/50 transition-all duration-300">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-background flex items-center justify-center">
                <Crown className="w-6 h-6 text-foreground" />
              </div>
              <div>
                <Label htmlFor="white-prompt" className="text-lg font-semibold">
                  White Agent
                </Label>
                <p className="text-sm text-muted-foreground">First to move</p>
              </div>
            </div>
            <Textarea
              id="white-prompt"
              placeholder="e.g., Play aggressively, focus on early attacks..."
              value={whitePrompt}
              onChange={(e) => setWhitePrompt(e.target.value)}
              className="min-h-[200px] resize-none text-base"
            />
          </Card>

          <Card className="p-6 space-y-4 border-2 hover:border-primary/50 transition-all duration-300">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-foreground flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-background" />
              </div>
              <div>
                <Label htmlFor="black-prompt" className="text-lg font-semibold">
                  Black Agent
                </Label>
                <p className="text-sm text-muted-foreground">Responds second</p>
              </div>
            </div>
            <Textarea
              id="black-prompt"
              placeholder="e.g., Play defensively, focus on solid positioning..."
              value={blackPrompt}
              onChange={(e) => setBlackPrompt(e.target.value)}
              className="min-h-[200px] resize-none text-base"
            />
          </Card>
        </div>

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
            onClick={handleStartGame}
            disabled={isLoading}
            className="min-w-[200px] bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Starting...
              </>
            ) : (
              "Start Game"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default GameSetup;
