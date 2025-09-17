from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie, UserPreference, User, UserList
from api.auth import get_current_user

router = APIRouter(prefix="/movies", tags=["content"])

def movie_to_dict(movie, user_movie_ids):
    return {
        "id": movie.id,
        "title": movie.title,
        "genre": movie.genre,
        "year": movie.year,
        "tags": movie.tags.split(",") if movie.tags else [],
        "description": movie.description,
        "cover": movie.cover,
        "haveIAddedToList": movie.id in user_movie_ids,
    }

@router.get("/list")
def get_list(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Correctly fetch the user's list from the database
    user_list_entries = db.query(UserList).filter(UserList.user_id == user.id).all()
    user_movie_ids = {entry.movie_id for entry in user_list_entries}

    # Get user preferences (from onboarding)
    prefs = db.query(UserPreference).filter_by(user_id=user.id).first()
    preferred_genres = prefs.genres.split(",") if prefs and prefs.genres else []

    # Recommended movies (match user genres)
    recommended = (
        db.query(Movie)
        .filter(Movie.genre.in_(preferred_genres))
        .limit(5)
        .all()
    )

    # Suggestions grouped by genre
    suggestions = {}
    for genre in preferred_genres:
        movies = (
            db.query(Movie)
            .filter(Movie.genre == genre)
            .limit(3)
            .all()
        )
        suggestions[genre] = [movie_to_dict(m, user_movie_ids) for m in movies]

    return {
        "success": True,
        "recommended": [movie_to_dict(m, user_movie_ids) for m in recommended],
        "suggestions": suggestions
    }