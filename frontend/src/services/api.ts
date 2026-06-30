/**
 * API service layer.
 * All HTTP calls go through here — never fetch() directly in components.
 * Uses the Vite proxy so no hardcoded localhost URLs in component code.
 */

import axios from "axios";
import type {
  CreateTokenPayload,
  HoneyToken,
  TokenListResponse,
  TriggerEvent,
} from "@/types";

// Axios instance with sensible defaults
const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Attach JWT token to every request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("shadowwall_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses — token expired, redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("shadowwall_token");
      window.location.reload();
    }
    return Promise.reject(error);
  },
);
// ----------------------------------------------------------------
// Token endpoints
// ----------------------------------------------------------------
export const tokenApi = {
  list: async (page = 1, pageSize = 50): Promise<TokenListResponse> => {
    const { data } = await api.get("/tokens/", {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  get: async (id: string): Promise<HoneyToken> => {
    const { data } = await api.get(`/tokens/${id}`);
    return data;
  },

  create: async (payload: CreateTokenPayload): Promise<HoneyToken> => {
    const { data } = await api.post("/tokens/", payload);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/tokens/${id}`);
  },
};

// ----------------------------------------------------------------
// Event endpoints
// ----------------------------------------------------------------
export const eventApi = {
  recent: async (limit = 100): Promise<TriggerEvent[]> => {
    const { data } = await api.get("/events/recent", {
      params: { limit },
    });
    return data;
  },

  forToken: async (tokenId: string): Promise<TriggerEvent[]> => {
    const { data } = await api.get(`/events/token/${tokenId}`);
    return data;
  },
};

export default api;
