from collections import defaultdict
from math import isfinite


def odds(a, b, c, d):
    if b * c == 0:
        return None
    ratio = a * d / (b * c)
    return round(ratio, 4) if isfinite(ratio) else None


def venue_versions(records):
    """每个场馆的「报名编号 → 版本」映射，用于判断证据是否可沿用。"""
    versions = defaultdict(dict)
    for row in records:
        versions[row['venue']][row['code']] = row.get('version', 1)
    return versions


def evidence_row(venue, table, config, source):
    a, b, c, d = table
    n = sum(table)
    if n < config['min_venue_n']:
        reason = '样本低于门槛'
    elif not all((a + b, c + d, a + c, b + d)):
        reason = '一门课缺少其报名或未报名对照'
    else:
        reason = ''
    return {'场馆': venue, '样本量': n, '两门均报': a, '仅首课': b, '仅次课': c,
            '均未报': d, '本馆 OR': odds(a, b, c, d), '纳入口径': reason or '纳入',
            '证据来源': source}


def analyze(records, config, base=None):
    """按快照计算分场馆列联表与两种优势比。

    base 为同课程组合与门槛下上一份完整复核（{'snapshot', 'result'}）时，
    报名版本未变的场馆沿用其证据行，其余场馆按发起时锁定的报名版本重算；
    两种优势比始终按合并后的证据同步重算，场馆进出门槛时一起更新。
    """
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
    reusable = {}
    if base and base.get('result'):
        base_rows = {row['场馆']: row for row in base['result'].get('rows', [])}
        current = venue_versions(records)
        for venue, mapping in venue_versions(base.get('snapshot', [])).items():
            if venue in by_venue and venue in base_rows and current.get(venue) == mapping:
                reusable[venue] = base_rows[venue]
    evidence = []
    reused = 0
    for venue in sorted(by_venue):
        if venue in reusable:
            evidence.append({**reusable[venue], '证据来源': '沿用上单'})
            reused += 1
        else:
            evidence.append(evidence_row(venue, by_venue[venue], config, '本次重算'))
    pooled = [0, 0, 0, 0]
    numerator = denominator = 0.0
    for row in evidence:
        if row['纳入口径'] != '纳入':
            continue
        a, b, c, d = row['两门均报'], row['仅首课'], row['仅次课'], row['均未报']
        n = row['样本量']
        pooled = [old + count for old, count in zip(pooled, (a, b, c, d))]
        numerator += a * d / n
        denominator += b * c / n
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
    notes = ['每条确认报名按场馆与两门课的勾选情况归入 2×2 表。',
             '合并比与调整比使用同一批合格场馆。OR 反映同报关联，单场馆零格不加伪样本。']
    if base and base.get('result'):
        notes.append(f'与上一复核单同口径：{reused} 个场馆报名版本未变沿用上次证据，'
                     f'{len(evidence) - reused} 个场馆按本次快照重算，两种优势比随合并证据同步更新。')
    return {'summary': action, 'metrics': {'分层调整 OR': adjusted, '同口径合并 OR': pooled_ratio,
            '纳入报名': sum(pooled), '剔除取消': cancelled}, 'rows': evidence, 'notes': notes}
