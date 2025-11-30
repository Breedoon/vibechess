import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Brain, Zap, Eye } from "lucide-react";
import heroImage from "@/assets/chess-hero.jpg";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20 relative overflow-hidden">
      {/* Background image */}
      <div 
        className="absolute inset-0 opacity-5 bg-cover bg-center"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      
      {/* Decorative elements */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(160,200,180,0.1),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(42,180,150,0.08),transparent_50%)]" />
      
      <div className="relative flex flex-col items-center justify-center min-h-screen px-4 py-16">
        <div className="max-w-4xl text-center space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-1000">
          {/* Logo/Icon */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
              <div className="relative w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center transform rotate-6 hover:rotate-12 transition-transform duration-500">
                <Brain className="w-10 h-10 text-primary-foreground" />
              </div>
            </div>
          </div>

          {/* Hero text */}
          <div className="space-y-4">
            <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-tight">
              Watch AI Agents
              <br />
              <span className="bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
                Battle on Chess
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Experience strategic gameplay as AI agents compete in real-time,
              revealing their reasoning and decision-making process
            </p>
          </div>

          {/* CTA Button */}
          <div className="pt-8">
            <Button
              size="lg"
              onClick={() => navigate("/setup")}
              className="text-lg px-8 py-6 h-auto rounded-xl bg-gradient-to-r from-primary to-accent hover:opacity-90 hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-xl"
            >
              <Zap className="w-5 h-5 mr-2" />
              Start New Game
            </Button>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 pt-16 max-w-3xl mx-auto">
            {[
              {
                icon: Brain,
                title: "AI Reasoning",
                description: "See how agents think and strategize each move",
              },
              {
                icon: Eye,
                title: "Live Updates",
                description: "Watch games unfold in real-time with SSE",
              },
              {
                icon: Zap,
                title: "Custom Agents",
                description: "Define unique playing styles and strategies",
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="space-y-3 p-6 rounded-xl bg-card/50 backdrop-blur border border-border/50 hover:border-primary/50 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4"
                style={{ animationDelay: `${(index + 1) * 200}ms` }}
              >
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mx-auto">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
