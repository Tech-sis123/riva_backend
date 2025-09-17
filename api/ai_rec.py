from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie
import speech_recognition as sr
import tempfile

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


def search_movies(query_text: str, db: Session):
    """
    Search movies in DB by title, genre, or tags.
    Returns a list of matching movies.
    """
    keywords = query_text.lower().split()
    query = db.query(Movie)

    for word in keywords:
        query = query.filter(
            Movie.genre.ilike(f"%{word}%")
            | Movie.tags.ilike(f"%{word}%")
            | Movie.title.ilike(f"%{word}%")
        )

    return query.limit(10).all()


@router.post("/text")
def chatbot_text(message: str, db: Session = Depends(get_db)):
    """
    Text chatbot: returns list of movies matching user query.
    """
    movies = search_movies(message, db)

    if not movies:
        return {
            "success": True,
            "reply": f"Sorry, I couldn’t find any movies for '{message}'.",
            "movies": []
        }

    return {
        "success": True,
        "reply": f"Here are movies you can watch based on '{message}':",
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "genre": m.genre,
                "year": m.year,
                "description": m.description,
                "cover": m.cover,
                "tags": m.tags.split(",") if m.tags else [],
            }
            for m in movies
        ],
    }


@router.post("/voice")
def chatbot_voice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Voice chatbot: upload audio, transcribe, return list of matching movies.
    """
    recognizer = sr.Recognizer()

    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        with sr.AudioFile(tmp.name) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                raise HTTPException(status_code=400, detail="Could not understand audio")

    movies = search_movies(text, db)

    if not movies:
        return {
            "success": True,
            "reply": f"Sorry, I couldn’t find any movies for '{text}'.",
            "movies": []
        }

    return {
        "success": True,
        "reply": f"Here are movies you can watch based on '{text}':",
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "genre": m.genre,
                "year": m.year,
                "description": m.description,
                "cover": m.cover,
                "tags": m.tags.split(",") if m.tags else [],
            }
            for m in movies
        ],
    }
