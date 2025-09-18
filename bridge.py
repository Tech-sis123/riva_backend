from fastapi import FastAPI
from contextlib import asynccontextmanager
from api import auth, wallet, payments, share_movie, redeem, creator_upload,subtitle, movie_list, onboarding, stream_movie, search, ai_rec
from db.session import engine, Base, get_db
import models
from models import create_and_populate_fts_table

# The lifespan context manager should contain all startup logic.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Step 1: Create all standard database tables for your models.
    Base.metadata.create_all(bind=engine)
    print("Database tables created")

    # Step 2: Get a database session and create the special FTS table.
    db = next(get_db())
    try:
        create_and_populate_fts_table(db)
    finally:
        db.close()
    
    # The 'yield' signals that the startup process is complete.
    yield

    # This part runs when the application is shutting down.
    print("Terminating backend...")


app = FastAPI(title="Riva-Backend", lifespan=lifespan)

# Routers should be included after the main app is defined.
app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(payments.router)
app.include_router(creator_upload.router)
app.include_router(movie_list.router)
app.include_router(onboarding.router)
app.include_router(stream_movie.router)
app.include_router(search.router)
app.include_router(ai_rec.router)
app.include_router(share_movie.router)
app.include_router(redeem.router)
app.include_router(subtitle.router)