from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.config.settings import REDIS_URL
from src.constants.enums import Status
from src.models.entities import Analysis, Audit, Course, Enrollment

queue = Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
QUEUE = 'workshop-linkage:notifications'


def record(obj, exclude=()):
    return {col.key: getattr(obj, col.key) for col in obj.__table__.columns if col.key not in exclude}


def audit(db, user, action, subject):
    db.add(Audit(user_id=user.id, action=action, subject=str(subject)))


def save_input(db, model, data, user):
    if model is Enrollment and data.codes:
        known = set(db.scalars(select(Course.code).where(Course.code.in_(data.codes))))
        if known != set(data.codes):
            raise HTTPException(422, '报名含未知课程编号')
    item = model(**data.model_dump())
    db.add(item)
    audit(db, user, 'create', data.code)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, '编号已登记') from exc
    return record(item)


def submit(db, data, user):
    codes = {data.course_a, data.course_b}
    if set(db.scalars(select(Course.code).where(Course.code.in_(codes)))) != codes:
        raise HTTPException(422, '请选择课程目录中的两门课程')
    sample = list(db.scalars(select(Enrollment).order_by(Enrollment.id)))
    if not sample:
        raise HTTPException(422, '请先录入报名')
    item = Analysis(title=data.title, status=Status.QUEUED, parameters=data.model_dump(exclude={'title'}),
                    snapshot=[record(row) for row in sample], author_id=user.id, result=None)
    db.add(item)
    db.flush()
    audit(db, user, 'queue', item.id)
    db.commit()
    try:
        queue.lpush(QUEUE, item.id)
    except RedisError:
        pass  # Worker polls the durable SQL queue even if the wake-up fails.
    return record(item, ('snapshot',))


def get_analysis(db, id):
    item = db.get(Analysis, id)
    if not item:
        raise HTTPException(404, '找不到复核单')
    return item


def publish(db, id, note, user):
    item = db.scalar(select(Analysis).where(Analysis.id == id).with_for_update())
    if not item:
        raise HTTPException(404, '找不到复核单')
    if item.status != Status.COMPLETED:
        raise HTTPException(409, '只有已完成的复核单可签核')
    item.status = Status.PUBLISHED
    item.note = note
    audit(db, user, 'publish', id)
    db.commit()
    return record(item, ('snapshot',))
