export const LANGS = { python: "Python", javascript: "JavaScript", java: "Java", cpp: "C++" };
export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => (t ? localStorage.setItem("token", t) : localStorage.removeItem("token"));

export async function api(path, body) {
  const res = await fetch((import.meta.env.VITE_API_URL || "") + "/api" + path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json", ...(getToken() ? { Authorization: "Bearer " + getToken() } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}
