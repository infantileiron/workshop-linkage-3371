import {api} from '../api/workshop.js';
import {heading} from '../components/common/layout.js';
import {table} from '../components/common/table.js';
import {states} from '../constants/enums.js';
import {onForm} from '../hooks/forms.js';
import {canWrite} from '../stores/session.js';
import {h} from '../utils/html.js';

export async function enrollments() {
  const [rows, courses] = await Promise.all([api.enrollments(), api.courses()]);
  const venues = [...new Set(rows.map(row => row.venue))];
  const renderTable = list => table(['报名编号','场馆','状态','勾选课程'], list.map(x => [x.code,x.venue,states[x.state],x.codes.join('、') || '未报目录课程']));
  const form = `<section class="sheet tools"><h2>录入报名</h2><form id="enrollment-form">
    <label>报名编号<input name="code" required placeholder="NOV-04-001"></label><label>场馆<input name="venue" required></label>
    <label>状态<select name="state"><option value="confirmed">已确认</option><option value="cancelled">已取消</option></select></label>
    <fieldset><legend>勾选课程</legend>${courses.map(item => `<label class="check"><input type="checkbox" name="codes" value="${h(item.code)}">${h(item.title)}</label>`).join('')}</fieldset>
    <button type="submit">保存报名</button><p role="alert"></p></form></section>`;
  return {
    html:heading('场馆报名', '一个报名编号代表一个独立报名单位。取消记录留在台账里，核查时剔除。') +
      `<div class="workarea"><section class="sheet"><h2>报名清单</h2><label class="filter">场馆<select id="venue"><option value="">全部场馆</option>${venues.map(x => `<option>${h(x)}</option>`).join('')}</select></label><p id="row-count">${rows.length} 条</p><div id="enrollments" class="tall">${renderTable(rows)}</div></section>${canWrite() ? form : ''}</div>`,
    bind(root, refresh) {
      root.querySelector('#venue').addEventListener('change', async event => {
        const venue = event.target.value;
        try {
          const filtered = await api.enrollments(undefined, venue);
          if (event.target.value !== venue) return;
          root.querySelector('#row-count').textContent = `${filtered.length} 条`;
          root.querySelector('#enrollments').innerHTML = renderTable(filtered);
        } catch (error) { root.querySelector('#row-count').textContent = error.message; }
      });
      const target = root.querySelector('#enrollment-form');
      onForm(target, async data => {
        await api.enrollments({...data, codes:new FormData(target).getAll('codes')});
        refresh();
      });
    }
  };
}
