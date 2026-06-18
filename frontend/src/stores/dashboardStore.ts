/**
 * Global dashboard state using Zustand.
 *
 * Zustand is simpler than Redux and perfectly suited for this use case.
 * The store holds:
 * - All honey tokens (fetched once, updated on WebSocket events)
 * - Recent trigger events (new ones prepended on WebSocket broadcast)
 * - Dashboard stats (computed from tokens + events)
 * - WebSocket connection state
 */

import { create } from "zustand";
import type {
  DashboardStats,
  HoneyToken,
  TriggerEvent,
  WebSocketMessage,
} from "@/types";

interface DashboardState {
  // Data
  tokens: HoneyToken[];
  events: TriggerEvent[];
  stats: DashboardStats;
  isConnected: boolean;

  // Loading states
  tokensLoading: boolean;
  eventsLoading: boolean;

  // Actions
  setTokens: (tokens: HoneyToken[]) => void;
  setEvents: (events: TriggerEvent[]) => void;
  setConnected: (connected: boolean) => void;
  setTokensLoading: (loading: boolean) => void;
  setEventsLoading: (loading: boolean) => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  removeToken: (id: string) => void;
}

function computeStats(
  tokens: HoneyToken[],
  events: TriggerEvent[],
  isConnected: boolean
): DashboardStats {
  return {
    totalTokens: tokens.length,
    activeTokens: tokens.filter((t) => t.status === "active").length,
    triggeredTokens: tokens.filter((t) => t.status === "triggered").length,
    totalEvents: events.length,
    criticalEvents: events.filter(
      (e) => e.severity === "critical" || e.severity === "high"
    ).length,
    connectedClients: isConnected ? 1 : 0,
  };
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  tokens: [],
  events: [],
  isConnected: false,
  tokensLoading: false,
  eventsLoading: false,
  stats: computeStats([], [], false),

  setTokens: (tokens) => {
    const { events, isConnected } = get();
    set({ tokens, stats: computeStats(tokens, events, isConnected) });
  },

  setEvents: (events) => {
    const { tokens, isConnected } = get();
    set({ events, stats: computeStats(tokens, events, isConnected) });
  },

  setConnected: (isConnected) => {
    const { tokens, events } = get();
    set({ isConnected, stats: computeStats(tokens, events, isConnected) });
  },

  setTokensLoading: (tokensLoading) => set({ tokensLoading }),
  setEventsLoading: (eventsLoading) => set({ eventsLoading }),

  removeToken: (id) => {
    const { tokens, events, isConnected } = get();
    const updated = tokens.filter((t) => t.id !== id);
    set({ tokens: updated, stats: computeStats(updated, events, isConnected) });
  },

  handleWebSocketMessage: (message) => {
    const { tokens, events, isConnected } = get();

    if (message.type === "token_triggered" && message.payload) {
      // Create a synthetic event entry for the feed
      // Full event data arrives via the REST endpoint
      // The WebSocket gives us enough to show an immediate alert
      const newEvent: TriggerEvent = {
        id: message.payload.event_id as string,
        token_id: message.payload.token_id as string,
        source_ip: message.payload.source_ip as string,
        user_agent: null,
        request_method: null,
        request_path: null,
        severity: message.payload.severity as TriggerEvent["severity"],
        agent_analysis: null,
        additional_context: null,
        created_at: message.payload.timestamp as string,
      };

      if (message.type === "agent_analysis_complete" && message.payload) {
      // Update the event in the feed with agent findings
      const updatedEvents = get().events.map((e) =>
        e.id === message.payload!.event_id
          ? {
              ...e,
              severity: message.payload!.severity as TriggerEvent["severity"],
              agent_analysis: message.payload!.summary as string,
            }
          : e
      );
      const { tokens, isConnected } = get();
      set({
        events: updatedEvents,
        stats: computeStats(tokens, updatedEvents, isConnected),
      });
    }

      // Prepend new event — newest first
      const updatedEvents = [newEvent, ...events].slice(0, 100);

      // Update the token status to triggered
      const updatedTokens = tokens.map((t) =>
        t.id === message.payload!.token_id
          ? { ...t, status: "triggered" as const }
          : t
      );

      set({
        events: updatedEvents,
        tokens: updatedTokens,
        stats: computeStats(updatedTokens, updatedEvents, isConnected),
      });
    }
  },
}));