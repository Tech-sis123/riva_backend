from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie
import speech_recognition as sr
from sqlalchemy import or_
import tempfile
import os
from openai import OpenAI
from openai import OpenAI, APIError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Router setup
router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# --- OpenRouter client setup ---
# Ensure OPENROUTER_API_KEY is set in your environment variables or a .env file
# using `pip install python-dotenv`
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def refine_query_with_llm(user_text: str) -> str:
    """
    Use OpenRouter to refine user text into concise search keywords.
    Example: "I want a funny sci-fi movie with space travel"
    → "sci-fi, comedy, space travel"
    """
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",  # Using a specific model via OpenRouter
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a movie assistant. Extract concise keywords "
                        "for searching a movie database. Return ONLY the keywords, "
                        "comma-separated. No extra text."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            max_tokens=50,
            temperature=0.3,
        )

        refined = completion.choices[0].message.content.strip()
        return refined

    except APIError as e:
        print(f"OpenRouter API error: {e}")
        # Fallback to returning the original text or a default
        return user_text

def search_movies(query_text: str, db: Session):
    """
    Search movies in DB by title, genre, or tags using refined query.
    Performs a single, efficient query.
    """
    keywords = [k.strip().lower() for k in query_text.split(",") if k.strip()]
    if not keywords:
        return []

    # Use a list of OR conditions for the query
    filters = []
    for word in keywords:
        filters.append(Movie.genre.ilike(f"%{word}%"))
        filters.append(Movie.tags.ilike(f"%{word}%"))
        filters.append(Movie.title.ilike(f"%{word}%"))

    return db.query(Movie).filter(or_(*filters)).limit(10).all()


@router.post("/text")
def chatbot_text(message: str = Form(...), db: Session = Depends(get_db)):
    """
    Text chatbot: refine query with LLM, return matching movies.
    """
    refined = refine_query_with_llm(message)
    movies = search_movies(refined, db)

    if not movies:
        return {
            "success": True,
            "reply": f"Sorry, I couldn’t find any movies for '{refined}'.",
            "movies": [],
        }

    return {
        "success": True,
        "reply": f"Here are movies you can watch based on '{refined}':",
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
    Voice chatbot: upload audio, transcribe, refine with LLM, return movies.
    """
    recognizer = sr.Recognizer()

    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
            tmp.write(file.file.read())
            tmp.flush()
            with sr.AudioFile(tmp.name) as source:
                audio = recognizer.record(source)
            
            # Using Google Web Speech API for transcription
            text = recognizer.recognize_google(audio)

    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    refined = refine_query_with_llm(text)
    movies = search_movies(refined, db)

    if not movies:
        return {
            "success": True,
            "reply": f"Sorry, I couldn’t find any movies for '{refined}'.",
            "movies": [],
        }

    return {
        "success": True,
        "reply": f"Here are movies you can watch based on '{refined}':",
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