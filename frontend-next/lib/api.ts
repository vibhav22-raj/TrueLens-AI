import axios from "axios";
import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const client = axios.create({
  baseURL: API_URL,
  timeout: 120000
});

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function extractApiError(error: unknown, fallback = "Something went wrong.") {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string })?.detail;
    if (detail) return detail;
    if (error.message) return error.message;
  }
  return fallback;
}

export async function apiLogin(payload: { email: string; password: string }) {
  const { data } = await client.post("/auth/login", payload);
  return data;
}

export async function apiSignup(payload: {
  email: string;
  password: string;
  name?: string;
  username?: string;
}) {
  const normalizedName = (payload.name || payload.email.split("@")[0] || "DeepShield User").trim();
  const safePayload = {
    name: normalizedName,
    username: payload.username?.trim() || normalizedName.toLowerCase().replace(/\s+/g, "_"),
    email: payload.email.trim(),
    password: payload.password
  };
  const { data } = await client.post("/auth/signup", safePayload);
  return data;
}

export async function apiRequestPasswordOtp(payload: { email: string }) {
  const { data } = await client.post("/auth/forgot-password/request", {
    email: payload.email.trim()
  });
  return data as { message: string; sent_to_email: boolean; debug_otp?: string | null };
}

export async function apiResetPasswordWithOtp(payload: {
  email: string;
  otp: string;
  new_password: string;
}) {
  const { data } = await client.post("/auth/forgot-password/reset", {
    email: payload.email.trim(),
    otp: payload.otp.trim(),
    new_password: payload.new_password
  });
  return data as { message: string };
}

export async function apiMe() {
  const { data } = await client.get("/users/me", { headers: { ...authHeaders() } });
  return data;
}

export async function apiHistory() {
  const { data } = await client.get("/users/history", { headers: { ...authHeaders() } });
  return data;
}

export async function apiAdminAnalytics() {
  const { data } = await client.get("/admin/analytics", { headers: { ...authHeaders() } });
  return data;
}

export async function apiPredict(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/predict", form, {
    headers: { ...authHeaders() }
  });
  return data;
}
