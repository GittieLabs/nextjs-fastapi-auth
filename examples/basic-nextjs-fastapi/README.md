# Basic Next.js + FastAPI Authentication Example

This example demonstrates a minimal working setup of the `@gittielabs/nextjs-fastapi-auth` library with:
- User authentication via Supabase
- Protected routes in Next.js
- Authenticated API calls to FastAPI backend
- Simple login/dashboard flow

## Project Structure

```
basic-nextjs-fastapi/
├── frontend/          # Next.js 15 application
│   ├── app/
│   │   ├── page.tsx              # Landing page
│   │   ├── login/page.tsx        # Login page
│   │   ├── dashboard/page.tsx    # Protected dashboard
│   │   └── api/
│   │       └── user/route.ts     # API route proxying to FastAPI
│   ├── middleware.ts             # Auth middleware
│   └── package.json
│
└── backend/           # FastAPI application
    ├── main.py                   # FastAPI app with auth
    ├── requirements.txt
    └── .env.example
```

## Prerequisites

- Node.js 18+
- Python 3.9+
- Supabase account with a project created

## Setup Instructions

### 1. Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to Settings > API and copy:
   - Project URL
   - Anon/Public Key
   - Service Role Key

3. Create a test user:
   - Go to Authentication > Users
   - Click "Add user"
   - Create a user with email/password

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your Supabase credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Run the FastAPI server
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local and add your Supabase credentials
# NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run the Next.js dev server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Testing the Application

1. **Open the app**: Navigate to `http://localhost:3000`

2. **Go to login**: Click "Login" or navigate to `/login`

3. **Sign in**: Use the test user credentials you created in Supabase

4. **View dashboard**: After successful login, you'll be redirected to `/dashboard`

5. **See authenticated data**: The dashboard fetches user data from the FastAPI backend

## Features Demonstrated

### Authentication Flow
- User login via Supabase Auth
- JWT token storage in httpOnly cookies
- Automatic token validation on protected routes

### Protected Routes
- Dashboard page requires authentication
- Automatic redirect to login if not authenticated
- Middleware handles authentication checks

### Authenticated API Calls
- Frontend makes authenticated requests to backend
- JWT token automatically included in requests
- FastAPI validates tokens and returns user data

### Error Handling
- Invalid credentials show error messages
- Expired tokens trigger re-authentication
- Network errors are caught and displayed

## API Endpoints

### Frontend (Next.js)

- `GET /` - Landing page (public)
- `GET /login` - Login page (public)
- `GET /dashboard` - Dashboard (protected)
- `GET /api/user` - Proxies to FastAPI user endpoint

### Backend (FastAPI)

- `GET /health` - Health check (public)
- `GET /api/v1/user/me` - Get current user (requires auth)
- `GET /api/v1/data` - Get sample data (requires auth)

## Code Walkthrough

### Middleware Setup

The `middleware.ts` file uses the auth library to protect routes:

```typescript
import { authMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

export default authMiddleware
```

### Login Component

The login page uses Supabase to authenticate users:

```typescript
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
})
```

### Protected Dashboard

The dashboard fetches authenticated user data:

```typescript
const response = await authenticatedFetch('http://localhost:8000/api/v1/user/me')
const userData = await response.json()
```

### FastAPI Backend

The backend validates JWT tokens and returns user info:

```python
@app.get("/api/v1/user/me")
async def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    token = auth_service.extract_token_from_header(auth_header)
    user = await auth_service.get_user_from_token(token)
    return user
```

## Troubleshooting

### "No JWT token found"

**Problem**: Authentication isn't working.

**Solution**:
- Check that you logged in successfully
- Verify cookies are being set (check browser dev tools)
- Ensure `NEXT_PUBLIC_SUPABASE_URL` is correct

### "CORS errors"

**Problem**: Browser blocking requests from Next.js to FastAPI.

**Solution**:
- Backend CORS middleware is configured in `main.py`
- Verify `allow_origins` includes `http://localhost:3000`
- Check that both servers are running

### "Invalid token"

**Problem**: FastAPI rejecting the JWT token.

**Solution**:
- Verify `SUPABASE_SERVICE_ROLE_KEY` in backend `.env`
- Ensure it's the service role key, not the anon key
- Check token hasn't expired (re-login)

### "Module not found" errors

**Problem**: Dependencies not installed.

**Solution**:
```bash
# Frontend
cd frontend && npm install

# Backend
cd backend && pip install -r requirements.txt
```

## Next Steps

After getting this example working, explore:

- [Multi-tenant example](../multi-tenant-subdomains/) - Organization-based routing
- [Admin dashboard example](../admin-dashboard/) - Role-based access control
- [Full documentation](../../docs/quickstart.md) - Comprehensive guide

## Support

- [GitHub Issues](https://github.com/gittielabs/nextjs-fastapi-auth/issues)
- [Documentation](../../README.md)
