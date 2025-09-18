from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
import json

from db.session import SessionLocal
from services import payment_service
from utils import security
from scopes import user_scopes
from .auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def get_current_user(db: Session = Depends(get_db), authorization: str | None = Header(None)):
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Missing auth")
#     token = authorization.split(" ")[1]
#     payload = security.decode_access_token(token)
#     user_id = int(payload["sub"])
#     user = user_scopes.get_user_by_id(db, user_id)
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")
#     return user

@router.post("/fund")
def fund_wallet(amount: float, db: Session = Depends(get_db), user = Depends(get_current_user)):
    #get user email from user dependency
    email = user.email
    
    #amount is in NGN as decimal float so convert to Decimal in service
    return payment_service.initialize_paystack_payment(db, email, Decimal(str(amount)))

@router.post("/webhook")
async def webhook(request: Request, x_paystack_signature: str | None = Header(None), db: Session = Depends(get_db)):
    raw_body = await request.body()
    #verify signature
    if not payment_service.verify_paystack_webhook(raw_body, x_paystack_signature or ""):
        raise HTTPException(status_code=400, detail="Invalid signature")
    payload = await request.json()
    result = payment_service.handle_paystack_event(db, payload)
    return {"status": "received", "result": result}