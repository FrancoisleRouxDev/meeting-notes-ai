"""Create the demo accounts used by the README."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import SessionLocal, engine
from app.models import User

DEMO_USERS = (
    ("demo1@example.com", "LaunchPadDemo1!"),
    ("demo2@example.com", "LaunchPadDemo2!"),
)


def seed_demo_users(db: Session) -> tuple[list[str], list[str]]:
    created: list[str] = []
    existing: list[str] = []

    for email, password in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            existing.append(email)
            continue

        db.add(User(email=email, password_hash=hash_password(password)))
        created.append(email)

    db.commit()
    return created, existing


def main() -> None:
    User.__table__.create(bind=engine, checkfirst=True)
    with SessionLocal() as db:
        created, existing = seed_demo_users(db)

    if created:
        print("Created demo accounts:")
        for email, password in DEMO_USERS:
            if email in created:
                print(f"  {email} / {password}")
    if existing:
        print("Left existing accounts unchanged: " + ", ".join(existing))


if __name__ == "__main__":
    main()
