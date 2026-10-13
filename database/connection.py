"""Database connection manager using SQLAlchemy and PyMySQL.
Handles connection pooling, engine initialization, and session management.
"""

import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Profile

# Load .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "job_search_rec")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_database_url() -> str:
    """Build MySQL SQLAlchemy connection URL with PyMySQL driver."""
    # Ensure URL encoding or raw string handling for special chars in password
    from urllib.parse import quote_plus
    encoded_user = quote_plus(DB_USER)
    encoded_pwd = quote_plus(DB_PASSWORD)
    return f"mysql+pymysql://{encoded_user}:{encoded_pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

_engine = None
_SessionFactory = None

def get_engine():
    """Retrieve or create singleton SQLAlchemy Engine."""
    global _engine, _SessionFactory
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": 10}
        )
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine

def get_session() -> Session:
    """Create a new database session."""
    global _SessionFactory
    if _SessionFactory is None:
        get_engine()
    return _SessionFactory()

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def test_connection():
    """Test MySQL database connection. Returns (bool, str)."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;"))
            val = result.scalar()
            if val == 1:
                return True, "Connected successfully to MySQL database."
        return False, "Unknown connection status."
    except Exception as e:
        return False, f"MySQL connection failed: {str(e)}"

def init_db():
    """Initialize database schema and seed default profile."""
    engine = get_engine()
    # Create tables if not present
    Base.metadata.create_all(bind=engine)

    # Seed initial candidate profile if empty
    with session_scope() as session:
        existing = session.query(Profile).filter_by(id=1).first()
        if not existing:
            default_profile = Profile(
                id=1,
                candidate_name="Sindhu Suraj",
                skills="Python, Machine Learning, SQL, Data Analysis",
                preferred_location="Bengaluru, India",
                preferred_work_model="All"
            )
            session.add(default_profile)
            session.commit()
