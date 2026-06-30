import { useState } from "react";
import { Shield, Eye, EyeOff } from "lucide-react";
import axios from "axios";

interface LoginProps {
  onLogin: (token: string) => void;
}

export function Login({ onLogin }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");

  const handleSubmit = async () => {
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        // Register first
        await axios.post("/api/v1/auth/register", {
          email,
          username,
          password,
        });
        // Then login automatically
      }

      const res = await axios.post("/api/v1/auth/login", {
        email,
        password,
      });

      const token = res.data.access_token;
      localStorage.setItem("shadowwall_token", token);
      onLogin(token);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: unknown } } };
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError((detail[0] as { msg?: string })?.msg || "Validation error");
      } else {
        setError((detail as string) || "Authentication failed");
      }
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full bg-cyber-bg border border-cyber-border rounded px-4 py-3 text-sm text-cyber-text font-mono focus:outline-none focus:border-cyber-accent transition-colors";

  return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center p-4">
      {/* Background grid effect */}
      <div
        className="fixed inset-0 opacity-5"
        style={{
          backgroundImage:
            "linear-gradient(#00d4ff 1px, transparent 1px), linear-gradient(90deg, #00d4ff 1px, transparent 1px)",
          backgroundSize: "50px 50px",
        }}
      />

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyber-accent/10 border border-cyber-accent/30 mb-4 animate-glow">
            <Shield size={32} className="text-cyber-accent" />
          </div>
          <h1 className="text-2xl font-bold text-cyber-accent tracking-widest uppercase">
            ShadowWall AI
          </h1>
          <p className="text-cyber-subtext text-sm mt-1">
            Cyber Deception Platform
          </p>
        </div>

        {/* Card */}
        <div className="card-glow">
          <h2 className="text-sm font-semibold text-cyber-text uppercase tracking-widest mb-6">
            {isRegister ? "Create Account" : "Secure Access"}
          </h2>

          <div className="flex flex-col gap-4">
            {isRegister && (
              <div>
                <label className="text-xs text-cyber-subtext uppercase tracking-wider block mb-1">
                  Username
                </label>
                <input
                  className={inputClass}
                  placeholder="analyst01"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            )}

            <div>
              <label className="text-xs text-cyber-subtext uppercase tracking-wider block mb-1">
                Email
              </label>
              <input
                className={inputClass}
                type="email"
                placeholder="analyst@shadowwall.io"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              />
            </div>

            <div>
              <label className="text-xs text-cyber-subtext uppercase tracking-wider block mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  className={inputClass}
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                />
                <button
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-subtext"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-cyber-danger text-xs bg-cyber-danger/10 border border-cyber-danger/20 rounded px-3 py-2">
                {error}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading || !email || !password}
              className="w-full bg-cyber-accent/10 border border-cyber-accent/50 text-cyber-accent rounded px-4 py-3 text-sm font-semibold uppercase tracking-widest hover:bg-cyber-accent/20 transition-colors disabled:opacity-50 mt-2"
            >
              {loading
                ? "Authenticating..."
                : isRegister
                  ? "Create Account"
                  : "Access Platform"}
            </button>

            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
              className="text-xs text-cyber-muted hover:text-cyber-subtext transition-colors text-center"
            >
              {isRegister
                ? "Already have access? Sign in"
                : "No account? Register"}
            </button>
          </div>
        </div>

        <p className="text-center text-cyber-muted text-xs mt-6">
          Unauthorized access is monitored and logged
        </p>
      </div>
    </div>
  );
}
