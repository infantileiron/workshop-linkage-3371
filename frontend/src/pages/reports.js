import {api} from '../api/workshop.js';
import {heading} from '../components/common/layout.js';
import {metrics} from '../components/common/metrics.js';
import {table} from '../components/common/table.js';
import {states} from '../constants/enums.js';
import {onForm} from '../hooks/forms.js';
import {session} from '../stores/session.js';
import {h} from '../utils/html.js';

export async function reports(id) {
  const list = await api.analyses();
  const run = id || list.length ? await api.analysis(id || list[0].id) : null;
  const sidebar = `<aside class="sheet"><h2>复核单</h2><ul class="runs">${list.map(x => `<li><a href="#reports/${x.id}">${h(x.title)}</a><span>${h(states[x.status])}</span></li>`).join('') || '<li>暂无复核单。</li>'}</ul></aside>`;
  let content = '<div class="empty">先在 <a href="#analyze">联报核查</a> 锁定报名快照。</div>';
  if (run) {
    const output = run.result;
    content = `<h2>${h(run.title)}</h2><p class="state">${h(states[run.status])}</p>`;
    if (output) {
      const rows = output.rows;
      content += `${metrics(output.metrics)}<p class="decision">${h(output.summary)}</p>
        <h3>场馆列联表</h3>${table(Object.keys(rows[0]), rows.map(Object.values))}
        <ul class="notes">${output.notes.map(note => `<li>${h(note)}</li>`).join('')}</ul>
        ${run.note ? `<p class="signed">签核意见 · ${h(run.note)}</p>` : ''}<button class="secondary" id="export">下载场馆复核 CSV</button><p id="export-error" role="alert"></p>`;
      if (session()?.role === 'manager' && run.status === 'completed') content += `<form id="publish-form"><label>签核意见<input name="note" required minlength="3"></label><button type="submit">签核排课建议</button><p role="alert"></p></form>`;
    } else {
      content += `<p>${h(run.note || 'Worker 正在读取锁定的报名快照，页面将自动刷新。')}</p>`;
    }
  }
  return {
    html:heading('排课建议','核对各场馆的分母、排除原因及计算方向。运营负责人在此保留签核意见。') + `<div class="workarea"> <section class="sheet" id="report">${content}</section>${sidebar}</div>`,
    bind(root, refresh, signal) {
      if (run && ['queued','running'].includes(run.status)) {
        const timer = setTimeout(refresh, 900);
        signal.addEventListener('abort', () => clearTimeout(timer));
      }
      root.querySelector('#export')?.addEventListener('click', async () => {
        try {
          const url = URL.createObjectURL(await api.export(run.id));
          const link = document.createElement('a');
          link.href = url;
          link.download = `linkage-${run.id}.csv`;
          link.click();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (error) { root.querySelector('#export-error').textContent = error.message; }
      });
      onForm(root.querySelector('#publish-form'), async data => { await api.publish(run.id, data.note); refresh(); });
    }
  };
}
