'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Lock } from 'lucide-react';

interface RoomGateProps {
  roomId: string;
  onJoin: (token: string) => void;
  message?: string;
}

export function RoomGate({ roomId, onJoin, message }: RoomGateProps) {
  const [inputVal, setInputVal] = useState('');

  const handleJoin = () => {
    if (!inputVal.trim()) return;

    // Smart logic: If user pastes a full URL, extract the token
    let token = inputVal.trim();
    if (token.includes('token=')) {
      try {
        const urlObj = new URL(token);
        const extracted = urlObj.searchParams.get('token');
        if (extracted) token = extracted;
      } catch (e) {
        // Not a valid URL, maybe just a partial string containing token=
        const match = token.match(/token=([^&]+)/);
        if (match) token = match[1];
      }
    }

    onJoin(token);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-muted/30">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <div className="mx-auto bg-primary/10 p-3 rounded-full w-fit mb-2">
            <Lock className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-xl">Private Room</CardTitle>
          <CardDescription>
            This room is private. Enter an invite code or paste the full link to join <strong>{roomId}</strong>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {message && (
            <div className="text-sm text-destructive">{message}</div>
          )}
          <Input 
            placeholder="Paste Invite Code or Link..." 
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
          />
          <Button className="w-full" onClick={handleJoin}>
            Join Room
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
