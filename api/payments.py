from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from decimal import Decimal

from db.session import SessionLocal
from services import payment_service
import json

router = APIRouter(prefix="/payments", tags=["payments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/fund")
def fund_wallet(email: str, amount: float, db: Session = Depends(get_db)):
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