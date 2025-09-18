from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
import whisper
import srt
import tempfile
import os
import datetime
import argostranslate.translate

router = APIRouter(prefix="/subtitles", tags=["subtitles"])

# Load Whisper once
whisper_model = whisper.load_model("tiny")  # options: tiny, base, small, medium, large

@router.post("/generate")
def generate_and_translate_subtitles(
    file: UploadFile = File(...),
    target_lang: str = Form("fra")  # default = French
):
    """
    Generate subtitles (SRT) from MP4 and translate them into another language (offline).
    Returns both original and translated .srt files as downloads.
    """

    # Save uploaded MP4 temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    # --- Step 1: Transcribe with Whisper ---
    result = whisper_model.transcribe(tmp_path)
    os.remove(tmp_path)  # cleanup

    # Build SRT
    subtitles = []
    for i, segment in enumerate(result["segments"]):
        start = datetime.timedelta(seconds=segment["start"])
        end = datetime.timedelta(seconds=segment["end"])
        subtitles.append(
            srt.Subtitle(index=i+1, start=start, end=end, content=segment["text"])
        )
    srt_text = srt.compose(subtitles)

    # Save original SRT
    original_srt_path = tempfile.NamedTemporaryFile(delete=False, suffix=".en.srt").name
    with open(original_srt_path, "w", encoding="utf-8") as f:
        f.write(srt_text)

    # --- Step 2: Translate with Argos Translate ---
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
    to_lang = next((lang for lang in installed_languages if lang.code == target_lang), None)

    if from_lang == to_lang:
        return {
            "success": True,
            "message": "No translation needed, source and target are the same.",
            "original_srt": original_srt_path,
            "translated_srt": original_srt_path
        }


    if not from_lang or not to_lang:
        return {
            "success": False,
            "message": f"Translation from 'en' to '{target_lang}' not installed. Install with argos-translate-cli."
        }

    translator = from_lang.get_translation(to_lang)
    translated_subtitles = []
    for sub in subtitles:
        translated_text = translator.translate(sub.content)
        translated_subtitles.append(
            srt.Subtitle(index=sub.index, start=sub.start, end=sub.end, content=translated_text)
        )
    translated_srt = srt.compose(translated_subtitles)

    # Save translated SRT
    translated_srt_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{target_lang}.srt").name
    with open(translated_srt_path, "w", encoding="utf-8") as f:
        f.write(translated_srt)

    # Return both files as downloadable links
    return {
        "success": True,
        "message": "Subtitles generated and translated successfully.",
        "original_subtitles": f"/subtitles/download?path={original_srt_path}",
        "translated_subtitles": f"/subtitles/download?path={translated_srt_path}"
    }

@router.get("/download")
def download_subtitles(path: str):
    """Download subtitle file"""
    return FileResponse(path, filename=os.path.basename(path), media_type="text/plain")
