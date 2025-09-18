import requests, hmac, hashlib, json
from sqlalchemy.orm import Session
from decimal import Decimal
from config import settings
from scopes import user_scopes, wallet_scopes, transaction_scopes
import models

PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"

def initialize_paystack_payment(db: Session, email: str, amount_decimal: Decimal):
    payload = {
        "email": email,
        "amount": int(amount_decimal * 100),
        "callback_url": settings.PAYSTACK_CALLBACK_URL or "https://hello.pstk.xyz/callback",
        "metadata": {"cancel_action": "https://your-cancel-url.com"},
        "metadata": {"cancel_action": settings.PAYSTACK_CANCEL_URL or "https://your-cancel-url.com"} 
    }
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }
    resp = requests.post(PAYSTACK_INIT_URL, json=payload, headers=headers, timeout=10)
    data = resp.json()
    print("Paystack init response:", data)
    #create a pending transaction record (if Paystack returns reference)
    if data.get("status") and data["data"].get("reference"):
        #find user wallet
        user = user_scopes.get_user_by_email(db, email)
        if user:
            wallet = wallet_scopes.get_wallet_by_user_id(db, user.id)
            transaction_scopes.create_transaction(db, wallet_id=wallet.id, t_type="fund", amount=amount_decimal, status="pending", reference=data["data"]["reference"])
            db.commit()
    # return data
    if data.get("status") == True:
        return {"success": True, "authorization_url": data["data"]["authorization_url"], "access_code": data["data"]["access_code"], "reference": data["data"]["reference"]}
    else:
        return {"success": False, "message": data.get("message", "Failed to initialize payment")}


def verify_paystack_webhook(raw_body: bytes, signature_header: str) -> bool:
    secret = settings.PAYSTACK_WEBHOOK_SECRET or settings.PAYSTACK_SECRET
    computed = hmac.new(secret.encode(), msg=raw_body, digestmod=hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature_header)

def handle_paystack_event(db: Session, payload: dict):
    event = payload.get("event")
    if event != "charge.success":
        return {"skipped": True}
    ref = payload["data"]["reference"]
    amount_kobo = payload["data"]["amount"]
    amount = Decimal(amount_kobo) / Decimal(100)
    tx = transaction_scopes.get_by_reference(db, ref)
    if not tx:
        #if we didn't previously create the pending tx, create one and mark success
        #try to find wallet by customer email
        customer = payload["data"].get("customer", {})
        email = customer.get("email")
        user = user_scopes.get_user_by_email(db, email) if email else None
        if not user:
            return {"error": "user not found"}
        wallet = wallet_scopes.get_wallet_by_user_id(db, user.id)
        with db.begin():
            transaction_scopes.create_transaction(db, wallet_id=wallet.id, t_type="deposit", amount=amount, status="success", reference=ref)
            # update balance
            wallet_db = db.query(models.Wallet).filter(models.Wallet.id == wallet.id).with_for_update().one()
            wallet_db.balance = wallet_db.balance + amount
            db.add(wallet_db)
        return {"created": True}
    else:
        #idempotency if already success, do nothing
        if tx.status == "success":
            return {"ok": "already processed"}
        #otherwise, mark success and update balance
        with db.begin():
            tx.status = "success"
            db.add(tx)
            wallet_db = db.query(models.Wallet).filter(models.Wallet.id == tx.wallet_id).with_for_update().one()
            wallet_db.balance = wallet_db.balance + amount
            db.add(wallet_db)
        return {"ok": True}
