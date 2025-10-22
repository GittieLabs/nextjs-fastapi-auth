'use client'

import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export default function DashboardPage() {
  const [userData, setUserData] = useState<any>(null)
  const [sampleData, setSampleData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const router = useRouter()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)

      // Fetch user data from FastAPI backend
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const userResponse = await authenticatedFetch(`${apiUrl}/api/v1/user/me`)

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user data')
      }

      const user = await userResponse.json()
      setUserData(user)

      // Fetch sample data
      const dataResponse = await authenticatedFetch(`${apiUrl}/api/v1/data`)

      if (dataResponse.ok) {
        const data = await dataResponse.json()
        setSampleData(data)
      }
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('Failed to load data. Please try logging in again.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
  }

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h1>Loading...</h1>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ padding: '20px', backgroundColor: '#fee', color: '#c00', borderRadius: '8px' }}>
          {error}
        </div>
        <button
          onClick={() => router.push('/login')}
          style={{
            marginTop: '20px',
            padding: '12px 24px',
            backgroundColor: '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Go to Login
        </button>
      </div>
    )
  }

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <h1>Dashboard</h1>
        <button
          onClick={handleLogout}
          style={{
            padding: '10px 20px',
            backgroundColor: '#666',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Logout
        </button>
      </div>

      <div style={{ marginBottom: '40px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h2 style={{ marginBottom: '20px' }}>User Information</h2>
        {userData && (
          <div style={{ fontFamily: 'monospace', fontSize: '14px' }}>
            <div style={{ marginBottom: '10px' }}>
              <strong>Email:</strong> {userData.email}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>User ID:</strong> {userData.id}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Role:</strong> {userData.role}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Authenticated:</strong> {userData.is_authenticated ? 'Yes' : 'No'}
            </div>
            {userData.organization_id && (
              <div>
                <strong>Organization ID:</strong> {userData.organization_id}
              </div>
            )}
          </div>
        )}
      </div>

      {sampleData && (
        <div style={{ padding: '20px', backgroundColor: '#f0f7ff', borderRadius: '8px' }}>
          <h2 style={{ marginBottom: '20px' }}>Sample Data</h2>
          <p style={{ marginBottom: '20px' }}>{sampleData.message}</p>

          <h3 style={{ marginBottom: '15px' }}>Data Items:</h3>
          <div style={{ display: 'grid', gap: '15px' }}>
            {sampleData.data?.map((item: any) => (
              <div
                key={item.id}
                style={{
                  padding: '15px',
                  backgroundColor: 'white',
                  borderRadius: '6px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                }}
              >
                <strong>{item.title}</strong>
                <p style={{ margin: '8px 0 0 0', color: '#666' }}>{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '40px', padding: '20px', backgroundColor: '#efe', borderRadius: '8px' }}>
        <h3 style={{ marginBottom: '10px' }}>Authentication Success!</h3>
        <p style={{ color: '#060' }}>
          You are viewing authenticated data fetched from the FastAPI backend. The JWT token was
          automatically included in the request using <code>authenticatedFetch()</code>.
        </p>
      </div>
    </div>
  )
}
