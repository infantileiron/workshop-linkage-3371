import json
from sqlalchemy import func, select

from src.config.database import Base, Session, engine
from src.constants.enums import Role, Status
from src.models.entities import Analysis, Course, Enrollment, User
from src.services.business import record
from src.utils.security import password_hash

COURSES = [('WOOD-11','木雕浅刻',22,'雕刻'), ('LACQ-24','木片彩漆',20,'上漆'),
           ('JOIN-06','榫卯入门',18,'木构'), ('SAND-18','研磨封蜡',16,'饰面')]
VENUES = [('河湾老仓', (30,30,30,10)), ('望桥木校', (3,17,17,63)), ('槐里快闪', (1,1,0,2))]


def seed():
    Base.metadata.create_all(engine)
    with Session() as db:
        for role in Role:
            email = f'{role}@hemu.demo'
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, role=role, password_hash=password_hash('Woodwork2026!')))
        known = set(db.scalars(select(Course.code)))
        db.add_all(Course(code=code, title=title, seats=seats, category=category)
                   for code, title, seats, category in COURSES if code not in known)
        registered = set(db.scalars(select(Enrollment.code)))
        for idx, (venue, counts) in enumerate(VENUES, 1):
            number = 0
            for selection, count in zip((['WOOD-11','LACQ-24'], ['WOOD-11'], ['LACQ-24'], []), counts):
                for _ in range(count):
                    number += 1
                    code = f'NOV-{idx:02d}-{number:03d}'
                    if code not in registered:
                        courses = selection + (['JOIN-06'] if number % 5 == 0 else [])
                        db.add(Enrollment(code=code, venue=venue, state='confirmed', codes=courses))
            code = f'NOV-{idx:02d}-X01'
            if code not in registered:
                db.add(Enrollment(code=code, venue=venue, state='cancelled', codes=['WOOD-11','LACQ-24']))
        db.flush()
        title = '11 月周末 · 木雕与上漆联报复核'
        if not db.scalar(select(Analysis).where(Analysis.title == title)):
            owner = db.scalar(select(User).where(User.role == Role.ANALYST))
            db.add(Analysis(title=title, status=Status.QUEUED, author_id=owner.id,
                            parameters={'course_a':'WOOD-11','course_b':'LACQ-24','min_venue_n':12},
                            snapshot=[record(row) for row in db.scalars(select(Enrollment).order_by(Enrollment.id))],
                            result=None))
        db.commit()
        return {model.__tablename__: db.scalar(select(func.count()).select_from(model))
                for model in (User, Course, Enrollment, Analysis)}


if __name__ == '__main__':
    print(json.dumps(seed(), sort_keys=True))
