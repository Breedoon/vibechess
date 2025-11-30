import { useState, useEffect } from 'react';
import { API_BASE_URL } from '@/config/api';

export interface ChatMessage {
  id: string;
  player: 'white' | 'black';
  message: string;
  timestamp: Date;
  type: 'thinking' | 'action' | 'game_over';
  moveSan?: string;
  fen?: string;
}

export interface GameState {
  fen?: string;
  pgn?: string;
  status?: string;
  winner?: string;
  move_count?: number;
}

export function useGameEvents(gameCode: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch initial game state on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/games/${gameCode}`)
      .then(res => res.json())
      .then(data => setGameState({
        fen: data.board_fen,
        status: data.status,
        winner: data.result,
        move_count: data.moves?.length || 0,
      }))
      .catch(console.error);
  }, [gameCode]);

  useEffect(() => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/games/${gameCode}/events`
    );

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('SSE connected');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Build message based on event type
        let messageText = '';
        if (data.type === 'thinking') {
          messageText = data.comment || 'Thinking...';
        } else if (data.type === 'move') {
          messageText = data.comment ? `${data.move_san}: ${data.comment}` : data.move_san;
        } else if (data.type === 'game_over') {
          messageText = `Game Over: ${data.result}${data.reason ? ` (${data.reason})` : ''}`;
        }

        const newMessage: ChatMessage = {
          id: `${Date.now()}-${Math.random()}`,
          player: data.color,
          message: messageText,
          timestamp: new Date(),
          type: data.type === 'move' ? 'action' :
                data.type === 'game_over' ? 'game_over' : 'thinking',
          moveSan: data.move_san,
          fen: data.fen,
        };

        setMessages(prev => [...prev, newMessage]);

        // Fetch updated game state after move or game over
        if (data.type === 'move' || data.type === 'game_over') {
          fetch(`${API_BASE_URL}/games/${gameCode}`)
            .then(res => res.json())
            .then(apiData => setGameState({
              fen: apiData.board_fen,
              status: apiData.status,
              winner: apiData.result,
              move_count: apiData.moves?.length || 0,
            }))
            .catch(console.error);
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [gameCode]);

  return { messages, gameState, isConnected };
}
