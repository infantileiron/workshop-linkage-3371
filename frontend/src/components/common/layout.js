import {h} from '../../utils/html.js';
import {roles} from '../../constants/enums.js';
export const menu = [['courses','课程与名额'],['enrollments','场馆报名'],['analyze','联报核查'],['reports','排课建议']];
export function shell(body, page, user) {
  return `<header class="masthead"><a class="brand" href="#courses">禾埠木作 <span>课程运营</span></a>
    <nav aria-label="业务模块">${menu.map(([link, label]) => `<a href="#${link}" ${page === link ? 'aria-current="page"' : ''}>${h(label)}</a>`).join('')}</nav>
    <div class="identity"><span>${h(roles[user.role])}</span><button class="secondary" id="logout">退出</button></div></header>
    <main>${body}</main><footer>禾埠木作 · 场馆排课工作台</footer>`;
}
export function heading(title, detail) { return `<div class="heading"><h1>${h(title)}</h1><p>${h(detail)}</p></div>`; }
