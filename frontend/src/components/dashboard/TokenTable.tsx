import { useState } from "react";
import { Trash2, Plus, Shield } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { StatusBadge } from "@/components/ui/Badge";
import { tokenApi } from "@/services/api";
import { useDashboardStore } from "@/stores/dashboardStore";
import type { HoneyToken, TokenType, CreateTokenPayload } from "@/types";

// ----------------------------------------------------------------
// Create Token Modal
// ----------------------------------------------------------------
interface CreateTokenModalProps {
  onClose: () => void;
  onCreated: (token: HoneyToken) => void;
}

function CreateTokenModal({ onClose, onCreated }: CreateTokenModalProps) {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<CreateTokenPayload>({
    label: "",
    token_type: "api_key",
    token_value: "",
    description: "",
    environment: "production",
    planted_location: "",
  });

  const handleSubmit = async () => {
    if (!form.label || !form.token_value) return;
    setLoading(true);
    try {
      const token = await tokenApi.create(form);
      onCreated(token);
      onClose();
    } catch (e) {
      console.error("Failed to create token:", e);
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full bg-cyber-bg border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text font-mono focus:outline-none focus:border-cyber-accent";
  const labelClass = "text-xs text-cyber-subtext uppercase tracking-wider";

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-md">
        <h3 className="text-cyber-accent font-semibold mb-4 uppercase tracking-widest text-sm">
          Deploy New Honey Token
        </h3>
        <div className="flex flex-col gap-3">
          <div>
            <label className={labelClass}>Label</label>
            <input
              className={inputClass}
              placeholder="Production AWS Key"
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
            />
          </div>
          <div>
            <label className={labelClass}>Token Type</label>
            <select
              className={inputClass}
              value={form.token_type}
              onChange={(e) =>
                setForm({ ...form, token_type: e.target.value as TokenType })
              }
            >
              <option value="api_key">API Key</option>
              <option value="aws_key">AWS Key</option>
              <option value="database_url">Database URL</option>
              <option value="jwt_secret">JWT Secret</option>
              <option value="ssh_key">SSH Key</option>
              <option value="webhook_url">Webhook URL</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Token Value (Fake Secret)</label>
            <input
              className={inputClass}
              placeholder="AKIAIOSFODNN7EXAMPLE"
              value={form.token_value}
              onChange={(e) => setForm({ ...form, token_value: e.target.value })}
            />
          </div>
          <div>
            <label className={labelClass}>Environment</label>
            <input
              className={inputClass}
              placeholder="production"
              value={form.environment}
              onChange={(e) => setForm({ ...form, environment: e.target.value })}
            />
          </div>
          <div>
            <label className={labelClass}>Planted Location</label>
            <input
              className={inputClass}
              placeholder=".env file, GitHub secrets..."
              value={form.planted_location}
              onChange={(e) =>
                setForm({ ...form, planted_location: e.target.value })
              }
            />
          </div>
          <div>
            <label className={labelClass}>Description</label>
            <input
              className={inputClass}
              placeholder="Why was this token planted?"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="flex gap-2 mt-2">
            <button
              onClick={onClose}
              className="flex-1 border border-cyber-border text-cyber-subtext rounded px-4 py-2 text-sm hover:border-cyber-muted transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !form.label || !form.token_value}
              className="flex-1 bg-cyber-accent/10 border border-cyber-accent/50 text-cyber-accent rounded px-4 py-2 text-sm hover:bg-cyber-accent/20 transition-colors disabled:opacity-50"
            >
              {loading ? "Deploying..." : "Deploy Token"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------
// Token Table
// ----------------------------------------------------------------
interface TokenTableProps {
  tokens: HoneyToken[];
}

export function TokenTable({ tokens }: TokenTableProps) {
  const [showModal, setShowModal] = useState(false);
  const { setTokens, removeToken } = useDashboardStore();

  const handleCreated = (token: HoneyToken) => {
    setTokens([token, ...tokens]);
  };

  const handleDelete = async (id: string) => {
    try {
      await tokenApi.delete(id);
      removeToken(id);
    } catch (e) {
      console.error("Failed to delete token:", e);
    }
  };

  return (
    <>
      {showModal && (
        <CreateTokenModal
          onClose={() => setShowModal(false)}
          onCreated={handleCreated}
        />
      )}
      <div className="card-glow">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-cyber-accent" />
            <h2 className="text-sm font-semibold text-cyber-text uppercase tracking-widest">
              Deployed Tokens
            </h2>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1 text-xs text-cyber-accent border border-cyber-accent/30 rounded px-3 py-1.5 hover:bg-cyber-accent/10 transition-colors"
          >
            <Plus size={12} />
            Deploy
          </button>
        </div>

        {tokens.length === 0 ? (
          <div className="text-center py-8 text-cyber-muted text-sm">
            No tokens deployed yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-cyber-muted uppercase tracking-wider border-b border-cyber-border">
                  <th className="text-left pb-2 pr-4">Label</th>
                  <th className="text-left pb-2 pr-4">Type</th>
                  <th className="text-left pb-2 pr-4">Environment</th>
                  <th className="text-left pb-2 pr-4">Status</th>
                  <th className="text-left pb-2 pr-4">Deployed</th>
                  <th className="pb-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-border/50">
                {tokens.map((token) => (
                  <tr
                    key={token.id}
                    className={`hover:bg-cyber-border/10 transition-colors ${
                      token.status === "triggered"
                        ? "bg-cyber-danger/5"
                        : ""
                    }`}
                  >
                    <td className="py-2.5 pr-4 text-cyber-text font-medium">
                      {token.label}
                    </td>
                    <td className="py-2.5 pr-4 text-cyber-subtext">
                      {token.token_type.replace("_", " ")}
                    </td>
                    <td className="py-2.5 pr-4 text-cyber-subtext">
                      {token.environment ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4">
                      <StatusBadge status={token.status} />
                    </td>
                    <td className="py-2.5 pr-4 text-cyber-muted">
                      {formatDistanceToNow(new Date(token.created_at), {
                        addSuffix: true,
                      })}
                    </td>
                    <td className="py-2.5">
                      {token.status !== "triggered" && (
                        <button
                          onClick={() => handleDelete(token.id)}
                          className="text-cyber-muted hover:text-cyber-danger transition-colors"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}