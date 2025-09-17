from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models import ShareCode
from api.auth import get_current_user
import datetime

router = APIRouter(prefix="/redeem", tags=["redeem"])

@router.post("/{code}")
def redeem_share(code: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Redeem a shared movie code → gives access to ONE movie for 24h.
    """
    share = db.query(ShareCode).filter(ShareCode.code == code).first()
    if not share:
        raise HTTPException(status_code=404, detail="Invalid code.")
    if share.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired.")
    if share.redeemed:
        raise HTTPException(status_code=400, detail="Code already redeemed.")

    # Mark as redeemed
    share.redeemed = True
    share.shared_with = current_user["id"]
    db.commit()
    db.refresh(share)

    return {
        "success": True,
        "message": "Movie unlocked for 24 hours!",
        "movie": {
            "id": share.movie.id,
            "title": share.movie.title,
            "cover": share.movie.cover,
            "description": share.movie.description,
        },
        "expires_at": share.expires_at,
    }
