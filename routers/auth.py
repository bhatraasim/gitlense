from fastapi import APIRouter, HTTPException , Depends , Request
from pydantic import BaseModel, EmailStr
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from bson import ObjectId
from jose import JWTError
from model.user import UserResponse , User

# you'll build these helpers yourself
from services.auth import hash_password, create_token , verify_password , decode_token
from services.database import db


router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

@router.post("/register")
async def register(body: RegisterRequest):
    #1.check for existing user 
    existing_user = await db.users.find_one({"email": body.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    #2.hash the password
    hashed_password = hash_password(body.password)
    #3.create user record
    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hashed_password
    )
    result = await db.users.insert_one(user)
    user_id = str(result.inserted_id)
    #4.generate token
    token = create_token({
        "sub": str(result.inserted_id),
        "email": body.email
    })

    return {
    "access_token": token,
    "token_type": "bearer",
    "user": UserResponse(
        id=str(result.inserted_id),
        name=body.name,
        email=body.email,
        created_at=datetime.utcnow()
    )
}

@router.post("/login")
async def login(body: RegisterRequest):
    #1.find user by email
    user = await db.users.find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email")
    #2.verify password
    if not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid  password")
    #3.generate token
    token = create_token({
        "sub": str(user["_id"]),
        "email": user["email"]
    })
    return {
    "access_token": token,
    "token_type": "bearer",
    "user": UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"]
    )
}


@router.post("/logout")
async def logout():
    # For JWT, logout is typically handled on the client side by deleting the token.
    # You can also implement token blacklisting on the server if needed.
    return {"message": "Logged out successfully"}

security = HTTPBearer()





async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except HTTPException:
        raise                        # re-raise your own HTTP exceptions as-is
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")