"""
Seed script: delete all users and create verified team accounts.

Run from the project root:
    python scripts/seed_team.py

Default password for all accounts: SoundWave@2026
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.core.security import hash_password  # noqa: E402

DEFAULT_PASSWORD = "SoundWave@2026"

TEAM_ACCOUNTS = [
    {
        "display_name": "Mostafa Yasser",
        "username": "mostafayasser",
        "email": "mostafa.yasser@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Mohamed Khaled",
        "username": "mohamedkhaled",
        "email": "mohamed.khaled@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Amira Elwakeel",
        "username": "amiraelwakeel",
        "email": "amira.elwakeel@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Hana Ahmed",
        "username": "hanaahmed",
        "email": "hana.ahmed@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Ahmed Sayed",
        "username": "ahmedsayed",
        "email": "ahmed.sayed@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Yassin Ragheb",
        "username": "yassinragheb",
        "email": "yassin.ragheb@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Mohamed Samy",
        "username": "mohamedsamy",
        "email": "mohamed.samy@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Julia Ehab",
        "username": "juliaehab",
        "email": "julia.ehab@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Irene Amgad",
        "username": "ireneamgad",
        "email": "irene.amgad@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Retaj Hussein",
        "username": "retajhussein",
        "email": "retaj.hussein@soundwave.com",
        "account_type": "listener",
    },
    {
        "display_name": "Mo'men",
        "username": "momen",
        "email": "momen@soundwave.com",
        "account_type": "listener",
    },
]


def run():
    db = SessionLocal()
    try:
        print("Deleting all existing users and related data...")
        db.execute(text("TRUNCATE TABLE users CASCADE"))
        db.commit()
        print("  Done.")

        print("\nCreating team accounts...")
        hashed = hash_password(DEFAULT_PASSWORD)
        for account in TEAM_ACCOUNTS:
            user = User(
                email=account["email"],
                username=account["username"],
                password_hash=hashed,
                display_name=account["display_name"],
                account_type=account["account_type"],
                is_verified=True,
            )
            db.add(user)
            print(f"  + {account['display_name']} (@{account['username']})")

        db.commit()
        print(f"\nDone. All {len(TEAM_ACCOUNTS)} accounts created.")
        print(f"Default password: {DEFAULT_PASSWORD}")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
