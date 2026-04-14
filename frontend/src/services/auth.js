const AUTH_API = "/api/auth";
const TOKEN_STORAGE_KEY = "token";

async function authRequest(path, payload) {
  const response = await fetch(`${AUTH_API}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Authentication request failed");
  }

  return data;
}

function parseTokenPayload(token) {
  try {
    const [, payload] = token.split(".");
    if (!payload) {
      return null;
    }

    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "="
    );

    return JSON.parse(window.atob(padded));
  } catch {
    return null;
  }
}

export async function signup(data) {
  return authRequest("/signup", data);
}

export async function login(data) {
  return authRequest("/login", data);
}

export function persistToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function isTokenValid(token) {
  if (!token) {
    return false;
  }

  const payload = parseTokenPayload(token);
  if (!payload) {
    return false;
  }

  if (!payload.exp) {
    return true;
  }

  return payload.exp * 1000 > Date.now();
}
