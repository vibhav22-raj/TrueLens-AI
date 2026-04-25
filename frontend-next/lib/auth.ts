export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("ds_token");
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("ds_token", token);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("ds_token");
}

export function isAuthed() {
  return !!getToken();
}
