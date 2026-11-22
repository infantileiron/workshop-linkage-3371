import {shell} from './components/common/layout.js';
import {login} from './pages/login.js';
import {route} from './router/router.js';
import {session, setSession} from './stores/session.js';
import {h} from './utils/html.js';

const root = document.querySelector('#app');
let lifetime;
async function render() {
  lifetime?.abort();
  lifetime = new AbortController();
  const {signal} = lifetime;
  const user = session();
  if (!user) { login(root, render); return; }
  const [key, load] = route();
  const after = () => root.querySelector('#logout')?.addEventListener('click', () => { setSession(null); render(); });
  try {
    const {html, bind} = await load();
    if (signal.aborted) return;
    root.innerHTML = shell(html, key, user);
    after();
    bind?.(root, render, signal);
  } catch (error) {
    if (signal.aborted) return;
    root.innerHTML = shell(`<section class="sheet"><p role="alert">${h(error.message)}</p><button id="retry">重试</button></section>`, key, user);
    after();
    root.querySelector('#retry').addEventListener('click', render);
  }
}
window.addEventListener('hashchange', render);
window.addEventListener('session-expired', render);
render();
