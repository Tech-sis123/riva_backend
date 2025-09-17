from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
import subprocess

# Router instance
router = APIRouter(prefix="/api/v1/content", tags=["Content"])

UPLOAD_DIR = "uploads/"
THUMBNAIL_DIR = "thumbnails/"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def compress_video_multires(input_path: str, output_dir: str, file_id: str):
    """
    Generate HLS video with multiple resolutions (1080p, 720p, 480p)
    """
    master_playlist = os.path.join(output_dir, f"{file_id}_master.m3u8")

    command = [
        "ffmpeg", "-i", input_path,
        # 1080p
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v:0", "libx265", "-b:v:0", "5000k", "-s:v:0", "1920x1080",
        "-c:a:0", "aac", "-b:a:0", "128k",

        # 720p
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v:1", "libx265", "-b:v:1", "2800k", "-s:v:1", "1280x720",
        "-c:a:1", "aac", "-b:a:1", "128k",

        # 480p
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v:2", "libx265", "-b:v:2", "1200k", "-s:v:2", "854x480",
        "-c:a:2", "aac", "-b:a:2", "96k",

        # HLS options
        "-f", "hls",
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2",
        "-master_pl_name", f"{file_id}_master.m3u8",
        os.path.join(output_dir, f"{file_id}_%v.m3u8")
    ]

    subprocess.run(command, check=True)
    return master_playlist


def generate_thumbnail(video_path: str, thumbnail_path: str):
    """
    Generate thumbnail at 1s into the video
    """
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ss", "00:00:01",
        "-vframes", "1",
        thumbnail_path
    ]
    subprocess.run(command, check=True)


@router.post("/upload")
async def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    genre: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Step 1: Save temp file
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Step 2: Compress into multiple resolutions
        output_dir = os.path.join(UPLOAD_DIR, file_id)
        os.makedirs(output_dir, exist_ok=True)
        master_playlist = compress_video_multires(temp_path, output_dir, file_id)

        # Step 3: Generate thumbnail
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{file_id}.jpg")
        generate_thumbnail(temp_path, thumbnail_path)

        # Step 4: Remove original file
        os.remove(temp_path)

        # Step 5: Return response (save to DB in real app)
        return {
            "success": True,
            "message": "Video uploaded successfully",
            "id": file_id,
            "title": title,
            "genre": genre,
            "video_master_playlist": master_playlist,
            "thumbnail": thumbnail_path
        }

    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
