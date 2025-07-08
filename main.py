from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uvicorn
from datetime import datetime, timedelta, UTC
# Configuration
SECRET_KEY = "Y3Q4TdDRnIt75LXEirWPneesIVB1N3YtW61BHXujPPU"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(title="Flutter Auth API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserSignUp(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class ListItem(BaseModel):
    id: int
    title: str
    description: str
    category: str
    created_at: datetime

# In-memory storage (use database in production)
users_db = {}
items_db = [
    {
        "id": 1,
        "title": "Premium Laptop",
        "description": "High-performance laptop for professionals",
        "category": "Electronics",
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Wireless Headphones",
        "description": "Noise-cancelling wireless headphones",
        "category": "Electronics",
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Coffee Maker",
        "description": "Automatic coffee brewing machine",
        "category": "Appliances",
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Office Chair",
        "description": "Ergonomic office chair with lumbar support",
        "category": "Furniture",
        "created_at": datetime.now()
    },
    {
        "id": 5,
        "title": "Smartphone",
        "description": "Latest smartphone with advanced camera",
        "category": "Electronics",
        "created_at": datetime.now()
    }
]

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Routes
@app.post("/api/auth/signup", response_model=Token)
async def signup(user: UserSignUp):
    # Check if user already exists
    if user.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and save user
    hashed_password = get_password_hash(user.password)
    users_db[user.email] = {
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": hashed_password
    }
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "full_name": user.full_name,
            "email": user.email
        }
    }

@app.post("/api/auth/signin", response_model=Token)
async def signin(user: UserSignIn):
    # Check if user exists
    if user.email not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    stored_user = users_db[user.email]
    if not verify_password(user.password, stored_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "full_name": stored_user["full_name"],
            "email": stored_user["email"]
        }
    }

@app.get("/api/items", response_model=List[dict])
async def get_items(current_user: str = Depends(verify_token)):
    # Return items only if user is authenticated
    formatted_items = []
    for item in items_db:
        formatted_items.append({
            "id": item["id"],
            "title": item["title"],
            "description": item["description"],
            "category": item["category"],
            "created_at": item["created_at"].isoformat()
        })
    return formatted_items

@app.get("/api/auth/me")
async def get_current_user(current_user: str = Depends(verify_token)):
    user_info = users_db.get(current_user)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {
        "full_name": user_info["full_name"],
        "email": user_info["email"]
    }

@app.get("/")
async def root():
    return {"message": "Flutter Auth API is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    
    
blacklisted_tokens = set()

