"""Provision an operator through a private server terminal with signup closed."""

from __future__ import annotations

import getpass

from app.db import SessionLocal, UserAccount
from app.schemas import SignUpRequest
from app.services.auth import hash_password
from sqlalchemy import select


def main():
    request = SignUpRequest(
        name=input("Operator name: "),
        email=input("Operator email: "),
        password=getpass.getpass("Password (hidden): "),
    )
    email = request.email.strip().lower()
    with SessionLocal() as db:
        if db.scalar(select(UserAccount).where(UserAccount.email == email)):
            raise SystemExit("Account already exists; no changes made")
        db.add(
            UserAccount(
                name=request.name, email=email, password_hash=hash_password(request.password), role="operator"
            )
        )
        db.commit()
    print("Operator created. Public signup remains disabled.")


if __name__ == "__main__":
    main()
