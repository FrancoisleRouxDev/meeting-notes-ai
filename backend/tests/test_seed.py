from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User
from seed import DEMO_USERS, seed_demo_users


def test_seed_creates_hashed_demo_accounts_and_is_idempotent():
    engine = create_engine("sqlite://")
    User.__table__.create(bind=engine)

    with Session(engine) as db:
        created, existing = seed_demo_users(db)
        assert created == [email for email, _ in DEMO_USERS]
        assert existing == []

        initial_hashes = {}
        for email, password in DEMO_USERS:
            user = db.scalar(select(User).where(User.email == email))
            assert user is not None
            assert verify_password(user.password_hash, password)
            assert password not in user.password_hash
            initial_hashes[email] = user.password_hash

        created_again, existing_again = seed_demo_users(db)
        assert created_again == []
        assert existing_again == [email for email, _ in DEMO_USERS]
        for email, password_hash in initial_hashes.items():
            user = db.scalar(select(User).where(User.email == email))
            assert user is not None
            assert user.password_hash == password_hash

    engine.dispose()
