interface ConnectionStatusProps {
  isConnected: boolean;
}

export function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-2 h-2 rounded-full ${
          isConnected
            ? "bg-cyber-success animate-pulse"
            : "bg-cyber-danger"
        }`}
      />
      <span className="text-xs text-cyber-subtext">
        {isConnected ? "LIVE" : "DISCONNECTED"}
      </span>
    </div>
  );
}