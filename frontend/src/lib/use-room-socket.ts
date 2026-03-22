"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { nanoid } from "nanoid";

import { getRoomSnapshot } from "@/lib/api";
import { LocalUser, RoomSnapshot } from "@/types";

type ConnectionState = "connecting" | "connected" | "reconnecting" | "offline";

interface UseRoomSocketResult {
  snapshot: RoomSnapshot | null;
  connectionState: ConnectionState;
  fatalError: string | null;
  serverMessage: string | null;
  clearServerMessage: () => void;
  sendEvent: (type: string, payload: Record<string, unknown>) => boolean;
}

function getWebSocketBase(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.hostname}:8000`;
  }

  return "ws://localhost:8000";
}

interface PendingEvent {
  type: string;
  payload: Record<string, unknown>;
}

export function useRoomSocket(roomId: string, user: LocalUser | null): UseRoomSocketResult {
  const [snapshot, setSnapshot] = useState<RoomSnapshot | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  const [fatalError, setFatalError] = useState<string | null>(null);
  const [serverMessage, setServerMessage] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReconnectRef = useRef(true);
  const snapshotRef = useRef<RoomSnapshot | null>(null);
  const pendingEventsRef = useRef<PendingEvent[]>([]);
  const connectionTokenRef = useRef(0);

  useEffect(() => {
    snapshotRef.current = snapshot;
  }, [snapshot]);

  useEffect(() => {
    if (!user) {
      setSnapshot(null);
      setFatalError(null);
      setServerMessage(null);
      pendingEventsRef.current = [];
      return;
    }

    const bootstrapUser = user;
    const controller = new AbortController();

    async function bootstrapSnapshot() {
      try {
        const nextSnapshot = await getRoomSnapshot(roomId, bootstrapUser.name, controller.signal);
        if (!controller.signal.aborted) {
          setSnapshot(nextSnapshot);
          setFatalError(null);
          setServerMessage(null);
        }
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        const message = error instanceof Error ? error.message : "Failed to load room snapshot.";
        if (message === "Only approved members can enter this room.") {
          setFatalError("当前用户不在这个房间的允许名单中。");
          return;
        }

        if (message === "Room not found.") {
          setFatalError("房间不存在，或者已经被移除。");
          return;
        }

        setServerMessage(message);
      }
    }

    void bootstrapSnapshot();

    return () => controller.abort();
  }, [roomId, user]);

  const clearReconnect = () => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  };

  const connect = useCallback(() => {
    if (!user) {
      setConnectionState("offline");
      return;
    }

    clearReconnect();
    setConnectionState((current) => (current === "connected" ? current : "connecting"));

    const connectionToken = ++connectionTokenRef.current;
    const nextSocket = new WebSocket(
      `${getWebSocketBase()}/ws/${encodeURIComponent(roomId)}/${encodeURIComponent(user.name)}`
    );
    socketRef.current = nextSocket;

    nextSocket.onopen = () => {
      if (connectionTokenRef.current !== connectionToken || socketRef.current !== nextSocket) {
        return;
      }

      setConnectionState("connected");
      setFatalError(null);
      setServerMessage(null);

      for (const event of pendingEventsRef.current) {
        nextSocket.send(JSON.stringify(event));
      }
      pendingEventsRef.current = [];
    };

    nextSocket.onmessage = (event) => {
      if (connectionTokenRef.current !== connectionToken || socketRef.current !== nextSocket) {
        return;
      }

      try {
        const message = JSON.parse(event.data);
        if (message.type === "snapshot") {
          setSnapshot(message.payload as RoomSnapshot);
          setServerMessage(null);
          return;
        }

        if (message.type === "error" && message.payload?.message) {
          setServerMessage(message.payload.message as string);
          return;
        }

        if (message.type === "ping" && nextSocket.readyState === WebSocket.OPEN) {
          nextSocket.send(JSON.stringify({ type: "pong", payload: {} }));
        }
      } catch {
        setServerMessage("Received an invalid update from the server.");
      }
    };

    nextSocket.onclose = (event) => {
      if (connectionTokenRef.current !== connectionToken || socketRef.current !== nextSocket) {
        return;
      }

      socketRef.current = null;

      if (!shouldReconnectRef.current) {
        return;
      }

      if (event.code === 4001) {
        setConnectionState("offline");
        setFatalError("当前用户不在这个房间的允许名单中。");
        return;
      }

      if (event.code === 4004) {
        setConnectionState("offline");
        setFatalError("房间不存在，或者已经被移除。");
        return;
      }

      setServerMessage(
        snapshotRef.current
          ? "Realtime sync disconnected. Retrying WebSocket."
          : "Realtime sync unavailable. Loaded snapshot via HTTP, retrying WebSocket."
      );
      setConnectionState("reconnecting");
      reconnectTimerRef.current = setTimeout(connect, 2000);
    };
  }, [roomId, user]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();
    return () => {
      shouldReconnectRef.current = false;
      clearReconnect();
      connectionTokenRef.current += 1;
      const currentSocket = socketRef.current;
      socketRef.current = null;
      if (currentSocket) {
        currentSocket.close();
      }
    };
  }, [connect]);

  const sendEvent = useCallback(
    (type: string, payload: Record<string, unknown>) => {
      const socket = socketRef.current;
      const eventPayload = {
        type,
        payload: {
          ...payload,
          clientEventId: nanoid(),
        },
      };

      if (!socket) {
        return false;
      }

      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(eventPayload));
        return true;
      }

      if (socket.readyState === WebSocket.CONNECTING) {
        pendingEventsRef.current.push(eventPayload);
        return true;
      }

      return false;
    },
    []
  );

  return {
    snapshot,
    connectionState,
    fatalError,
    serverMessage,
    clearServerMessage: () => setServerMessage(null),
    sendEvent,
  };
}
