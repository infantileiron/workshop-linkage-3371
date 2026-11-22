export function onForm(form, handler) {
  if (!form) return;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type=submit]');
    const error = form.querySelector('[role=alert]');
    error.textContent = '';
    button.disabled = true;
    try { await handler(Object.fromEntries(new FormData(form))); }
    catch (problem) { error.textContent = problem.message; }
    finally { button.disabled = false; }
  });
}
