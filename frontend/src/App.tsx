import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "@/pages/Dashboard";
import { Login } from "@/pages/Login";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30000,
    },
  },
});

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // Check for existing token on load
    const stored = localStorage.getItem("shadowwall_token");
    if (stored) {
      setToken(stored);
    }
    setChecking(false);
  }, []);

  const handleLogin = (newToken: string) => {
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem("shadowwall_token");
    setToken(null);
  };

  if (checking) {
    return (
      <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
        <div className="text-cyber-accent text-sm animate-pulse">
          Initializing ShadowWall AI...
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      {token ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </QueryClientProvider>
  );
}

export default App;
