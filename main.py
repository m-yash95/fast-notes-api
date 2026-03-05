from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
import utils
from database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

# Initialize the FastAPI application
app = FastAPI(title="Fast Notes API", description="A simple note taking backend")

# This tells FastAPI where to look for the token (the /users/login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    The Bouncer: Decodes the token, validates it, and fetches the user from the DB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch the user from the database
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# --- USER ENDPOINTS ---

@app.post("/users/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user by providing an email and password.
    """
    # 1. Check if a user with this email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )

    # 2. Hash the raw password
    hashed_pwd = utils.hash_password(user.password)

    # 3. Create a new SQLAlchemy User object
    new_user = models.User(email=user.email, hashed_password=hashed_pwd)

    # 4. Save to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Fetches the newly created ID and timestamp from Postgres

    # 5. Return the user (FastAPI automatically strips the password using UserResponse)
    return new_user

@app.post("/users/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Log in a user and return a JWT token.
    Note: OAuth2 uses 'username' by default, but we are passing our email into it.
    """
    # 1. Find the user by email (which is stored in the username field of the form)
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    
    # 2. If user doesn't exist, or password doesn't match, throw a 401 Unauthorized
    if not user or not utils.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 3. Create the JWT token (we embed the user's email inside the token payload as the "subject")
    access_token = utils.create_access_token(data={"sub": user.email})
    
    # 4. Return the token to the user
    return {"access_token": access_token, "token_type": "bearer"}

# --- PROTECTED USER ROUTES ---

@app.get("/users/me", response_model=schemas.UserResponse)
def get_user_details(current_user: models.User = Depends(get_current_user)):
    """
    Returns the currently logged-in user's details.
    """
    return current_user

@app.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Allows a logged-in user to delete their own account.
    """
    db.delete(current_user)
    db.commit()
    return None # 204 No Content doesn't return a body

# --- NOTE ENDPOINTS ---

@app.post("/notes/", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: schemas.NoteCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_note = models.Note(**note.model_dump(), owner_id=current_user.id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/notes/", response_model=list[schemas.NoteResponse])
def get_notes(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Note).filter(models.Note.owner_id == current_user.id).all()

@app.get("/notes/{note_id}", response_model=schemas.NoteResponse)
def get_note(note_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note

@app.patch("/notes/{note_id}", response_model=schemas.NoteResponse)
def update_note(note_id: int, payload: schemas.NoteUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    db.delete(note)
    db.commit()
    return None

@app.get("/")
def read_root():
    return {"message": "Welcome to the Fast Notes API!"}