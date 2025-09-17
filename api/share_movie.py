from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models import ShareCode
from api.auth import get_current_user
import datetime, uuid

router = APIRouter(prefix="/share", tags=["share"])

@router.post("/{movie_id}")
def share_movie(movie_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Paid user can share ONE movie per day → generates a share code.
    """

    # Check if user has paid today (replace with your actual logic)
    if not current_user.get("have_paid_today", False):
        raise HTTPException(status_code=403, detail="You must pay daily access before sharing.")

    # Ensure they haven’t already shared today
    existing = db.query(ShareCode).filter(
        ShareCode.shared_by == current_user["id"],
        ShareCode.expires_at >= datetime.datetime.utcnow(),
    ).first()
    if existing:
        raise HTTPException(status_code=403, detail="You can only share one video per day.")

    # Generate short code
    code = str(uuid.uuid4())[:8]

    share = ShareCode(
        code=code,
        movie_id=movie_id,
        shared_by=current_user["id"],
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    return {
        "success": True,
        "share_code": share.code,
        "expires_at": share.expires_at,
    }
