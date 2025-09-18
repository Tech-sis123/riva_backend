from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie, UserPreference, User
from api.auth import get_current_user

router = APIRouter(prefix="/movies", tags=["content"])

# -------------------- Helpers -------------------- #
def parse_tags(tags: str | None):
    return [t.strip() for t in tags.split(",")] if tags else []

def movie_to_dict(movie: Movie, user: User):
    user_list = getattr(user, "my_list", [])
    if isinstance(user_list, str):
        user_list = [int(x) for x in user_list.split(",") if x]

    return {
        "id": movie.id,
        "title": movie.title,
        "genre": movie.genre,
        "year": movie.year,
        "tags": parse_tags(movie.tags),
        "description": movie.description,
        "cover": movie.cover,
        "haveIAddedToList": movie.id in user_list,
    }

# -------------------- Routes -------------------- #
@router.get("/list")
def get_list(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Get user preferences
    prefs = db.query(UserPreference).filter_by(user_id=user.id).first()
    preferred_genres = prefs.genres.split(",") if prefs and prefs.genres else []

    # Recommended movies
    recommended_query = db.query(Movie)
    if preferred_genres:
        recommended_query = recommended_query.filter(Movie.genre.in_(preferred_genres))
    recommended = recommended_query.limit(5).all()

    # Suggestions grouped by genre
    suggestions = {}
    for genre in preferred_genres:
        movies = db.query(Movie).filter(Movie.genre == genre).limit(3).all()
        suggestions[genre] = [movie_to_dict(m, user) for m in movies]

    return {
        "success": True,
        "recommended": [movie_to_dict(m, user) for m in recommended],
        "suggestions": suggestions
    }
