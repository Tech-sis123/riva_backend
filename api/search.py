# routers/search.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def search_movies(query: str, db: Session = Depends(get_db)):
    """
    Search movies by title, genre, or tags.
    """
    results = db.query(Movie).filter(
        (Movie.title.ilike(f"%{query}%")) |
        (Movie.genre.ilike(f"%{query}%")) |
        (Movie.tags.ilike(f"%{query}%"))
    ).all()

    return {
        "success": True,
        "results": [
            {
                "id": m.id,
                "title": m.title,
                "genre": m.genre,
                "description": m.description,
                "cover": m.cover,
                "tags": m.tags.split(",") if m.tags else []
            } for m in results
        ]
    }
