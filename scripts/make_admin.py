#!/usr/bin/env python3
"""Set role='admin' on users/{uid} in Firestore (emulator by default).

Usage:
    python scripts/make_admin.py <uid>
    python scripts/make_admin.py <uid> --allow-remote
"""

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.user import UserDoc
from app.repositories.user_repository import UserRepository


def promote_to_admin(uid: str, repo: UserRepository | None = None) -> UserDoc:
    """Set role='admin' on users/{uid}, creating the document if it does not exist."""
    user_repo = repo if repo is not None else UserRepository()
    existing = user_repo.get(uid)
    if existing is not None:
        updated = user_repo.update_fields(uid, {"role": "admin"})
        if updated is None:
            raise RuntimeError(f"Failed to update user {uid} to admin.")
        return updated

    now = datetime.now(UTC)
    new_admin = UserDoc(
        uid=uid,
        role="admin",
        display_name=None,
        auth_provider="email",
        preferred_language="bn",
        created_at=now,
        last_login=now,
    )
    return user_repo.create(new_admin)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote a PothSathi user to role='admin'.")
    parser.add_argument("uid", help="Firebase Auth UID of the user to promote.")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow writing to a remote Firestore project (requires interactive confirmation).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uid = args.uid.strip()
    if not uid:
        print("ERROR: uid must not be empty.", file=sys.stderr)
        sys.exit(1)

    if not args.allow_remote:
        # Emulator by default: guarantee we never touch remote Firestore accidentally
        os.environ.setdefault("APP_ENV", "dev")
        os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")
        if os.environ.get("APP_ENV") == "prod":
            print(
                "ERROR: Refusing to run in APP_ENV=prod without --allow-remote.",
                file=sys.stderr,
            )
            sys.exit(1)
        target_label = f"emulator ({os.environ['FIRESTORE_EMULATOR_HOST']})"
    else:
        if os.environ.get("FIRESTORE_EMULATOR_HOST"):
            print(
                "ERROR: --allow-remote cannot be used while FIRESTORE_EMULATOR_HOST is set.",
                file=sys.stderr,
            )
            sys.exit(1)
        confirmation = input(
            f"WARNING: You are about to set role='admin' for uid '{uid}' on REMOTE Firestore.\n"
            "Type 'CONFIRM' to proceed: "
        ).strip()
        if confirmation != "CONFIRM":
            print("Aborted. Remote Firestore was not modified.", file=sys.stderr)
            sys.exit(1)
        target_label = "REMOTE Firestore"

    doc = promote_to_admin(uid)
    print(f"Success: users/{doc.uid} now has role='{doc.role}' on {target_label}.")


if __name__ == "__main__":
    main()
