import {h} from '../../utils/html.js';
export function metrics(values) {
  return `<dl class="metrics">${Object.entries(values).map(([label,value]) => `<div><dt>${h(label)}</dt><dd>${h(value)}</dd></div>`).join('')}</dl>`;
}
