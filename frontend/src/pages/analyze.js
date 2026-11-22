import {api} from '../api/workshop.js';
import {heading} from '../components/common/layout.js';
import {states} from '../constants/enums.js';
import {onForm} from '../hooks/forms.js';
import {canWrite} from '../stores/session.js';
import {h} from '../utils/html.js';

export async function analyze() {
  const [courses, runs] = await Promise.all([api.courses(), api.analyses()]);
  const select = selected => courses.map(x => `<option value="${h(x.code)}" ${x.code === selected ? 'selected' : ''}>${h(x.title)} · ${h(x.code)}</option>`).join('');
  return {
    html: heading('联报核查', '对比合并与按场馆调整的优势比。同一批合格场馆用于两次计算。') +
      `<div class="workarea reverse"><section class="sheet"><h2>新建核查单</h2>${canWrite() ? `
      <form id="analysis-form"><label>核查单标题<input name="title" required value="周末联报排课复核"></label>
      <label>首门课<select name="course_a">${select('WOOD-11')}</select></label>
      <label>次门课<select name="course_b">${select('LACQ-24')}</select></label>
      <label>每馆最少有效报名<input name="min_venue_n" type="number" min="2" max="200" value="12" required></label>
      <button type="submit">锁定报名快照并运算</button><p role="alert"></p></form>` : '<p>观察员可查看已有核查单。</p>'}</section>
      <section class="sheet"><h2>计算记录</h2><ul class="runs">${runs.map(x => `<li><a href="#reports/${x.id}">${h(x.title)}</a><span>${h(states[x.status])}</span></li>`).join('') || '<li>首次运行后会出现记录。</li>'}</ul></section></div>`,
    bind(root) { onForm(root.querySelector('#analysis-form'), async data => {
      const run = await api.analyses({...data, min_venue_n:Number(data.min_venue_n)});
      location.hash = `reports/${run.id}`;
    }); }
  };
}
