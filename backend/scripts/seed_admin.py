import sys
import os

# Add the backend directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash

def seed_admin():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if admin:
            admin.hashed_password = get_password_hash("password123")
            db.commit()
            print("Admin password reset to 'password123'")
            return

        # Create admin user
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="System Administrator",
            role="Admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
        print("Email: admin@example.com")
        print("Password: password123")
    except Exception as e:
        print(f"Error seeding admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
