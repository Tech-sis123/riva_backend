from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from decimal import Decimal
from db.session import SessionLocal
from services import wallet_service
from utils import security
from scopes import user_scopes, wallet_scopes, transaction_scopes
import models

router = APIRouter(prefix="/wallet", tags=["wallet"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth")
    token = authorization.split(" ")[1]
    payload = security.decode_access_token(token)
    user_id = int(payload["sub"])
    user = user_scopes.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/", response_model=dict)
def get_my_wallet(user = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = wallet_service.get_wallet(db, user.id)
    if not wallet:
        return {"success": False, "balance": 0.00, "currency": "No wallet found", "havePaidToday": False}
        # raise HTTPException(status_code=404, detail="Wallet not found")
    
    #check if user has made a 'pay' transaction withing the last 24 hours
    have_paid_today = transaction_scopes.user_has_paid_today(db, wallet.id)

    if have_paid_today:
        return {"success": True, "balance": str(wallet.balance), "currency": wallet.currency, "havePaidToday": True}

    else:
        return {"success": True, "balance": str(wallet.balance), "currency": wallet.currency, "havePaidToday": False}

@router.post("/transfer")
def transfer(destination_email: str, amount: Decimal, user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        wallet_service.transfer(db, from_user_id=user.id, to_email=destination_email, amount=amount)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pay-for-today")
def transfer(destination_email: str, amount: Decimal, user = Depends(get_current_user), db: Session = Depends(get_db)):
    #check if user has paid today
    wallet = wallet_service.get_wallet(db, user.id)
    if not wallet:
        return {"success": False, "message": "No wallet found", "havePaidToday": False}
        # raise HTTPException(status_code=404, detail="Wallet not found")
    have_paid_today = transaction_scopes.user_has_paid_today(db, wallet.id)
    if have_paid_today:
        return {"success": False, "message": "You have already paid for today", "havePaidToday": True}

    try:
        #check if the available balance is sufficient
        if wallet.balance < amount:
            return {"success": False, "message": "Insufficient funds", "havePaidToday": False}
        else:
            #decrement 200 from balance an create tx record
            wallet = wallet_service.get_wallet(db, user.id).with_for_update()
            wallet.balance = wallet.balance - amount
            db.add(wallet)

            #create tx record
            transaction_scopes.create_transaction(db, wallet_id=wallet.id, t_type="pay", amount=amount, status="success")
            db.commit()
            return {"success": True, "message": "Payment successful", "havePaidToday": True}

    except ValueError as e:
        return {"success": False, "message": "Oh no, something went wrong...", "havePaidToday": False}
    

