'use client';

import { useState, useEffect, use, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { RoomGate } from '@/components/RoomGate';
import { RoomError } from '@/components/RoomError';
import PriorityBadge from '@/components/PriorityBadge';
import PrioritySelector from '@/components/PrioritySelector';
import FilterBar from '@/components/FilterBar';
import { 
  getRoom, 
  saveRoom, 
  getLocalUser, 
  addRecentRoom,
} from '@/lib/store';
import { Room, TodoItem, Priority } from '@/types';
import { rotateInviteToken } from '@/lib/api';
import { 
  Trash2, 
  Share2, 
  Copy, 
  ArrowLeft,
  Edit2,
  Wifi,
  WifiOff,
  Shield,
  RefreshCw,
  CheckCheck,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { nanoid } from 'nanoid';

// Extended Room Interface for Frontend
interface RoomWithTokens extends Room {
  joinToken?: string;
  adminToken?: string; // Only if admin
}

interface ErrorState {
    title: string;
    message: string;
}

interface BannerMessage {
  type: 'info' | 'error' | 'success';
  text: string;
}

export default function RoomPage({ params }: { params: Promise<{ roomId: string }> }) {
  const { roomId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();

  // State
  const [room, setRoom] = useState<RoomWithTokens | null>(null);
  const [items, setItems] = useState<TodoItem[]>([]);
  const [newItemText, setNewItemText] = useState('');
  const [newItemPriority, setNewItemPriority] = useState<Priority>('medium');
  const [currentUser, setCurrentUser] = useState('');
  const [hideCompleted, setHideCompleted] = useState(false);
  const [priorityFilter, setPriorityFilter] = useState<'all' | Priority>('all');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [editPriority, setEditPriority] = useState<Priority>('medium');
  const [isConnected, setIsConnected] = useState(false);
  const [myRole, setMyRole] = useState<'admin' | 'member' | 'guest'>('guest');
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [errorState, setErrorState] = useState<ErrorState | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [gateMessage, setGateMessage] = useState<string | null>(null);
  const [bannerMessage, setBannerMessage] = useState<BannerMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);

  // 1. Initial Auth Check (URL -> State)
  useEffect(() => {
    const urlToken = searchParams.get('token');
    if (urlToken) {
      setAuthToken(urlToken);
    }
  }, [searchParams]);

  // 2. User & Room Setup
  useEffect(() => {
    const user = getLocalUser();
    if (!user.name) {
      router.push(`/?returnTo=${roomId}`);
      return;
    }
    setCurrentUser(user.name);
  }, [roomId, router]);

  // Save to Recent Rooms when room data is loaded
  useEffect(() => {
    if (room && myRole) {
        addRecentRoom(room.roomId, room.roomName, authToken || undefined, myRole);
    }
  }, [room, myRole, authToken]);

  // 3. WebSocket Connection
  const connectWebSocket = useCallback((token: string) => {
    if (!currentUser) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const wsUrl = `${baseUrl}/ws/${roomId}/${currentUser}?token=${token}`;
    
    console.log('Connecting...');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
      setIsReconnecting(false);
      setErrorState(null); // Clear errors on success
      setBannerMessage(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'snapshot') {
            const serverRoom = data.payload as RoomWithTokens;
            setRoom(serverRoom);
            setItems(serverRoom.items);
            if (data.role) setMyRole(data.role);
        } else if (data.type === 'token_rotated') {
            setRoom((prev) => prev ? { ...prev, joinToken: data.payload?.newJoinToken } : prev);
            setBannerMessage({ type: 'info', text: 'Invite updated. Old links no longer work.' });
        } else if (data.type === 'error') {
            setBannerMessage({ type: 'error', text: data.payload.message });
        } else if (data.type === 'ping') {
             if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'pong', payload: {} }));
             }
        }
      } catch (e) {
        console.error(e);
      }
    };

    ws.onclose = (event) => {
      console.log('WS Close', event.code, event.reason);
      setIsConnected(false);
      
      // Handle Specific Close Codes
      if (event.code === 4004) {
          // Room Not Found
          setAuthToken(null);
          setIsReconnecting(false);
          setErrorState({
              title: "Room Not Found",
              message: "This room does not exist or has expired. Please create a new one."
          });
          return;
      }
      
      if (event.code === 4001) {
          // Unauthorized
          setAuthToken(null);
          setIsReconnecting(false);
          setGateMessage("Invite code is invalid or expired. Please request a new invite.");
          return;
      }

      if (event.code === 4003) {
          // Room Full
           setIsReconnecting(false);
           setErrorState({
              title: "Room is Full",
              message: "This room has reached its maximum user capacity."
          });
          return;
      }
      
      // For network errors / server restart (1006), retry indefinitely
      setIsReconnecting(true);
      setTimeout(() => connectWebSocket(token), 3000);
    };
  }, [currentUser, roomId]);

  // Trigger connection when we have a token
  useEffect(() => {
    if (authToken && currentUser && !isConnected) {
      connectWebSocket(authToken);
    }
  }, [authToken, currentUser, isConnected, connectWebSocket]);

  // --- Actions ---

  const sendEvent = (type: string, payload: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ 
        type, 
        payload: { ...payload, clientEventId: nanoid() } 
      }));
    }
  };

  const handleAddItem = () => {
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to add items.' });
      return;
    }
    if (!newItemText.trim()) return;
    sendEvent('item_add', {
      text: newItemText.trim(),
      priority: newItemPriority
    });
    setNewItemText('');
    setNewItemPriority('medium'); // Reset to default
    setBannerMessage({ type: 'success', text: 'Item added.' });
  };

  const handleToggle = (itemId: string, currentDone: boolean) => {
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to update items.' });
      return;
    }
    sendEvent('item_toggle', { itemId, done: !currentDone });
  };
  const handleDelete = (itemId: string) => {
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to delete items.' });
      return;
    }
    if (confirm('Delete?')) {
      sendEvent('item_delete', { itemId });
      setBannerMessage({ type: 'success', text: 'Item deleted.' });
    }
  };
  
  const startEditing = (item: TodoItem) => {
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to edit items.' });
      return;
    }
    setEditingId(item.id);
    setEditText(item.text);
    setEditPriority(item.priority || 'medium');  // Default to medium if not set
  };

  const saveEdit = () => {
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to edit items.' });
      return;
    }
    if (editingId && editText.trim()) {
      sendEvent('item_edit', {
        itemId: editingId,
        text: editText.trim(),
        priority: editPriority
      });
    }
    setEditingId(null);
  };

  const handleClearDone = () => {
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to clear items.' });
      return;
    }
    if (confirm('Clear all completed items?')) {
        sendEvent('room_clear_done', {});
        setBannerMessage({ type: 'success', text: 'Completed items cleared.' });
    }
  }

  const handleRename = () => {
      if (!isConnected) {
        setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to rename the room.' });
        return;
      }
      const newName = prompt("Enter new room name:", room?.roomName);
      if (newName) {
          sendEvent('room_rename', { roomName: newName });
      }
  }

  const handleRotateInvite = async () => {
    if (!room?.roomId || !authToken) return;
    if (!isConnected) {
      setBannerMessage({ type: 'error', text: 'You are offline. Reconnect to rotate invite.' });
      return;
    }
    if (!confirm('Reset invite? Old links will stop working.')) return;
    try {
      const res = await rotateInviteToken(room.roomId, authToken);
      setRoom((prev) => prev ? { ...prev, joinToken: res.newJoinToken } : prev);
      setBannerMessage({ type: 'success', text: 'Invite reset. Share the new link.' });
    } catch (e) {
      setBannerMessage({ type: 'error', text: 'Failed to reset invite. Try again.' });
    }
  };

  const copyLink = async () => {
    if (!room?.joinToken) return;
    const url = new URL(window.location.href);
    url.searchParams.set('token', room.joinToken);
    const shareUrl = url.toString();
    const shareData = { title: room.roomName, text: `Join my list! Code: ${roomId}. Rooms expire after 24h of inactivity.`, url: shareUrl };

    if (navigator.share) {
      try { await navigator.share(shareData); return; } catch (e) {}
    }
    navigator.clipboard.writeText(shareUrl);
    setBannerMessage({ type: 'success', text: 'Invite link copied.' });
  };

  const handleCopyList = async () => {
      if (!room) return;
      const lines = [`${room.roomName}`];
      items.forEach(item => {
          const mark = item.done ? '☑' : '☐';
          const suffix = item.done && item.doneBy ? ` (Done by ${item.doneBy})` : '';
          lines.push(`${mark} ${item.text}${suffix}`);
      });
      const text = lines.join('\n');
      
      try {
          await navigator.clipboard.writeText(text);
          setBannerMessage({ type: 'success', text: 'List copied to clipboard.' });
      } catch (err) {
          console.error('Failed to copy', err);
      }
  }

  const handleCopyInviteCode = async () => {
    if (!room?.joinToken) return;
    try {
      await navigator.clipboard.writeText(room.joinToken);
      setBannerMessage({ type: 'success', text: 'Invite code copied.' });
    } catch (err) {
      setBannerMessage({ type: 'error', text: 'Failed to copy invite code.' });
    }
  };

  // --- Render ---

  // 1. Error State (Blocking)
  if (errorState) {
      return <RoomError title={errorState.title} message={errorState.message} />;
  }

  // 2. Gate State (No Token)
  if (!authToken) {
      return <RoomGate roomId={roomId} message={gateMessage || undefined} onJoin={(t) => { setGateMessage(null); setAuthToken(t); }} />;
  }

  // 3. Loading State (Token present, but no data yet)
  if (!room) {
      return (
        <div className="flex flex-col h-screen items-center justify-center space-y-4 bg-muted/30">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="text-muted-foreground animate-pulse">Entering Room...</p>
        </div>
      );
  }

  const displayRoomName = room?.roomName || 'Loading...';
  const displayedItems = items.filter(item => {
    if (hideCompleted && item.done) return false;
    if (priorityFilter !== 'all' && (item.priority || 'medium') !== priorityFilter) return false;
    return true;
  });
  const completedCount = items.filter(i => i.done).length;
  const connectionStatus = isConnected ? 'Connected' : (isReconnecting ? 'Reconnecting' : 'Offline');
  const canEdit = isConnected;

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto bg-background shadow-xl sm:border-x relative">
      
      {/* Reconnecting Banner */}
      {!isConnected && (
        <Alert variant="destructive" className="rounded-none border-x-0 border-t-0 py-2">
            <WifiOff className="h-4 w-4" />
            <AlertTitle className="ml-2 text-xs font-semibold">Connection Lost</AlertTitle>
            <AlertDescription className="ml-2 text-xs">
                Reconnecting to server...
            </AlertDescription>
        </Alert>
      )}

      {bannerMessage && (
        <Alert variant={bannerMessage.type === 'error' ? 'destructive' : 'default'} className="rounded-none border-x-0 border-t-0 py-2">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle className="ml-2 text-xs font-semibold">Notice</AlertTitle>
            <AlertDescription className="ml-2 text-xs">
                {bannerMessage.text}
            </AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <div className="p-4 border-b bg-card z-10 sticky top-0">
        <div className="flex items-center justify-between mb-2">
          <Button variant="ghost" size="icon" onClick={() => router.push('/')}>
             <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="text-center">
            <h1 
                className={`font-bold text-lg flex items-center justify-center gap-2 ${myRole === 'admin' ? 'cursor-pointer hover:underline' : ''}`}
                onDoubleClick={myRole === 'admin' ? handleRename : undefined}
            >
              {displayRoomName}
            </h1>
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <span>ID: {roomId}</span>
                {myRole === 'admin' && (
                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 border-primary text-primary flex gap-1">
                        <Shield className="w-3 h-3" /> Admin
                    </Badge>
                )}
                {myRole === 'member' && (
                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 border-muted-foreground text-muted-foreground flex gap-1">
                        Member
                    </Badge>
                )}
            </div>
            <div className="text-[10px] text-muted-foreground mt-1">
              Rooms expire after 24h of inactivity.
            </div>
          </div>
          <div className="flex gap-1">
            <Button variant="ghost" size="icon" onClick={handleCopyList} title="Copy List as Text">
                <Copy className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={myRole === 'admin' ? handleRotateInvite : undefined}
              disabled={myRole !== 'admin'}
              title={myRole === 'admin' ? "Reset Invite" : "Admin only"}
            >
              <RefreshCw className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={copyLink} title="Share Link">
                <Share2 className="h-5 w-5" />
            </Button>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-sm mt-2">
          <div className="text-muted-foreground">
            {completedCount}/{items.length} Done
          </div>
          <div className="flex items-center gap-2">
            {completedCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs text-destructive"
                onClick={myRole === 'admin' ? handleClearDone : undefined}
                disabled={!canEdit || myRole !== 'admin'}
                title={myRole === 'admin' ? "Clear completed items" : "Admin only"}
              >
                <CheckCheck className="w-3 h-3 mr-1" /> Clear Done
              </Button>
            )}
            <label className="text-xs flex items-center gap-1 cursor-pointer select-none">
              <Checkbox checked={hideCompleted} onCheckedChange={(c) => setHideCompleted(!!c)} />
              Hide Done
            </label>
          </div>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
          <div className="flex items-center gap-1">
            {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            <span>{connectionStatus}</span>
          </div>
          {room?.joinToken && (
            <div className="flex items-center gap-2">
              <span className="truncate max-w-[120px]">Invite: {room.joinToken}</span>
              <button className="text-xs underline" onClick={handleCopyInviteCode}>
                Copy
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar currentFilter={priorityFilter} onFilterChange={setPriorityFilter} />

      {/* List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 pb-20">
        {displayedItems.length === 0 && (
            <div className="text-center text-muted-foreground py-10 opacity-50">
                {items.length === 0 ? "No items yet." : "All items hidden."}
            </div>
        )}
        
        {displayedItems.map(item => (
          <div key={item.id} className={`group flex items-start gap-3 p-3 rounded-lg border transition-all ${item.done ? 'bg-muted/50 border-transparent' : 'bg-card border-border shadow-sm'}`}>
            <div className="pt-1">
               <Checkbox checked={item.done} onCheckedChange={() => handleToggle(item.id, item.done)} disabled={!canEdit} />
            </div>
            <div className="flex-1 min-w-0">
              {editingId === item.id ? (
                <div className="space-y-2">
                  <Input value={editText} onChange={(e) => setEditText(e.target.value)} autoFocus onKeyDown={(e) => { if (e.key === 'Enter') saveEdit(); }} className="h-8" disabled={!canEdit} />
                  <PrioritySelector value={editPriority} onChange={setEditPriority} />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={saveEdit} disabled={!canEdit}>Save</Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                  </div>
                </div>
              ) : (
                <div className="break-words">
                  <div className="flex items-center gap-2 mb-1">
                    <PriorityBadge priority={item.priority || 'medium'} size="sm" />
                    <span className={`block text-sm leading-relaxed ${item.done ? 'line-through text-muted-foreground' : ''}`} onDoubleClick={() => startEditing(item)}>
                      {item.text}
                    </span>
                  </div>
                  {item.done && item.doneBy && (
                    <span className="text-xs text-muted-foreground mt-1 block">Done by {item.doneBy}</span>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
               {!editingId && !item.done && (
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary" onClick={() => startEditing(item)} disabled={!canEdit}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
               )}
               <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => handleDelete(item.id)} disabled={!canEdit}>
                 <Trash2 className="h-4 w-4" />
               </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-background sticky bottom-0 z-10">
        <div className="max-w-2xl mx-auto space-y-3">
          <PrioritySelector value={newItemPriority} onChange={setNewItemPriority} />
          <div className="flex gap-2">
            <Input
              placeholder="Add a new item..."
              value={newItemText}
              onChange={(e) => setNewItemText(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleAddItem(); }}
              className="flex-1"
              disabled={!canEdit}
            />
            <Button onClick={handleAddItem} disabled={!canEdit}>Add</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
