from fastapi import APIRouter, Depends
from sqlalchemy import select

from src.config.database import get_db
from src.controllers.auth import current, login, manager, writable
from src.controllers.export import export
from src.models.entities import Analysis, Audit, Course, Enrollment
from src.schemas.business import AnalysisInput, CourseInput, EnrollmentInput, Login, Publication
from src.services import business as svc

router = APIRouter(prefix='/api')


@router.post('/auth/login')
def sign_in(data: Login, db=Depends(get_db)):
    return login(data, db)


@router.get('/auth/me')
def me(user=Depends(current)):
    return {'email': user.email, 'role': user.role}


@router.get('/courses')
def courses(db=Depends(get_db), user=Depends(current)):
    return [svc.record(item) for item in db.scalars(select(Course).order_by(Course.code))]


@router.post('/courses', status_code=201)
def create_course(data: CourseInput, db=Depends(get_db), user=Depends(writable)):
    return svc.save_input(db, Course, data, user)


@router.get('/enrollments')
def enrollments(venue: str | None = None, db=Depends(get_db), user=Depends(current)):
    query = select(Enrollment).order_by(Enrollment.id.desc())
    if venue:
        query = query.where(Enrollment.venue == venue)
    return [svc.record(item) for item in db.scalars(query)]


@router.post('/enrollments', status_code=201)
def create_enrollment(data: EnrollmentInput, db=Depends(get_db), user=Depends(writable)):
    return svc.save_input(db, Enrollment, data, user)


@router.get('/analyses')
def analyses(db=Depends(get_db), user=Depends(current)):
    return [svc.record(item, ('snapshot', 'result')) for item in db.scalars(select(Analysis).order_by(Analysis.id.desc()))]


@router.post('/analyses', status_code=202)
def enqueue(data: AnalysisInput, db=Depends(get_db), user=Depends(writable)):
    return svc.submit(db, data, user)


@router.get('/analyses/{id}')
def analysis(id: int, db=Depends(get_db), user=Depends(current)):
    return svc.record(svc.get_analysis(db, id), ('snapshot',))


@router.get('/analyses/{id}/export')
def download(id: int, db=Depends(get_db), user=Depends(current)):
    return export(svc.get_analysis(db, id))


@router.post('/analyses/{id}/publish')
def publish(id: int, data: Publication, db=Depends(get_db), user=Depends(manager)):
    return svc.publish(db, id, data.note, user)


@router.get('/audits')
def audit_log(db=Depends(get_db), user=Depends(manager)):
    return [svc.record(item) for item in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))]
