from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models import Movie
from api.auth import get_current_user  # <-- your JWT dependency

router = APIRouter(prefix="/movies", tags=["movies"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{movie_id}/stream")
def stream_movie(
    movie_id: int,
    resolution: str = "720p",  # default resolution
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch the compressed video file URL for streaming.
    Resolutions: 480p, 720p, 1080p
    """
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Construct video path based on resolution
    if resolution not in ["480p", "720p", "1080p"]:
        raise HTTPException(status_code=400, detail="Invalid resolution")

    video_url = f"{movie.url.replace('.mp4', '')}_{resolution}.mp4"

    return {
        "success": True,
        "id": movie.id,
        "title": movie.title,
        "description": movie.description,
        "genre": movie.genre,
        "type": movie.type,
        "requested_resolution": resolution,
        "video_url": video_url
    }
