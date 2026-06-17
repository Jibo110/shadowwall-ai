/**
 * TypeScript type definitions for ShadowWall AI.
 * These mirror the Pydantic schemas from the backend exactly.
 * If you change a backend schema, update this file too.
 */

// ----------------------------------------------------------------
// Enums — match backend exactly
// ----------------------------------------------------------------
export type TokenType =
  | "api_key"
  | "database_url"
  | "aws_key"
  | "jwt_secret"
  | "ssh_key"
  | "webhook_url"
  | "custom";

export type TokenStatus =
  | "active"
  | "triggered"
  | "expired"
  | "archived";

export type SeverityLevel =
  | "low"
  | "medium"
  | "high"
  | "critical";

// ----------------------------------------------------------------
// Honey Token
// ----------------------------------------------------------------
export interface HoneyToken {
  id: string;
  label: string;
  token_type: TokenType;
  description: string | null;
  environment: string | null;
  planted_location: string | null;
  status: TokenStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  triggered_at: string | null;
}

export interface TokenListResponse {
  items: HoneyToken[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface CreateTokenPayload {
  label: string;
  token_type: TokenType;
  token_value: string;
  description?: string;
  environment?: string;
  planted_location?: string;
}

// ----------------------------------------------------------------
// Trigger Events
// ----------------------------------------------------------------
export interface TriggerEvent {
  id: string;
  token_id: string;
  source_ip: string;
  user_agent: string | null;
  request_method: string | null;
  request_path: string | null;
  severity: SeverityLevel;
  agent_analysis: string | null;
  additional_context: Record<string, unknown> | null;
  created_at: string;
}

// ----------------------------------------------------------------
// WebSocket message envelope
// Every WS message has this shape — switch on 'type'
// ----------------------------------------------------------------
export type WebSocketMessageType =
  | "connection_established"
  | "token_triggered"
  | "agent_analysis_complete"
  | "pong";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  payload?: Record<string, unknown>;
  timestamp?: string;
  message?: string;
  active_connections?: number;
  connections?: number;
}

// ----------------------------------------------------------------
// Dashboard stats (computed on frontend)
// ----------------------------------------------------------------
export interface DashboardStats {
  totalTokens: number;
  activeTokens: number;
  triggeredTokens: number;
  totalEvents: number;
  criticalEvents: number;
  connectedClients: number;
}