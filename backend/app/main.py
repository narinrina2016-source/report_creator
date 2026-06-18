from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models import setting, template, user, report
from app.core.security import get_password_hash

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated Report Management System API",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        admin = db.query(user.User).filter(user.User.email == "admin@example.com").first()
        if not admin:
            admin_user = user.User(
                email="admin@example.com",
                hashed_password=get_password_hash("password123"),
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

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to ARMS API"}
