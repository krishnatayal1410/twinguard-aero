from __future__ import annotations
import hashlib,hmac,re,secrets
from datetime import datetime,timezone,timedelta
from sqlalchemy import select,delete
from ..db import SessionLocal,UserAccount,AuthSession

ITERATIONS=260_000
SESSION_DAYS=7

class AuthError(ValueError): pass

def _now(): return datetime.now(timezone.utc)
def _normalize(email:str)->str: return email.strip().lower()
def _token_hash(token:str)->str: return hashlib.sha256(token.encode()).hexdigest()

def validate_password(password:str):
    if len(password)<10: raise AuthError("Password must be at least 10 characters.")
    if not re.search(r"[A-Z]",password): raise AuthError("Password needs an uppercase letter.")
    if not re.search(r"[a-z]",password): raise AuthError("Password needs a lowercase letter.")
    if not re.search(r"\d",password): raise AuthError("Password needs a number.")

def hash_password(password:str)->str:
    validate_password(password)
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def verify_password(password:str,encoded:str)->bool:
    try:
        scheme,it,salt_hex,digest_hex=encoded.split("$",3)
        if scheme!="pbkdf2_sha256": return False
        digest=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt_hex),int(it))
        return hmac.compare_digest(digest.hex(),digest_hex)
    except Exception:
        return False

def _public(user:UserAccount)->dict:
    return {"id":user.id,"name":user.name,"email":user.email,"role":user.role}

def _new_session(db,user:UserAccount)->tuple[str,dict]:
    token=secrets.token_urlsafe(40)
    now=_now()
    db.add(AuthSession(user_id=user.id,token_hash=_token_hash(token),created_at=now,last_seen_at=now,expires_at=now+timedelta(days=SESSION_DAYS)))
    db.commit()
    return token,_public(user)

def signup(name:str,email:str,password:str)->tuple[str,dict]:
    email=_normalize(email)
    validate_password(password)
    with SessionLocal() as db:
        if db.scalar(select(UserAccount).where(UserAccount.email==email)):
            raise AuthError("An account with this email already exists.")
        first=db.scalar(select(UserAccount.id).limit(1)) is None
        user=UserAccount(name=name.strip(),email=email,password_hash=hash_password(password),role="admin" if first else "operator")
        db.add(user);db.commit();db.refresh(user)
        return _new_session(db,user)

def signin(email:str,password:str)->tuple[str,dict]:
    email=_normalize(email)
    with SessionLocal() as db:
        user=db.scalar(select(UserAccount).where(UserAccount.email==email))
        if not user or not user.active or not verify_password(password,user.password_hash):
            raise AuthError("Invalid email or password.")
        return _new_session(db,user)

def session_user(token:str|None)->dict|None:
    if not token:return None
    now=_now();hashed=_token_hash(token)
    with SessionLocal() as db:
        db.execute(delete(AuthSession).where(AuthSession.expires_at<now))
        row=db.scalar(select(AuthSession).where(AuthSession.token_hash==hashed))
        if not row:
            db.commit();return None
        exp=row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
        if exp<now:
            db.delete(row);db.commit();return None
        user=db.get(UserAccount,row.user_id)
        if not user or not user.active:return None
        row.last_seen_at=now;db.commit()
        return _public(user)

def signout(token:str|None):
    if not token:return
    with SessionLocal() as db:
        db.execute(delete(AuthSession).where(AuthSession.token_hash==_token_hash(token)));db.commit()
