from fastapi import FastAPI
from contextlib import asynccontextmanager
from api import auth, wallet, payments #not implemented authentication yet
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
