#!/usr/bin/env python3
"""Create an anonymous user in the local Firebase Auth emulator and print uid + ID token.

Usage:
    FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 python scripts/dev_token.py
    FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 python scripts/dev_token.py --token-only
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def create_anonymous_user_token(auth_emulator_host: str) -> tuple[str, str]:
    """Call the Firebase Auth emulator accounts:signUp endpoint and return (uid, id_token)."""
    url = (
        f"http://{auth_emulator_host}"
        "/identitytoolkit.googleapis.com/v1/accounts:signUp?key=fake-api-key"
    )
    body = json.dumps({"returnSecureToken": True}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach Firebase Auth emulator at {auth_emulator_host}: {exc}"
        ) from exc

    uid = data.get("localId")
    id_token = data.get("idToken")
    if not uid or not id_token:
        raise RuntimeError("Auth emulator response did not include localId and idToken.")
    return uid, id_token


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mint an anonymous Firebase Auth emulator ID token for local testing."
    )
    parser.add_argument(
        "--token-only",
        action="store_true",
        help="Print only the ID token (useful for shell substitution).",
    )
    args = parser.parse_args()

    auth_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "").strip()
    if not auth_host:
        print(
            "ERROR: FIREBASE_AUTH_EMULATOR_HOST is not set.\n"
            "This script only runs against the local Firebase Auth emulator.\n"
            "Example: FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 python scripts/dev_token.py",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        uid, id_token = create_anonymous_user_token(auth_host)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.token_only:
        print(id_token)
    else:
        print(f"UID: {uid}")
        print(f"ID_TOKEN: {id_token}")


if __name__ == "__main__":
    main()
