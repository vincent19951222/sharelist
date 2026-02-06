'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { getLocalUser, updateLocalUserName } from '@/lib/store';
import { createRoomApi } from '@/lib/api';
import { RecentRoom } from '@/types';
import { Plus, Loader2, Clock, Shield, ChevronRight, History } from 'lucide-react';

function formatTimeAgo(timestamp: number) {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function Home() {
  const router = useRouter();
  const [nickname, setNickname] = useState('');
  const [roomIdInput, setRoomIdInput] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [recentRooms, setRecentRooms] = useState<RecentRoom[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const user = getLocalUser();
    if (user.name) setNickname(user.name);
    setRecentRooms(user.recentRooms || []);
    setMounted(true);
  }, []);

  const handleCreateRoom = async () => {
    if (!nickname.trim()) {
      alert('Please enter a nickname');
      return;
    }
    updateLocalUserName(nickname);
    setIsCreating(true);

    try {
      const room = await createRoomApi(nickname + "'s Room");
      // Redirect with Admin Token
      router.push(`/room/${room.roomId}?token=${room.adminToken}`);
    } catch (err) {
      alert('Failed to create room. Please try again.');
      console.error(err);
      setIsCreating(false);
    }
  };

  const handleJoinRoom = () => {
    if (!nickname.trim()) {
      alert('Please enter a nickname');
      return;
    }
    
    // Smart Join: Handle full URL paste
    let targetId = roomIdInput.trim();
    let tokenParam = '';

    if (targetId.includes('http')) {
       try {
         const url = new URL(targetId);
         // Extract Room ID from path (assuming /room/ID)
         const pathParts = url.pathname.split('/');
         const idFromPath = pathParts[pathParts.length - 1]; // very basic check
         if (idFromPath) targetId = idFromPath;
         
         const token = url.searchParams.get('token');
         if (token) tokenParam = `?token=${token}`;
       } catch (e) {
         // ignore
       }
    }

    if (!targetId) {
      alert('Please enter a Room ID');
      return;
    }

    updateLocalUserName(nickname);
    router.push(`/room/${targetId}${tokenParam}`);
  };

  const handleRecentClick = (room: RecentRoom) => {
      if (!nickname.trim()) return;
      updateLocalUserName(nickname);
      const tokenParam = room.token ? `?token=${room.token}` : '';
      router.push(`/room/${room.roomId}${tokenParam}`);
  }

  if (!mounted) return null;

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-muted/30">
      <Card className="w-full max-w-md shadow-lg border-none sm:border bg-background">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-3xl font-bold tracking-tight text-primary">Room Todo</CardTitle>
          <CardDescription>Collaborate on checklists together</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">
              Your Nickname
            </label>
            <Input
              placeholder="Enter your name"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
            />
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">Start a new list</h3>
              <Button className="w-full" size="lg" onClick={handleCreateRoom} disabled={isCreating}>
                {isCreating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                {isCreating ? 'Creating...' : 'Create New Room'}
              </Button>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Join with invite</span>
              </div>
            </div>

            <div className="flex space-x-2">
              <Input
                placeholder="Invite Code or Link"
                value={roomIdInput}
                onChange={(e) => setRoomIdInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleJoinRoom();
                }}
              />
              <Button variant="secondary" onClick={handleJoinRoom}>
                Join
              </Button>
            </div>
          </div>

          {/* Recent Rooms Section */}
          {recentRooms.length > 0 && (
            <>
                <Separator />
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                        <History className="w-4 h-4" />
                        <h3>Recent Rooms</h3>
                    </div>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                        {recentRooms.map((room) => (
                            <button
                                key={room.roomId}
                                onClick={() => handleRecentClick(room)}
                                className="w-full flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors text-left group"
                            >
                                <div className="flex flex-col gap-1 min-w-0">
                                    <div className="font-medium truncate flex items-center gap-2">
                                        {room.roomName}
                                        {room.role === 'admin' && (
                                            <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 border-primary text-primary">
                                                Admin
                                            </Badge>
                                        )}
                                    </div>
                                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {formatTimeAgo(room.lastVisited)}
                                    </div>
                                </div>
                                <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                            </button>
                        ))}
                    </div>
                </div>
            </>
          )}

        </CardContent>
        <CardFooter className="justify-center text-xs text-muted-foreground">
          Simple, fast, secure.
        </CardFooter>
      </Card>
    </div>
  );
}
