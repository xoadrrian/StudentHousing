"""
Creates one test account per role, with names from the case data.
Run once:  python create_test_users.py
Password for all three: Test1234!   (test accounts only, never real ones)
"""
from sqlalchemy import select

from database import SessionLocal, engine
from models import Base, Role, User
from routers.auth import hash_password

TEST_PASSWORD = "Test1234!"
USERS = [
    ("Emma", "Johnson", "emma.johnson@xyzmail.com", Role.tenant),
    ("John", "Doe", "john@studenthousing.com", Role.manager),
    ("Alice", "Smith", "alice@studenthousing.com", Role.worker),
]

Base.metadata.create_all(engine)
with SessionLocal() as db:
    for first, last, email, role in USERS:
        if db.scalar(select(User).where(User.email == email)):
            print("exists: ", email)
            continue
        db.add(User(first_name=first, surname=last, email=email,
                    password_hash=hash_password(TEST_PASSWORD), role=role))
        print("created:", email, f"({role.value})")
    db.commit()
