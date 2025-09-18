from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
import speech_recognition as sr
from sqlalchemy import or_
import tempfile
import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

from db.session import get_db
from models import Movie
from config import settings

# Load environment variables
load_dotenv()

# Router setup
router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# --- OpenRouter client setup ---
OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def search_movies(query_text: str, db: Session):
    """
    Search movies in DB by title, genre, or tags using refined query.
    """
    keywords = [k.strip().lower() for k in query_text.split() if k.strip()]
    if not keywords:
        return []

    filters = []
    for word in keywords:
        filters.append(Movie.genre.ilike(f"%{word}%"))
        filters.append(Movie.tags.ilike(f"%{word}%"))
        filters.append(Movie.title.ilike(f"%{word}%"))

    return db.query(Movie).filter(or_(*filters)).limit(5).all()


def engage_conversation(user_text: str, db: Session):
    """
    Let the LLM engage in conversation, but also attach movies if found.
    """
    # Try finding related movies
    movies = search_movies(user_text, db)

    # Prepare context for LLM
    system_prompt = (
        "You are a friendly multilingual movie assistant. "
        "Engage in a natural conversation with the user in the SAME language they use. "
        "If you found matching movies from the database, weave them naturally into your reply. "
        "If no movie matches, just continue the conversation politely."
    )

    movie_context = ""
    if movies:
        movie_context = "Here are some movies I found: " + ", ".join(
            [f"{m.title} ({m.year}) - {m.genre}" for m in movies]
        )

    try:
        completion = client.chat.completions.create(
            model="tngtech/deepseek-r1t2-chimera:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": movie_context},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        reply = completion.choices[0].message.content.strip()
        return reply, movies

    except APIError as e:
        print(f"OpenRouter API error: {e}")
        return "I'm sorry, something went wrong with my brain today 😅.", movies


@router.post("/text")
def chatbot_text(message: str = Form(...), db: Session = Depends(get_db)):
    """
    Text chatbot: engage in conversation + recommend movies if relevant.
    """
    reply, movies = engage_conversation(message, db)

    return {
        "success": True,
        "reply": reply,
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "genre": m.genre,
                "year": m.year,
                "description": m.description,
                "cover": m.cover,
                "tags": [tag.strip() for tag in m.tags.split(",")] if m.tags else [],
            }
            for m in movies
        ],
    }


@router.post("/voice")
def chatbot_voice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Voice chatbot: upload audio, transcribe, engage in conversation + recommend movies if relevant.
    """
    recognizer = sr.Recognizer()

    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
            tmp.write(file.file.read())
            tmp.flush()
            with sr.AudioFile(tmp.name) as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio)  # Auto-detects language

    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    reply, movies = engage_conversation(text, db)

    return {
        "success": True,
        "reply": reply,
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "genre": m.genre,
                "year": m.year,
                "description": m.description,
                "cover": m.cover,
                "tags": [tag.strip() for tag in m.tags.split(",")] if m.tags else [],
            }
            for m in movies
        ],
    }
