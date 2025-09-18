from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import openai
import tempfile
import speech_recognition as sr

from db.session import get_db
from models import Movie

router = APIRouter(prefix="/chat", tags=["chat"])


# ---- Intent Classifier ----
def detect_movie_intent(query: str) -> bool:
    """
    Uses LLM to classify if a query is about movie recommendations.
    Returns True if it's a movie request, otherwise False.
    """
    response = openai.ChatCompletion.create(
        model="tngtech/deepseek-r1t2-chimera:free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intent classifier. "
                    "Reply with only 'true' if the user is asking about movie recommendations "
                    "or movies in general. Otherwise reply with 'false'."
                )
            },
            {"role": "user", "content": query}
        ],
        max_tokens=5,
        temperature=0.0
    )

    intent = response.choices[0].message["content"].strip().lower()
    return intent == "true"


# ---- Handle Chat (Core Logic) ----
def handle_chat(query: str, db: Session):
    is_movie_query = detect_movie_intent(query)

    if is_movie_query:
        # Query DB for matching movies
        movies = db.query(Movie).filter(Movie.title.ilike(f"%{query}%")).all()
        if movies:
            return {
                "success": True,
                "reply": f"I found {len(movies)} movies related to '{query}'.",
                "movies": [m.to_dict() for m in movies],
            }
        else:
            return {
                "success": True,
                "reply": f"Sorry, I couldn’t find any movies for of your choice, let's discuss something else\n.",
                "movies": []
            }

    # If not about movies → normal multilingual conversation
    response = openai.ChatCompletion.create(
        model="tngtech/deepseek-r1t2-chimera:free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful conversational assistant. "
                    "Always reply in the same language the user used."
                )
            },
            {"role": "user", "content": query}
        ],
        max_tokens=300,
        temperature=0.7
    )
    reply = response.choices[0].message["content"]

    return {
        "success": True,
        "reply": reply,
        "movies": None
    }


# ---- Text Endpoint ----
@router.post("/")
def chat(query: str, db: Session = Depends(get_db)):
    return handle_chat(query, db)


# ---- Voice Endpoint ----
@router.post("/voice")
async def chat_voice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded audio temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Use SpeechRecognition for transcription
    recognizer = sr.Recognizer()
    with sr.AudioFile(tmp_path) as source:
        audio = recognizer.record(source)

    try:
        query = recognizer.recognize_google(audio)  # Uses Google Speech API
    except sr.UnknownValueError:
        return {"success": False, "reply": "Sorry, I couldn’t understand the audio.", "movies": None}
    except sr.RequestError as e:
        return {"success": False, "reply": f"Speech Recognition error: {e}", "movies": None}

    # Handle as normal chat
    return handle_chat(query, db)
