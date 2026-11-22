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
        ensure_known_courses(db, data.codes)
    item = model(**data.model_dump())
    db.add(item)
    audit(db, user, 'create', data.code)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, '编号已登记') from exc
    return record(item)


def ensure_known_courses(db, codes):
    known = set(db.scalars(select(Course.code).where(Course.code.in_(codes))))
    if known != set(codes):
        raise HTTPException(422, '报名含未知课程编号')


def supplement(db, code, data, user):
    """补单对账：按报名编号加版本号取舍，乱序到达的旧版本不得覆盖台账。"""
    ensure_known_courses(db, data.codes)
    item = db.scalar(select(Enrollment).where(Enrollment.code == code).with_for_update())
    if item and data.version <= item.version:
        raise HTTPException(409, f'补单版本 {data.version} 不新于台账版本 {item.version}，未覆盖现有记录')
    if item:
        item.venue, item.state, item.codes = data.venue, data.state, data.codes
        item.version = data.version
        action = 'supplement'
    else:
        item = Enrollment(code=code, venue=data.venue, state=data.state,
                          codes=data.codes, version=data.version)
        db.add(item)
        action = 'create'
    audit(db, user, action, code)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, '编号已登记，请刷新后按最新版本补单') from exc
    return record(item)


def latest_base(db, parameters):
    """同课程组合与门槛下最近一份完整复核，作为增量重算的证据底单。"""
    done = select(Analysis).where(Analysis.status.in_([Status.COMPLETED, Status.PUBLISHED]),
                                  Analysis.result.isnot(None)).order_by(Analysis.id.desc())
    return next((item for item in db.scalars(done) if item.parameters == parameters), None)


def submit(db, data, user):
    codes = {data.course_a, data.course_b}
    if set(db.scalars(select(Course.code).where(Course.code.in_(codes)))) != codes:
        raise HTTPException(422, '请选择课程目录中的两门课程')
    sample = list(db.scalars(select(Enrollment).order_by(Enrollment.id)))
    if not sample:
        raise HTTPException(422, '请先录入报名')
    parameters = data.model_dump(exclude={'title'})
    base = latest_base(db, parameters)
    item = Analysis(title=data.title, status=Status.QUEUED, parameters=parameters,
                    snapshot=[record(row) for row in sample], author_id=user.id, result=None,
                    base_id=base.id if base else None)
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


def retry(db, id, user):
    """失败重试复用原复核单与锁定快照，不新增复核。"""
    item = db.scalar(select(Analysis).where(Analysis.id == id).with_for_update())
    if not item:
        raise HTTPException(404, '找不到复核单')
    if item.status != Status.FAILED:
        raise HTTPException(409, '只有需复查的复核单可重试')
    item.status = Status.QUEUED
    item.note = ''
    audit(db, user, 'retry', id)
    db.commit()
    try:
        queue.lpush(QUEUE, item.id)
    except RedisError:
        pass
    return record(item, ('snapshot',))
