from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie, UserPreference, User
from api.auth import get_current_user

router = APIRouter(prefix="/movies", tags=["content"])

def movie_to_dict(movie, user):
    return {
        "id": movie.id,
        "title": movie.title,
        "genre": movie.genre,
        "year": movie.year,
        "tags": movie.tags.split(",") if movie.tags else [],
        "description": movie.description,
        "cover": movie.cover,
        "haveIAddedToList": movie.id in (user.my_list if hasattr(user, "my_list") else []),
    }

@router.get("/list")
def get_list(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    #Get user preferences (from onboarding)
    prefs = db.query(UserPreference).filter_by(user_id=user.id).first()
    preferred_genres = prefs.genres.split(",") if prefs and prefs.genres else []
    preferred_types = prefs.types.split(",") if prefs and prefs.types else []

    #Recommended movies (match user genres)
    recommended = (
        db.query(Movie)
        .filter(Movie.genre.in_(preferred_genres))
        .limit(5)
        .all()
    )

    #Suggestions grouped by genre
    suggestions = {}
    for genre in preferred_genres:
        movies = (
            db.query(Movie)
            .filter(Movie.genre == genre)
            .limit(3)
            .all()
        )
        suggestions[genre] = [movie_to_dict(m, user) for m in movies]

    return {
        "success": True,
        "recommended": [movie_to_dict(m, user) for m in recommended],
        "suggestions": suggestions
    }
