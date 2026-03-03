import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load the connection string from your .env file
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

# The Engine is the core interface to the database.
# pool_pre_ping=True is a crucial backend trick! It tests the connection 
# before sending a query. Since Neon is serverless and goes to sleep, 
# this prevents our app from crashing when Neon wakes up.
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# A SessionLocal class will be used to create actual database sessions per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All our models will inherit from this Base class
Base = declarative_base()

# This is a dependency we will inject into our FastAPI routes later.
# It ensures each API request gets its own database connection, and closes it when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()