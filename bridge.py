from fastapi import FastAPI
from contextlib import asynccontextmanager
from api import auth, wallet, payments,share_movie, redeem, creator_upload, movie_list, onboarding, stream_movie, search, ai_rec#not implemented authentication yet
from db.session import engine, Base
import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print(" Database tables created")

    yield

    print("Terminaing backend...")

app = FastAPI(title="Riva-Backend", lifespan=lifespan)

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

