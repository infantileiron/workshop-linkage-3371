import {courses} from '../pages/courses.js';
import {enrollments} from '../pages/enrollments.js';
import {analyze} from '../pages/analyze.js';
import {reports} from '../pages/reports.js';
const routes = {courses, enrollments, analyze, reports};
export function route() {
  const [page, id] = location.hash.slice(1).split('/');
  if (Object.hasOwn(routes, page)) return [page, () => routes[page](/^\d+$/.test(id) ? Number(id) : null)];
  return ['courses', courses];
}
