import { authMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

export default authMiddleware

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}
