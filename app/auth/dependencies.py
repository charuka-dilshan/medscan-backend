import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


load_dotenv()


JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "medscan-ai-hackathon-secret-key-2026",
)

JWT_ALGORITHM = "HS256"


# Swagger UI and frontend applications read the JWT token
# from the Authorization: Bearer <token> header.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login"
)


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> int:
    """
    Decode the JWT token and return the authenticated user's ID.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please login again.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

        return int(user_id)

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        TypeError,
        ValueError,
    ) as error:
        raise credentials_exception from error