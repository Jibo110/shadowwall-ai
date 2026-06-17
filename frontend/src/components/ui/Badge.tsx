import { clsx } from "clsx";
import type { SeverityLevel, TokenStatus } from "@/types";

interface SeverityBadgeProps {
  severity: SeverityLevel;
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  return (
    <span className={`badge-${severity}`}>
      {severity.toUpperCase()}
    </span>
  );
}

interface StatusBadgeProps {
  status: TokenStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const classes = clsx({
    "badge-active": status === "active",
    "badge-triggered": status === "triggered",
    "bg-cyber-muted/10 text-cyber-muted border border-cyber-muted/20 text-xs px-2 py-0.5 rounded-full":
      status === "expired" || status === "archived",
  });

  return <span className={classes}>{status.toUpperCase()}</span>;
}