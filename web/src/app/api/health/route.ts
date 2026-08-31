import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      cache: 'no-store',
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ status: 'error', message: 'Backend not reachable' }, { status: 503 })
  }
}
