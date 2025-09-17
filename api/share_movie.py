from fastapi import APIRouter, Depends, HTTPException
import datetime, uuid
from sqlalchemy.orm import Session

from services import wallet_service
from db.session import get_db
from models import ShareCode
from api.auth import get_current_user
from scopes import transaction_scopes

router = APIRouter(prefix="/share", tags=["share"])

@router.post("/{movie_id}")
def share_movie(movie_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Paid user can share ONE movie per day → generates a share code.
    """

    # Check if user has paid today
    wallet = wallet_service.get_wallet(db, current_user.id)
    if not wallet:
        return {"success": False, "message": "No wallet found."}

    
    have_paid_today = transaction_scopes.user_has_paid_today(db, wallet.id)
    if not have_paid_today:
        return {"success": False, "message": "You must pay daily access before sharing."}

    #ensure they haven’t already shared today
    existing = db.query(ShareCode).filter(
        ShareCode.shared_by == current_user["id"],
        ShareCode.expires_at >= datetime.datetime.now(datetime.timezone.utc),
    ).first()
    if existing:
        raise HTTPException(status_code=403, detail="You can only share one video per day.")

    # Generate short code
    code = str(uuid.uuid4())[:8]

    share = ShareCode(
        code=code,
        movie_id=movie_id,
        shared_by=current_user["id"],
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    return {
        "success": True,
        "share_code": share.code,
        "expires_at": share.expires_at,
    }
