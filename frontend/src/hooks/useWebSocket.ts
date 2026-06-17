/**
 * useWebSocket — custom React hook for the real-time event stream.
 *
 * Handles:
 * - Connection lifecycle (connect, disconnect, reconnect)
 * - Automatic reconnection with exponential backoff
 * - Message parsing and type-safe dispatch
 * - Connection state tracking
 *
 * Usage:
 *   const { isConnected, lastEvent } = useWebSocket();
 */

import { useEffect, useRef, useState, useCallback } from "react";
import type { WebSocketMessage } from "@/types";

interface UseWebSocketReturn {
  isConnected: boolean;
  lastEvent: WebSocketMessage | null;
  connectionCount: number;
  sendPing: () => void;
}

const WS_URL = "ws://localhost:8000/api/v1/ws";
const MAX_RECONNECT_DELAY = 30000; // 30 seconds max
const INITIAL_RECONNECT_DELAY = 1000; // Start at 1 second

export function useWebSocket(
  onMessage?: (event: WebSocketMessage) => void
): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WebSocketMessage | null>(null);
  const [connectionCount, setConnectionCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  const connect = useCallback(() => {
    // Don't connect if component unmounted
    if (!isMounted.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMounted.current) return;
        setIsConnected(true);
        // Reset backoff on successful connection
        reconnectDelay.current = INITIAL_RECONNECT_DELAY;
        console.info("[ShadowWall] WebSocket connected");
      };

      ws.onmessage = (event) => {
        if (!isMounted.current) return;
        try {
          const parsed: WebSocketMessage = JSON.parse(event.data);
          setLastEvent(parsed);

          // Update connection count from server messages
          if (parsed.active_connections !== undefined) {
            setConnectionCount(parsed.active_connections);
          }
          if (parsed.connections !== undefined) {
            setConnectionCount(parsed.connections);
          }

          // Call external handler if provided
          onMessage?.(parsed);
        } catch {
          console.error("[ShadowWall] Failed to parse WebSocket message");
        }
      };

      ws.onclose = () => {
        if (!isMounted.current) return;
        setIsConnected(false);
        wsRef.current = null;

        // Exponential backoff reconnection
        console.info(
          `[ShadowWall] WebSocket disconnected. Reconnecting in ${reconnectDelay.current}ms`
        );
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay.current = Math.min(
            reconnectDelay.current * 2,
            MAX_RECONNECT_DELAY
          );
          connect();
        }, reconnectDelay.current);
      };

      ws.onerror = () => {
        // onclose fires after onerror, so reconnect logic lives there
        console.error("[ShadowWall] WebSocket error");
      };
    } catch (error) {
      console.error("[ShadowWall] WebSocket connection failed:", error);
    }
  }, [onMessage]);

  useEffect(() => {
    isMounted.current = true;
    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send("ping");
    }
  }, []);

  return { isConnected, lastEvent, connectionCount, sendPing };
}