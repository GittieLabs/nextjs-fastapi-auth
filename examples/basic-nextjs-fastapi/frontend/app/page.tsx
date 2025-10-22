import Link from 'next/link'

export default function Home() {
  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Basic Auth Example</h1>
      <p style={{ marginTop: '20px', fontSize: '18px' }}>
        Welcome to the basic authentication example using{' '}
        <code>@gittielabs/nextjs-fastapi-auth</code>
      </p>

      <div style={{ marginTop: '40px' }}>
        <h2>Features</h2>
        <ul style={{ lineHeight: '2' }}>
          <li>Supabase authentication with JWT tokens</li>
          <li>Protected routes with middleware</li>
          <li>Authenticated API calls to FastAPI backend</li>
          <li>Simple login/dashboard flow</li>
        </ul>
      </div>

      <div style={{ marginTop: '40px', display: 'flex', gap: '20px' }}>
        <Link
          href="/login"
          style={{
            padding: '12px 24px',
            backgroundColor: '#0070f3',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px',
          }}
        >
          Go to Login
        </Link>
        <Link
          href="/dashboard"
          style={{
            padding: '12px 24px',
            backgroundColor: '#666',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px',
          }}
        >
          Go to Dashboard
        </Link>
      </div>

      <div style={{ marginTop: '60px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h3>Quick Start</h3>
        <ol style={{ lineHeight: '2' }}>
          <li>Set up your Supabase project and get credentials</li>
          <li>Configure environment variables in <code>.env.local</code></li>
          <li>Create a test user in Supabase dashboard</li>
          <li>Start the FastAPI backend: <code>cd backend && uvicorn main:app --reload</code></li>
          <li>Start the Next.js frontend: <code>cd frontend && npm run dev</code></li>
          <li>Log in with your test user credentials</li>
        </ol>
      </div>
    </div>
  )
}
