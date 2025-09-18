from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

from scopes import wallet_scopes
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from db.session import SessionLocal
import models
from scopes.transaction_scopes import user_has_paid_today
from services.wallet_service import get_wallet
import schemas
from config import settings
from utils.create_b_wallet import create_b_wallet



router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # replace with your actual login path

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password context: argon2 for new users, bcrypt for old users
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)

security = HTTPBearer()


# -------------------- Utilities -------------------- #

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def get_current_user(db: Session = Depends(get_db), token:  str = Depends(oauth2_scheme)):
    print("AUTH HEADER:", token)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    # token = authorization.split(" ")[1] if " " in authorization else authorization
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        print(f"JWTError: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# -------------------- Routes -------------------- #

@router.post("/signup", response_model=dict)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": "Email already registered"}
        )
    
    #get a new blockchain wallet for the user
    wallet_address, private_key = create_b_wallet()
    print("New wallet created:", wallet_address)

    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        b_wallet_address=wallet_address,
        private_key=private_key,
        email=user.email,
        password_hash=hash_password(user.password),  # hashed with argon2
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_wallet = models.Wallet(
        user_id=db_user.id, 
        balance=0.00,
        currency="NGN"
    )
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)

    token = create_access_token({"sub": str(db_user.id)})
    return {
        "success": True,
        "token": token,
        "user": {
            "id": db_user.id,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "email": db_user.email,
            "role": db_user.role,
        },
    }


@router.post("/login", response_model=dict)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if not db_user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid email or password"}
        )
    
    try:
        password_valid = verify_password(user.password, db_user.password_hash)
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid email or password"}
        )
    
    if not password_valid:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid email or password"}
        )
# @router.post("/login", response_model=dict)
# def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
#     db_user = db.query(models.User).filter(models.User.email == user.email).first()
#     if not db_user or not verify_password(user.password, db_user.password_hash):
#         return JSONResponse(
#             status_code=401,
#             content = {"success": False, "message":"Invalid email or password"}
#         )

#     token = create_access_token({"sub": str(db_user.id)})
#     return {
#         "success": True,
#         "token": token,
#         "user": {
#             "id": db_user.id,
#             "first_name": db_user.first_name,
#             "last_name": db_user.last_name,
#             "email": db_user.email,
#             "role": db_user.role,
#         },
#     }



    # Auto-upgrade old bcrypt hashes to argon2
    if pwd_context.needs_update(db_user.password_hash):
        db_user.password_hash = hash_password(user.password)
        db.commit()
    
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}
    # return {
    #     "success": True,
    #     "token": token,
    #     "user": {
    #         "id": db_user.id,
    #         "first_name": db_user.first_name,
    #         "last_name": db_user.last_name,
    #         "email": db_user.email,
    #         "role": db_user.role,
    #     },
    # }




@router.get("/me", response_model=dict)
def read_users_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    wallet_id = wallet_scopes.get_wallet_by_user_id(db, current_user.id)
    paid = user_has_paid_today(db, wallet_id)

    return {
        "success": True,
        "user": {
            "id":current_user.id,
            "first_name":current_user.first_name,
            "last_name":current_user.last_name,
            "email":current_user.email,
            "role":current_user.role,
            "has_paid":user_has_paid_today(db, wallet_id)
        },
    }

