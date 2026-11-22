import {api} from '../api/workshop.js';
import {onForm} from '../hooks/forms.js';
import {setSession} from '../stores/session.js';

export function login(root, refresh) {
  root.innerHTML = `<main class="login"><section class="intro"><div class="maker-mark" aria-hidden="true">禾</div>
    <div><p>禾埠木作</p><h1>工坊课程<br>联报核查</h1><p>把各场馆报名账放在一起，核对同报关系，再安排下一轮课程。</p></div></section>
    <section class="sheet signin"><h2>进入课程运营台</h2><form id="login-form">
      <label>邮箱<input name="email" type="email" value="analyst@hemu.demo" required autocomplete="username"></label>
      <label>密码<input name="password" type="password" value="Woodwork2026!" required autocomplete="current-password"></label>
      <button type="submit">登录工作台</button><p role="alert"></p>
      <small>演示账号可切换 analyst、manager、viewer 邮箱前缀。</small></form></section></main>`;
  onForm(root.querySelector('#login-form'), async data => { setSession(await api.login(data)); refresh(); });
}
