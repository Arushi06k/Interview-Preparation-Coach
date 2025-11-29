from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This is the full URL path to our SQLite database file.
# 'sqlite:///./interview_sessions.db' means the file will be named 'interview_sessions.db'
# and it will be located in the same directory as our main script.
SQLALCHEMY_DATABASE_URL = "sqlite:///./interview_sessions.db"

# The 'engine' is the core interface to the database. It's how SQLAlchemy
# communicates with the database using a specific dialect (in this case, sqlite).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# A SessionLocal class is a "factory" for creating new database sessions.
# Think of a session as a temporary, short-lived conversation with the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from this Base class to create each of the database models (ORM models).
# It's like a blueprint for our tables.
Base = declarative_base()