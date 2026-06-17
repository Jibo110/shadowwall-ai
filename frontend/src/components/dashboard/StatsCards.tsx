import { Shield, AlertTriangle, Activity, Zap } from "lucide-react";
import type { DashboardStats } from "@/types";

interface StatsCardsProps {
  stats: DashboardStats;
}

interface StatCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: React.ReactNode;
  accent: string;
  alert?: boolean;
}

function StatCard({ title, value, subtitle, icon, accent, alert }: StatCardProps) {
  return (
    <div
      className={`card-glow flex flex-col gap-3 ${
        alert && value > 0 ? "border-cyber-danger/50" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-cyber-subtext uppercase tracking-widest">
          {title}
        </span>
        <div className={`${accent} opacity-80`}>{icon}</div>
      </div>
      <div className={`text-3xl font-bold ${accent} ${alert && value > 0 ? "animate-pulse" : ""}`}>
        {value.toLocaleString()}
      </div>
      <div className="text-xs text-cyber-muted">{subtitle}</div>
    </div>
  );
}

export function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Active Tokens"
        value={stats.activeTokens}
        subtitle={`${stats.totalTokens} total deployed`}
        icon={<Shield size={18} />}
        accent="text-cyber-accent"
      />
      <StatCard
        title="Triggered"
        value={stats.triggeredTokens}
        subtitle="Tokens accessed by threat"
        icon={<AlertTriangle size={18} />}
        accent="text-cyber-danger"
        alert
      />
      <StatCard
        title="Total Events"
        value={stats.totalEvents}
        subtitle="Unauthorized access attempts"
        icon={<Activity size={18} />}
        accent="text-cyber-accent2"
      />
      <StatCard
        title="High Severity"
        value={stats.criticalEvents}
        subtitle="High + critical events"
        icon={<Zap size={18} />}
        accent="text-cyber-warning"
        alert
      />
    </div>
  );
}