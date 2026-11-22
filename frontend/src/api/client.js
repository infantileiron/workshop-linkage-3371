import {session, setSession} from '../stores/session.js';

export async function send(path, payload, download = false) {
  const headers = {};
  if (session()?.token) headers.Authorization = `Bearer ${session().token}`;
  if (payload !== undefined) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, {
    headers, method:payload === undefined ? 'GET' : 'POST',
    body:payload === undefined ? undefined : JSON.stringify(payload),
  });
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') { setSession(null); window.dispatchEvent(new Event('session-expired')); }
    const problem = await response.json();
    const detail = Array.isArray(problem.detail) ? problem.detail.map(row => `${row.loc.at(-1)} ${row.msg}`).join('；') : problem.detail;
    throw new Error(detail || '操作失败，请重试');
  }
  return download ? response.blob() : response.json();
}
