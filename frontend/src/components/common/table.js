import {h} from '../../utils/html.js';
export function table(columns, rows, empty = '暂无记录，可先维护课程目录或录入确认报名。') {
  if (!rows.length) return `<p class="empty">${h(empty)}</p>`;
  return `<div class="scroll"><table><thead><tr>${columns.map(name => `<th>${h(name)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${h(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
