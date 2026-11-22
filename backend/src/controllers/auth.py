import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from src.config.database import get_db
from src.config.settings import JWT_SECRET
from src.constants.enums import Role
from src.models.entities import User
from src.utils.security import issue, verify

bearer = HTTPBearer(auto_error=False)


def login(data, db):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify(data.password, user.password_hash):
        raise HTTPException(401, '邮箱或密码不正确')
    return {'token': issue(user), 'role': user.role, 'email': user.email}


def current(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(get_db)):
    if not credentials:
        raise HTTPException(401, '请先登录')
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=['HS256'], options={'require': ['exp', 'sub']})
        user = db.get(User, int(payload['sub']))
    except (jwt.InvalidTokenError, ValueError):
        user = None
    if not user:
        raise HTTPException(401, '登录已失效')
    return user


def writable(user=Depends(current)):
    if user.role not in (Role.MANAGER, Role.ANALYST):
        raise HTTPException(403, '观察员无法编辑或提交分析')
    return user


def manager(user=Depends(current)):
    if user.role != Role.MANAGER:
        raise HTTPException(403, '请由运营负责人签核')
    return user
