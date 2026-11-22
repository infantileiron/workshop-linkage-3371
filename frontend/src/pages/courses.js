import {api} from '../api/workshop.js';
import {heading} from '../components/common/layout.js';
import {table} from '../components/common/table.js';
import {onForm} from '../hooks/forms.js';
import {canWrite} from '../stores/session.js';

export async function courses() {
  const rows = await api.courses();
  return {
    html: heading('课程与名额', '维护课程编号及每场核准容量。报名意向用于联报核查，可覆盖多个班次。') +
      `<div class="workarea"><section class="sheet"><h2>课程目录</h2>${table(['课程编号','课程','工序','每场名额'], rows.map(x => [x.code,x.title,x.category,x.seats]))}</section>` +
      (canWrite() ? `<section class="sheet tools"><h2>登记课程</h2><form id="course-form">
      <label>课程编号<input name="code" required placeholder="CARVE-01"></label><label>课程名称<input name="title" required></label>
      <label>工序分类<input name="category" required></label><label>每场名额<input name="seats" type="number" min="1" max="500" required></label>
      <button type="submit">登记课程</button><p role="alert"></p></form></section>` : '') + '</div>',
    bind(root, refresh) { onForm(root.querySelector('#course-form'), async data => { await api.courses({...data, seats:Number(data.seats)}); refresh(); }); }
  };
}
