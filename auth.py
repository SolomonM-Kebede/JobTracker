"""
Microsoft MSAL Authentication for @live.com accounts
Handles OAuth2 login and token refresh automatically.
Requires: Mobile and desktop applications platform in Azure AD
"""

import os
import msal
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID        = os.getenv("APPLICATION_CLIENT_ID")
TENANT_ID        = os.getenv("TENANT_ID", "consumers")

SCOPES           = ["Mail.Read", "Mail.ReadWrite", "MailboxSettings.Read"]
TOKEN_CACHE_FILE = "data/token_cache.json"
AUTHORITY        = f"https://login.microsoftonline.com/{TENANT_ID}"


def _load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        os.makedirs("data", exist_ok=True)
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_access_token():
    """
    Returns a valid access token.
    - First run: opens browser for login.
    - Subsequent runs: silently refreshes from cache.
    """
    cache = _load_cache()

    # PublicClientApplication 
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    accounts = app.get_accounts()
    result = None

    # Try silent token refresh first
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # Open browser for interactive login
    if not result:
        print("\n Opening browser for Microsoft login...")
        print("   Sign in with your @live.com account.\n")
        result = app.acquire_token_interactive(scopes=SCOPES)

    _save_cache(cache)

    if "access_token" in result:
        print("Authentication successful.")
        return result["access_token"]
    else:
        error = result.get("error_description") or result.get("error") or str(result)
        raise Exception(f"Auth failed: {error}")


if __name__ == "__main__":
    token = get_access_token()
    print(f"\nToken (first 40 chars): {token[:40]}...")