import { useEffect, useCallback } from "react";
import { Shield, Radio } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useDashboardStore } from "@/stores/dashboardStore";
import { tokenApi, eventApi } from "@/services/api";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { EventFeed } from "@/components/dashboard/EventFeed";
import { TokenTable } from "@/components/dashboard/TokenTable";
import { SeverityChart } from "@/components/dashboard/SeverityChart";
import { ConnectionStatus } from "@/components/ui/ConnectionStatus";
import type { WebSocketMessage } from "@/types";

export function Dashboard() {
  const {
    tokens,
    events,
    stats,
    isConnected,
    setTokens,
    setEvents,
    setConnected,
    setTokensLoading,
    setEventsLoading,
    handleWebSocketMessage,
  } = useDashboardStore();

  // Handle incoming WebSocket messages
  const onMessage = useCallback(
    (message: WebSocketMessage) => {
      handleWebSocketMessage(message);
    },
    [handleWebSocketMessage]
  );

  const { isConnected: wsConnected } = useWebSocket(onMessage);

  // Sync WS connection state to store
  useEffect(() => {
    setConnected(wsConnected);
  }, [wsConnected, setConnected]);

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      setTokensLoading(true);
      setEventsLoading(true);
      try {
        const [tokensData, eventsData] = await Promise.all([
          tokenApi.list(),
          eventApi.recent(100),
        ]);
        setTokens(tokensData.items);
        setEvents(eventsData);
      } catch (e) {
        console.error("Failed to load dashboard data:", e);
      } finally {
        setTokensLoading(false);
        setEventsLoading(false);
      }
    };
    loadData();
  }, [setTokens, setEvents, setTokensLoading, setEventsLoading]);

  return (
    <div className="min-h-screen bg-cyber-bg">
      {/* Header */}
      <header className="border-b border-cyber-border bg-cyber-surface/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield size={20} className="text-cyber-accent" />
            <span className="text-cyber-accent font-semibold tracking-widest uppercase text-sm">
              ShadowWall AI
            </span>
            <span className="text-cyber-muted text-xs hidden sm:block">
              Cyber Deception Platform
            </span>
          </div>
          <div className="flex items-center gap-4">
            {isConnected && (
              <div className="flex items-center gap-1.5 text-xs text-cyber-subtext">
                <Radio size={12} className="text-cyber-accent animate-pulse" />
                <span>MONITORING</span>
              </div>
            )}
            <ConnectionStatus isConnected={isConnected} />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 flex flex-col gap-6">

        {/* Alert banner — shows when tokens are triggered */}
        {stats.triggeredTokens > 0 && (
          <div className="border border-cyber-danger/50 bg-cyber-danger/5 rounded-lg px-4 py-3 flex items-center gap-3 animate-fade-in">
            <div className="w-2 h-2 rounded-full bg-cyber-danger animate-pulse" />
            <span className="text-cyber-danger text-sm font-semibold">
              ALERT: {stats.triggeredTokens} honey token
              {stats.triggeredTokens > 1 ? "s" : ""} triggered —
              unauthorized access detected
            </span>
          </div>
        )}

        {/* Stats row */}
        <StatsCards stats={stats} />

        {/* Main grid — event feed + chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <EventFeed events={events} />
          </div>
          <div>
            <SeverityChart events={events} />
          </div>
        </div>

        {/* Token table */}
        <TokenTable tokens={tokens} />

      </main>
    </div>
  );
}