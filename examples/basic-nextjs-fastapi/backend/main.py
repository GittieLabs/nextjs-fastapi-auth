"""
Basic FastAPI example with Supabase authentication using gittielabs-nextjs-fastapi-auth
"""

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gittielabs_fastapi_auth import SupabaseAuthService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Basic Auth Example API",
    description="Example FastAPI application with Supabase authentication",
    version="1.0.0",
)

# CORS configuration - allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize auth service
auth_service = SupabaseAuthService(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)


@app.get("/health")
async def health():
    """Health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "service": "basic-auth-example",
        "version": "1.0.0",
    }


@app.get("/api/v1/user/me")
async def get_current_user(request: Request):
    """
    Get the current authenticated user

    This endpoint requires authentication via Bearer token in the Authorization header.
    """
    # Extract authorization header
    auth_header = request.headers.get("authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    # Extract and validate JWT token
    token = auth_service.extract_token_from_header(auth_header)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Return user information
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "is_authenticated": user.is_authenticated,
        "organization_id": user.organization_id,
    }


@app.get("/api/v1/data")
async def get_sample_data(request: Request):
    """
    Get sample data for the authenticated user

    This demonstrates fetching data that requires authentication.
    In a real app, you would filter this data based on the user's organization or permissions.
    """
    # Extract and validate user
    auth_header = request.headers.get("authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization required")

    token = auth_service.extract_token_from_header(auth_header)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Return sample data
    return {
        "message": f"Hello {user.email}! Here is your data.",
        "data": [
            {"id": 1, "title": "Item 1", "description": "First item"},
            {"id": 2, "title": "Item 2", "description": "Second item"},
            {"id": 3, "title": "Item 3", "description": "Third item"},
        ],
        "user_email": user.email,
        "timestamp": "2025-10-22T12:00:00Z",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Basic Auth Example API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
