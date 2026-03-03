import os
from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Token expires in 1 hour
def hash_password(password: str) -> str:
    """Takes a raw password and returns a hashed version using raw bcrypt."""
    # bcrypt requires bytes, not strings
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    
    # Decode back to a string so SQLAlchemy can store it in the database
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if a raw password matches the hashed version in the DB."""
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password=password_bytes, hashed_password=hashed_password_bytes)

def create_access_token(data: dict):
    """Creates a JWT token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # This mathematically signs the token using your SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt