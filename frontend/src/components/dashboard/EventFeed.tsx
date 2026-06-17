import { formatDistanceToNow } from "date-fns";
import { AlertTriangle, Globe, Terminal } from "lucide-react";
import { SeverityBadge } from "@/components/ui/Badge";
import type { TriggerEvent } from "@/types";

interface EventFeedProps {
  events: TriggerEvent[];
}

interface EventRowProps {
  event: TriggerEvent;
  isNew?: boolean;
}

function EventRow({ event, isNew }: EventRowProps) {
  return (
    <div
      className={`flex flex-col gap-2 p-3 rounded-lg border transition-all duration-500 ${
        isNew
          ? "border-cyber-danger/50 bg-cyber-danger/5 animate-fade-in"
          : "border-cyber-border bg-cyber-surface/50"
      }`}
    >
      {/* Top row — severity + IP + time */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle
            size={14}
            className={
              event.severity === "critical" || event.severity === "high"
                ? "text-cyber-danger"
                : "text-cyber-warning"
            }
          />
          <SeverityBadge severity={event.severity} />
          <div className="flex items-center gap-1 text-cyber-accent text-xs font-mono">
            <Globe size={12} />
            {event.source_ip}
          </div>
        </div>
        <span className="text-xs text-cyber-muted whitespace-nowrap">
          {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
        </span>
      </div>

      {/* Bottom row — request details */}
      {event.request_path && (
        <div className="flex items-center gap-2 text-xs text-cyber-subtext">
          <Terminal size={12} className="text-cyber-muted" />
          <span className="font-mono">
            {event.request_method && (
              <span className="text-cyber-accent2 mr-2">
                {event.request_method}
              </span>
            )}
            {event.request_path}
          </span>
        </div>
      )}

      {/* Agent analysis */}
      {event.agent_analysis && (
        <div className="text-xs text-cyber-subtext bg-cyber-bg/50 rounded px-2 py-1 border-l-2 border-cyber-accent2">
          🤖 {event.agent_analysis}
        </div>
      )}
    </div>
  );
}

export function EventFeed({ events }: EventFeedProps) {
  if (events.length === 0) {
    return (
      <div className="card-glow h-full flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-cyber-text uppercase tracking-widest">
            Live Event Feed
          </h2>
          <span className="text-xs text-cyber-muted">0 events</span>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-cyber-muted text-4xl mb-3">◎</div>
            <p className="text-cyber-muted text-sm">Monitoring active</p>
            <p className="text-cyber-muted text-xs mt-1">
              Awaiting honey token triggers...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-glow flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-cyber-text uppercase tracking-widest">
          Live Event Feed
        </h2>
        <span className="text-xs text-cyber-muted">{events.length} events</span>
      </div>
      <div className="flex flex-col gap-2 overflow-y-auto max-h-[500px] pr-1">
        {events.map((event, index) => (
          <EventRow key={event.id} event={event} isNew={index === 0} />
        ))}
      </div>
    </div>
  );
}