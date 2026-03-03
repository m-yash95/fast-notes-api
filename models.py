from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from database import Base

# Define our strict sharing permissions
class PermissionLevel(str, enum.Enum):
    VIEW = "view"
    EDIT = "edit"
    FULL = "full"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Using timezone-aware UTC is a backend best practice
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One User has many Notes. If User is deleted, orphan the notes (delete them).
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Foreign key linking back to the User
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Relationships mapping back to the objects
    owner = relationship("User", back_populates="notes")
    shares = relationship("NoteShare", back_populates="note", cascade="all, delete-orphan")

class NoteShare(Base):
    __tablename__ = "note_shares"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"))
    shared_with_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    permission_level = Column(Enum(PermissionLevel), default=PermissionLevel.VIEW)

    note = relationship("Note", back_populates="shares")
    shared_user = relationship("User")