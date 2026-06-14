import 'server-only'
import { cache } from 'react'
import { redirect } from 'next/navigation'
import { getSession, type SessionPayload } from '@/lib/session'

export const getOptionalSession = cache(async (): Promise<SessionPayload | null> => {
  return getSession()
})

export const verifySession = cache(async (): Promise<SessionPayload> => {
  const session = await getSession()
  if (!session) redirect('/login')
  return session
})
