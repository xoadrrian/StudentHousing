import sys

from sqlalchemy import text

from database import SessionLocal
from models import Manager, Role, Tenant, User, Worker

if len(sys.argv) < 5:
    sys.exit("Usage: python create_test_users.py <email> <first name> <last name> <tenant|manager|worker> [room_id]")

email, first, last, role = sys.argv[1].strip().lower(), sys.argv[2], sys.argv[3], Role(sys.argv[4])
room_id = int(sys.argv[5]) if len(sys.argv) > 5 else None
if role is Role.tenant and room_id is None:
    sys.exit("A tenant needs a room_id.")

with SessionLocal() as db:
    account_id = db.execute(text("select id from auth.users where lower(email) = :e"),
                            {"e": email}).scalar()
    if account_id is None:
        sys.exit(f"No Supabase Auth account for {email}. Create it in the dashboard first.")

    user = db.get(User, account_id) or User(id=account_id, first_name=first, last_name=last, email=email)
    db.add(user)
    db.flush()
    if user.role is not None:
        sys.exit(f"{email} already has the role {user.role.value}.")

    if role is Role.tenant:
        db.add(Tenant(user_id=account_id, room_id=room_id))
    elif role is Role.manager:
        db.add(Manager(user_id=account_id))
    else:
        db.add(Worker(user_id=account_id))
    db.commit()
    print(f"{email} can now log in as {role.value}.")
