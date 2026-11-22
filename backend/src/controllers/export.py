import csv
import io
from fastapi import HTTPException, Response


def safe(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def export(item):
    if not item.result:
        raise HTTPException(409, '复核结果尚未完成')
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(['复核单', '状态', '结论'])
    writer.writerow([safe(item.title), item.status, safe(item.result['summary'])])
    for key, value in item.result['metrics'].items():
        writer.writerow([key, value])
    rows = item.result['rows']
    if rows:
        writer.writerow([])
        writer.writerow(rows[0].keys())
        writer.writerows([safe(value) for value in row.values()] for row in rows)
    return Response(content='\ufeff' + stream.getvalue(), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="linkage-{item.id}.csv"'})
