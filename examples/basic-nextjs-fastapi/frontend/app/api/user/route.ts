import { NextRequest, NextResponse } from 'next/server'
import { validateAdminAuth } from '@gittielabs/nextjs-fastapi-auth/server'

export async function GET(request: NextRequest) {
  // Validate authentication
  const auth = validateAdminAuth(request)

  if (auth.error) {
    return auth.error
  }

  // User is authenticated - return user data
  return NextResponse.json({
    user: auth.user,
    message: 'User authenticated successfully',
  })
}
