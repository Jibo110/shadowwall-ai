import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { TriggerEvent } from "@/types";

interface SeverityChartProps {
  events: TriggerEvent[];
}

const SEVERITY_COLORS = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#ef4444",
  critical: "#dc2626",
};

export function SeverityChart({ events }: SeverityChartProps) {
  const counts = events.reduce(
    (acc, e) => {
      acc[e.severity] = (acc[e.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const data = Object.entries(counts).map(([name, value]) => ({
    name: name.toUpperCase(),
    value,
  }));

  if (data.length === 0) {
    return (
      <div className="card-glow flex flex-col items-center justify-center h-48">
        <p className="text-cyber-muted text-sm">No events to chart</p>
      </div>
    );
  }

  return (
    <div className="card-glow">
      <h2 className="text-sm font-semibold text-cyber-text uppercase tracking-widest mb-4">
        Severity Distribution
      </h2>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={
                  SEVERITY_COLORS[
                    entry.name.toLowerCase() as keyof typeof SEVERITY_COLORS
                  ] ?? "#4a5568"
                }
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f1729",
              border: "1px solid #1e2d4a",
              borderRadius: "8px",
              color: "#e2e8f0",
              fontSize: "12px",
            }}
          />
          <Legend
            formatter={(value) => (
              <span style={{ color: "#94a3b8", fontSize: "11px" }}>
                {value}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}