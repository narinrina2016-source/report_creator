from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models import setting, template, user, report
from app.core.security import get_password_hash

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated Report Management System API",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        admin = db.query(user.User).filter(user.User.email == settings.FIRST_SUPERUSER_EMAIL).first()
        if not admin:
            admin_user = user.User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="System Administrator",
                role="Admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created successfully.")
    except Exception as e:
        print(f"Error seeding default admin: {e}")
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/setup-db")
def setup_database():
    """Set up the database schema."""
    import alembic.config
    import os
    results = {}
    
    # Method 1: SQLAlchemy create_all (Works for all models defined)
    try:
        Base.metadata.create_all(bind=engine)
        results["sqlalchemy"] = "Tables created successfully via SQLAlchemy"
    except Exception as e:
        results["sqlalchemy_error"] = str(e)
        
    # Method 2: Alembic
    try:
        alembic_args = ['--raiseerr', 'upgrade', 'head']
        alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini")
        alembic.config.main(argv=['-c', alembic_ini_path, *alembic_args])
        results["alembic"] = "Migrations applied successfully"
    except Exception as e:
        results["alembic_error"] = str(e)
        
    # Create superuser
    try:
        db = SessionLocal()
        admin = db.query(user.User).filter(user.User.email == settings.FIRST_SUPERUSER_EMAIL).first()
        if not admin:
            admin_user = user.User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="System Administrator",
                role="Admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            results["superuser"] = "Superuser created successfully"
        else:
            results["superuser"] = "Superuser already exists"
        db.close()
    except Exception as e:
        results["superuser_error"] = str(e)
        
    return results

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to ARMS API"}
