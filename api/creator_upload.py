from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
import shutil
#import os
import uuid
from web3 import Web3
import hashlib
import subprocess
import imageio_ffmpeg as ffmpeg
from sqlalchemy.orm import Session
from db.session import get_db
from models import Movie, MovieFTS
import json
from sqlalchemy.orm import Session
import cv2
import os

from db.session import get_db
import models
from utils import hash_file
from config import settings
from .auth import get_current_user
from utils import hash_file

router = APIRouter(prefix="/content", tags=["Content"])

UPLOAD_DIR = "uploads"
THUMBNAIL_DIR = "thumbnails"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

FFMPEG_BIN = ffmpeg.get_ffmpeg_exe()
RPC_URL = settings.RPC_URL
CHAIN_ID = settings.CHAIN_ID
w3 = Web3(Web3.HTTPProvider(RPC_URL))


with open("contract_data.json") as f:
    contract_data = json.load(f)
upload_contract = w3.eth.contract(address=contract_data["address"], abi=contract_data["abi"])


# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

print("Upload dir:", UPLOAD_DIR)


def compress_video_multires(input_path: str, output_dir: str, file_id: str):
    """
    Generate HLS video with multiple resolutions (1080p, 720p, 480p)
    """
    master_playlist = os.path.join(output_dir, f"{file_id}_master.m3u8")

    command = [
        FFMPEG_BIN, "-i", input_path,
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


# def generate_thumbnail(video_path: str, thumbnail_path: str):
#     """
#     Generate thumbnail at 1s into the video
#     """
#     command = [
#         "ffmpeg",
#         "-i", video_path,
#         "-ss", "00:00:01",
#         "-vframes", "1",
#         thumbnail_path
#     ]
#     subprocess.run(command, check=True)


def generate_thumbnail(video_path, thumbnail_path):
    """
    Generates a thumbnail from a video file using OpenCV.
    """
    print(f"Generating thumbnail for {video_path}...")
    
    # Create a VideoCapture object to read the video file
    vidcap = cv2.VideoCapture(video_path)
    
    # Check if the video was opened successfully
    if not vidcap.isOpened():
        print("Error: Could not open video file.")
        return False
    
    # Set the frame position to capture a frame from the middle of the video
    frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle_frame_number = frame_count // 2
    
    # Set the video's current position to the desired frame
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_number)
    
    success, image = vidcap.read()
    
    if success:
        # Save the frame as a JPEG image
        cv2.imwrite(thumbnail_path, image)
        print(f"Thumbnail saved to {thumbnail_path}")
    else:
        print("Error: Could not read frame from video.")
        
    # Release the VideoCapture object
    vidcap.release()
    
    # return success

# @router.post("/upload-and-compress")
# async def upload_video(
#     title: str = Form(...),
#     description: str = Form(...),
#     genre: str = Form(...),
#     file: UploadFile = File(...)
# ):
#     try:
#         # Step 1: Save temp file
#         file_ext = os.path.splitext(file.filename)[1]
#         file_id = str(uuid.uuid4())
#         temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")

#         with open(temp_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         print("done with temp save")

#         # Step 2: Compress into multiple resolutions
#         print("starting compression")
#         output_dir = os.path.join(UPLOAD_DIR, file_id)
#         print("output dir:", output_dir)
#         os.makedirs(output_dir, exist_ok=True)
#         master_playlist = compress_video_multires(temp_path, output_dir, file_id)

#         print("done with compression")

#         # Step 3: Generate thumbnail
#         thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{file_id}.jpg")
#         generate_thumbnail(temp_path, thumbnail_path)

#         print("done with thumbnail")

#         # Step 4: Remove original file
#         os.remove(temp_path)

#         print("done with cleanup")

#         # Step 5: Return response (save to DB in real app)
#         return {
#             "success": True,
#             "message": "Video uploaded successfully",
#             "id": file_id,
#             "title": title,
#             "genre": genre,
#             "video_master_playlist": master_playlist,
#             "thumbnail": thumbnail_path
#         }

#     except Exception as e:
#         return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    

# @router.post("/upload")
# async def upload_video(
#     title: str = Form(...),
#     description: str = Form(...),
#     genre: str = Form(...),
#     file: UploadFile = File(...),
#     user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     try:
#         #step 1, save temp file
#         file_ext = os.path.splitext(file.filename)[1]
#         file_id = str(uuid.uuid4())
#         temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")

#         with open(temp_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         print("done with temp save")

#         print("starting compression")
#         output_dir = os.path.join(UPLOAD_DIR, file_id)
#         print("output dir:", output_dir)
#         os.makedirs(output_dir, exist_ok=True)
        
#         master_playlist = os.path.join(output_dir, f"{file_id}_master.m3u8")
#         # master_playlist = compress_video_multires(temp_path, output_dir, file_id)
        
#         print("done with extra stuff")

#         #step 2, generate thumbnail
#         thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{file_id}.jpg")
#         generate_thumbnail(temp_path, thumbnail_path)

#         print("done with thumbnail")


#         #step 3, attempt to hash and store it on blockchain
#         creator_private_key = user.private_key
#         creator_address = user.b_wallet_address

#         file_bytes = await file.read()
#         file_hash = hash_file(file_bytes)

#         creator = w3.eth.account.from_key(creator_private_key)

#         tx = upload_contract.functions.registerContent(file_hash).build_transaction({
#             "from": creator.address,
#             "nonce": w3.eth.get_transaction_count(creator.address),
#             "gas": 200000,
#             "gasPrice": w3.to_wei("2", "gwei"),
#             "chainId": CHAIN_ID,
#         })
#         signed_tx = w3.eth.account.sign_transaction(tx, creator_private_key)
#         tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
#         receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#         #step 4, remove original file
#         os.remove(temp_path)

#         print("done with cleanup")

#         #step 5, return response
#         new_content = models.Movie(
#             # id=file_id,
#             title=title,
#             description=description,
#             genre=genre,
#             url=master_playlist,
#             cover=thumbnail_path,
#         )
#         db.add(new_content)
#         db.commit()

#         return {
#             "success": True,
#             "message": "Video uploaded successfully",
#             # "id": file_id,
#             "title": title,
#             "genre": genre,
#             "video_master_playlist": master_playlist,
#             "thumbnail": thumbnail_path
#         }

#         #save to the db laterrr, do not forget

#     except Exception as e:
#         return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@router.post("/upload")
async def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    genre: str = Form(...),

    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        #hash the file first
        file_bytes = await file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        print("file hash:", file_hash)

        #move the file pointer back to the beginning so it can be read again
        await file.seek(0)
        print("file seek done")

        #check if the file hash already exists in the db
        existing = db.query(models.Movie).filter(models.Movie.hash == file_hash).first()
        if existing:
            return JSONResponse({"success": False, "message": "This content has already been uploaded"}, status_code=400)

        print("starting upload process...")
        # Step 1: Save the uploaded file
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
        print("file path:", file_path)


        with open(file_path, "wb") as buffer:
            print("writing to file...")
            shutil.copyfileobj(file.file, buffer)
            print("file write complete.")

        print("done with file save")

        # Step 2: Generate thumbnail
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{file_id}.jpg")
        generate_thumbnail(file_path, thumbnail_path)


        print("done with thumbnail")

        # Step 3: Hash and store on blockchain
        creator_private_key = user.private_key
        print("creator private key:", creator_private_key)
        creator_address = user.b_wallet_address
        print("creator address:", creator_address)

        # file_bytes = await file.read()
        # file_hash = hashlib.sha256(file_bytes).hexdigest()
        # print("file hash:", file_hash)

        creator = w3.eth.account.from_key(creator_private_key)
        # print("creator account:", creator.address)

        tx = upload_contract.functions.registerContent(file_hash).build_transaction({
            "from": creator.address,
            "nonce": w3.eth.get_transaction_count(creator.address),
            "gas": 200000,
            "gasPrice": w3.to_wei("35", "gwei"),
            "chainId": CHAIN_ID,
        })
        print("built transaction:", tx)

        signed_tx = w3.eth.account.sign_transaction(tx, creator_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print("done with blockchain registration")

        # Step 4: Save to database
        new_content = models.Movie(
            title=title,
            description=description,
            genre=genre,
            url=file_path,  #store the path to the original file
            hash=file_hash,
            cover=thumbnail_path,
        )
        db.add(new_content)
        db.commit()

        # Step 5: Return response
        return {
            "success": True,
            "message": "Aiit, your content is now in the stream",
            "title": title,
            "genre": genre,
            "video_path": FileResponse(file_path, media_type="video/mp4"),  #return the path to the original file
            "thumbnail": thumbnail_path
        }

    except subprocess.CalledProcessError as e:
        return JSONResponse(
            {"success": False, "message": f"FFmpeg failed: {e}"},
            status_code=500
        )
    except Exception as e:

        # Clean up the file in case of failure
        if os.path.exists(file_path):
            os.remove(file_path)
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
