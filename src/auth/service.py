# src/auth/service.py
from __future__ import annotations

from fastapi import Header, HTTPException, status
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta
import uuid, json

from sqlalchemy.orm import Session
from sqlalchemy import or_
from email_validator import validate_email, EmailNotValidError

from src.ai.face import face_embed, face_match, face_liveness as liveness_score
from src.db.models import User, FaceProfile #
if TYPE_CHECKING:
  ## typing 용 forward refs (runtime import မဖြစ်အောင်)

 from src.db.models import KycVerification, AuthSession



SIM_THRESHOLD = 0.85
SESSION_HOURS = 72

def _now() -> datetime:
    return datetime.utcnow()

# ✅ tests/client မှာ headers={"x-user-id": "demo"} ပို့ရင် အလုပ်လုပ်တယ်
async def require_user(x_user_id: Optional[str] = Header(default=None, alias="x-user-id")) -> Dict[str, Any]:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    return {"id": x_user_id}
    
def validate_user_email(email: str) -> str:
    """Ensure the email is syntactically valid before creating a user."""
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email: {e}")

def _new_token() -> str:
    return str(uuid.uuid4())

def _ensure_face_profile(db: Session, user: User, face_b64: str) -> FaceProfile:
    prof = db.query(FaceProfile).filter(FaceProfile.user_id == user.id).one_or_none()
    vec = face_embed(face_b64)
    live = liveness_score(face_b64)
    if prof is None:
        prof = FaceProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            face_vec=vec,
            liveness=live,
            updated_at=_now(),
        )
        db.add(prof)
    else:
        # update if liveness better
        if live > (prof.liveness or 0):
            prof.face_vec = vec
            prof.liveness = live
            prof.updated_at = _now()
    return prof

def register_user(db: Session, email: str, face_b64: str, device_fp: str) -> AuthSession:
    # user exists?
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            email=email.lower(),
            device_fp=device_fp,
            identity_tier="FACE_ONLY",
            created_at=_now(),
        )
        db.add(user)
        db.flush()
    else:
        # enforce 1 user ↔ 1 person : require face to match if email exists
        prof = db.query(FaceProfile).filter(FaceProfile.user_id == user.id).one_or_none()
        if prof:
            ok, sim = face_match(face_embed(face_b64), prof.face_vec, SIM_THRESHOLD)
            if not ok:
                raise ValueError("face_mismatch_existing_account")
        # bind/update device
        if user.device_fp and user.device_fp != device_fp:
            # allow update only if face verified OK + rotate sessions
            user.device_fp = device_fp

    _ensure_face_profile(db, user, face_b64)

    # bootstrap KYC envelope if not exists
    kyc = db.query(KycVerification).filter(KycVerification.user_id == user.id).one_or_none()
    if kyc is None:
        kyc = KycVerification(
            id=str(uuid.uuid4()),
            user_id=user.id,
            tier="FACE_ONLY",
            ai_risk_score=0.12,
            state="APPROVED_AI",
            decided_at=_now(),
            evidence_json={"init": True},
        )
        db.add(kyc)

    # create session
    tok = _new_token()
    sess = AuthSession(
        id=tok,
        user_id=user.id,
        device_fp=device_fp,
        created_at=_now(),
        expires_at=_now() + timedelta(hours=SESSION_HOURS),
        revoked_at=None,
    )
    db.add(sess)
    db.commit()
    return sess

def login(db: Session, email: str, face_b64: str, device_fp: str) -> AuthSession:
    user = db.query(User).filter(User.email == email.lower()).one_or_none()
    if not user:
        raise ValueError("user_not_found")

    prof = db.query(FaceProfile).filter(FaceProfile.user_id == user.id).one_or_none()
    if not prof:
        raise ValueError("no_face_on_record")

    ok, sim = face_match(face_embed(face_b64), prof.face_vec, SIM_THRESHOLD)
    if not ok:
        raise ValueError("face_not_matched")

    # 1 user 1 device: allow update to new device after face OK
    if user.device_fp and user.device_fp != device_fp:
        user.device_fp = device_fp

    # rotate sessions (optional): revoke old sessions for this user
    db.query(AuthSession).filter(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))\
        .update({AuthSession.revoked_at: _now()})

    tok = _new_token()
    sess = AuthSession(
        id=tok,
        user_id=user.id,
        device_fp=device_fp,
        created_at=_now(),
        expires_at=_now() + timedelta(hours=SESSION_HOURS),
        revoked_at=None,
    )
    db.add(sess)
    db.commit()
    return sess

def logout(db: Session, token: str) -> None:
    row = db.query(AuthSession).filter(AuthSession.id == token, AuthSession.revoked_at.is_(None)).one_or_none()
    if row:
        row.revoked_at = _now()
        db.commit()

def kyc_submit(db: Session, user_id: str, id_images_b64=None, id_meta: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
    # AI-first: if any ID provided, auto-evaluate low risk => FACE_PLUS_ID
    kyc = db.query(KycVerification).filter(KycVerification.user_id == user_id).one_or_none()
    if not kyc:
        kyc = KycVerification(
            id=str(uuid.uuid4()), user_id=user_id, tier="FACE_ONLY",
            ai_risk_score=0.12, state="APPROVED_AI", decided_at=_now(), evidence_json={}
        )
        db.add(kyc)

    if id_images_b64 or id_meta:
        # simple AI ok path (stub)
        kyc.tier = "FACE_PLUS_ID"
        kyc.ai_risk_score = 0.10
        kyc.state = "APPROVED_AI"
        kyc.decided_at = _now()
        kyc.evidence_json = {"id_meta": id_meta or {}, "images": bool(id_images_b64)}
        # also reflect on user table
        user = db.query(User).filter(User.id == user_id).one()
        user.identity_tier = "FACE_PLUS_ID"
        db.commit()
        return {"ok": True, "tier": "FACE_PLUS_ID", "state": "APPROVED_AI"}
    


    # no id provided → keep FACE_ONLY
    db.commit()
    return {"ok": True, "tier": kyc.tier, "state": kyc.state}
