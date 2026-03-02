from fastapi import HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError
from httpx import AsyncClient
from app.config import settings

# Simple OIDC Flow implementation
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.POCKET_ID_ISSUER}/authorize",
    tokenUrl=f"{settings.POCKET_ID_ISSUER}/token",
    scheme_name="PocketID"
)

async def get_current_user(request: Request):
    # In a real prod app, verify the JWT signature using Pocket ID's public key
    # For this MVP, we assume the session middleware handles validation or we do a simple introspection
    # Since we are using server-side sessions with FastAPI, we'll rely on a custom dependency
    # that checks the session state populated during callback.

    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
