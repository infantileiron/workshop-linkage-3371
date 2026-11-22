import os,hashlib,hmac
from datetime import datetime,timedelta,timezone
import jwt
from src.config.settings import JWT_SECRET
def password_hash(p):
    salt=os.urandom(16).hex()
    return salt+":"+hashlib.pbkdf2_hmac('sha256',p.encode(),salt.encode(),180000).hex()
def verify(p,h):
    salt,value=h.split(':')
    return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',p.encode(),salt.encode(),180000).hex(),value)
def issue(user):
    return jwt.encode({'sub':str(user.id),'exp':datetime.now(timezone.utc)+timedelta(hours=8)},JWT_SECRET,algorithm='HS256')
