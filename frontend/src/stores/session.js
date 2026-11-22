const key = 'hemu-session';
export function session() {
  try { return JSON.parse(sessionStorage.getItem(key)); } catch { return null; }
}
export function setSession(value) {
  if (value) sessionStorage.setItem(key, JSON.stringify(value));
  else sessionStorage.removeItem(key);
}
export function canWrite() { return ['manager', 'analyst'].includes(session()?.role); }
