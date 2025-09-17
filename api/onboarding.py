from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models import UserPreference, User
from api.auth import get_current_user

router = APIRouter(prefix="/api/v1/user", tags=["user"])

# 🟢 Save or update preferences (from onboarding)
@router.post("/preferences")
def save_preferences(preferences: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(UserPreference).filter_by(user_id=user.id).first()

    genres = ",".join(preferences.get("genres", []))
    types = ",".join(preferences.get("types", []))

    if existing:
        existing.genres = genres
        existing.types = types
    else:
        pref = UserPreference(user_id=user.id, genres=genres, types=types)
        db.add(pref)

    db.commit()

    return {"success": True, "message": "Preferences saved"}

# 🟡 Fetch preferences
@router.get("/preferences")
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prefs = db.query(UserPreference).filter_by(user_id=user.id).first()

    if not prefs:
        return {"success": True, "genres": [], "types": []}

    return {
        "success": True,
        "genres": prefs.genres.split(",") if prefs.genres else [],
        "types": prefs.types.split(",") if prefs.types else []
    }
