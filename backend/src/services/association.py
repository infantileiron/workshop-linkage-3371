from collections import defaultdict
from math import isfinite


def odds(a, b, c, d):
    if b * c == 0:
        return None
    ratio = a * d / (b * c)
    return round(ratio, 4) if isfinite(ratio) else None


def analyze(records, config):
    a_code, b_code = config['course_a'], config['course_b']
    by_venue = defaultdict(lambda: [0, 0, 0, 0])
    cancelled = 0
    for row in records:
        if row['state'] == 'cancelled':
            cancelled += 1
            continue
        selected = set(row['codes'])
        index = 2 * (a_code not in selected) + (b_code not in selected)
        by_venue[row['venue']][index] += 1
    if not by_venue:
        raise ValueError('没有已确认的报名记录')
    pooled = [0, 0, 0, 0]
    numerator = denominator = 0.0
    evidence = []
    for venue, table in sorted(by_venue.items()):
        a, b, c, d = table
        n = sum(table)
        if n < config['min_venue_n']:
            reason = '样本低于门槛'
        elif not all((a + b, c + d, a + c, b + d)):
            reason = '一门课缺少其报名或未报名对照'
        else:
            reason = ''
        if not reason:
            pooled = [old + count for old, count in zip(pooled, table)]
            numerator += a * d / n
            denominator += b * c / n
        evidence.append({'场馆': venue, '样本量': n, '两门均报': a, '仅首课': b, '仅次课': c,
                         '均未报': d, '本馆 OR': odds(a, b, c, d), '纳入口径': reason or '纳入'})
    pooled_ratio = odds(*pooled)
    adjusted = round(numerator / denominator, 4) if denominator else None
    if pooled_ratio is None or adjusted is None:
        action = '证据不足，暂缓组合排课。检查被排除场馆和列联表分母。'
    elif (pooled_ratio - 1) * (adjusted - 1) < 0:
        action = '合并结果与场馆内方向相反。按场馆复核时段和招募构成，暂缓统一捆绑。'
    elif adjusted >= 1.25:
        action = '同报优势较高，可和场馆协调试行相邻场次，再比较独立报名率。'
    else:
        action = '同报优势有限，保留独立报名入口和课程名额。'
    return {'summary': action, 'metrics': {'分层调整 OR': adjusted, '同口径合并 OR': pooled_ratio,
            '纳入报名': sum(pooled), '剔除取消': cancelled}, 'rows': evidence,
            'notes': ['每条确认报名按场馆与两门课的勾选情况归入 2×2 表。',
                      '合并比与调整比使用同一批合格场馆。OR 反映同报关联，单场馆零格不加伪样本。']}
