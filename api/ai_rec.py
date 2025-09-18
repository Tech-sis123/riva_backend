from fastapi import APIRouter, UploadFile, File
import openai
import tempfile
import speech_recognition as sr

router = APIRouter(prefix="/chat", tags=["chat"])

# ---- Core Chat Logic ----
def handle_chat(query: str):
    """
    Handles both normal conversation and African movie recommendations.
    Uses the LLM only (no DB).
    """
    response = openai.ChatCompletion.create(
        model="tngtech/deepseek-r1t2-chimera:free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a conversational assistant. "
                    "If the user asks about movies or recommendations, "
                    "suggest African movies (e.g. Nollywood, Ghallywood, South African cinema). "
                    "If the user does not mention movies, just reply normally. "
                    "Always respond in the same language the user used."
                )
            },
            {"role": "user", "content": query}
        ],
        max_tokens=400,
        temperature=0.7
    )
    reply = response.choices[0].message["content"]

    return {
        "success": True,
        "reply": reply
    }


# ---- Text Chat Endpoint ----
@router.post("/")
def chat(query: str):
    return handle_chat(query)


# ---- Voice Chat Endpoint ----
@router.post("/voice")
async def chat_voice(file: UploadFile = File(...)):
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
        return {"success": False, "reply": "Sorry, I couldn’t understand the audio."}
    except sr.RequestError as e:
        return {"success": False, "reply": f"Speech Recognition error: {e}"}

    # Handle as normal chat
    return handle_chat(query)
