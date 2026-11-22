import json
import logging
import time
from pathlib import Path

from redis.exceptions import RedisError
from sqlalchemy import select, update

from src.config.database import Session
from src.constants.enums import Status
from src.models.entities import Analysis
from src.services.association import analyze
from src.services.business import QUEUE, queue


def next_job():
    with Session() as db:
        item = db.scalar(select(Analysis).where(Analysis.status == Status.QUEUED)
                         .order_by(Analysis.id).limit(1).with_for_update(skip_locked=True))
        if not item:
            return False
        item.status = Status.RUNNING
        db.commit()
        try:
            base = db.get(Analysis, item.base_id) if item.base_id else None
            reference = {'snapshot': base.snapshot, 'result': base.result} if base and base.result else None
            result = analyze(item.snapshot, item.parameters, reference)
            temp = Path(f'/artifacts/.linkage-{item.id}.tmp')
            temp.write_text(json.dumps(result, ensure_ascii=False))
            temp.replace(Path(f'/artifacts/linkage-{item.id}.json'))
            item.result = result
            item.status = Status.COMPLETED
        except ValueError as exc:
            item.note = str(exc)
            item.status = Status.FAILED
        except Exception:
            logging.exception('Analysis %s failed', item.id)
            item.note = '后台计算失败，请检查数据后重提'
            item.status = Status.FAILED
        db.commit()
        return True


def main():
    with Session() as db:
        db.execute(update(Analysis).where(Analysis.status == Status.RUNNING).values(status=Status.QUEUED))
        db.commit()
    while True:
        Path('/tmp/worker-heartbeat').touch()
        if next_job():
            continue
        try:
            queue.blpop(QUEUE, timeout=2)
        except RedisError:
            time.sleep(2)


if __name__ == '__main__':
    main()
