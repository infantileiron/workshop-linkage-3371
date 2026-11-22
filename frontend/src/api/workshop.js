import {send} from './client.js';
export const api = {
  login: data => send('/auth/login', data),
  courses: input => send('/courses', input),
  enrollments: (input, venue) => send('/enrollments' + (venue ? `?venue=${encodeURIComponent(venue)}` : ''), input),
  analyses: input => send('/analyses', input),
  analysis: id => send(`/analyses/${id}`),
  publish: (id, note) => send(`/analyses/${id}/publish`, {note}),
  export: id => send(`/analyses/${id}/export`, undefined, true),
};
