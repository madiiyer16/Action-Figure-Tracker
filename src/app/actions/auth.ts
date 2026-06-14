'use server'
import bcrypt from 'bcryptjs'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { createSession, deleteSession } from '@/lib/session'

export type AuthState =
  | { errors?: { email?: string[]; password?: string[]; zipCode?: string[] }; message?: string }
  | undefined

export async function signup(state: AuthState, formData: FormData): Promise<AuthState> {
  const email = (formData.get('email') as string | null)?.trim().toLowerCase() ?? ''
  const password = (formData.get('password') as string | null) ?? ''
  const zipCode = (formData.get('zipCode') as string | null)?.trim() ?? ''

  const errors: NonNullable<NonNullable<AuthState>['errors']> = {}
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = ['Valid email required.']
  if (password.length < 8) errors.password = ['Password must be at least 8 characters.']
  if (Object.keys(errors).length) return { errors }

  const existing = await prisma.user.findUnique({ where: { email } })
  if (existing) return { errors: { email: ['An account with this email already exists.'] } }

  const passwordHash = await bcrypt.hash(password, 10)
  const user = await prisma.user.create({
    data: { email, passwordHash, zipCode: zipCode || null },
  })

  await createSession(user.id)
  redirect('/watchlist')
}

export async function login(state: AuthState, formData: FormData): Promise<AuthState> {
  const email = (formData.get('email') as string | null)?.trim().toLowerCase() ?? ''
  const password = (formData.get('password') as string | null) ?? ''

  if (!email || !password) return { message: 'Email and password are required.' }

  const user = await prisma.user.findUnique({ where: { email } })
  if (!user) return { message: 'Invalid email or password.' }

  const valid = await bcrypt.compare(password, user.passwordHash)
  if (!valid) return { message: 'Invalid email or password.' }

  await createSession(user.id)
  redirect('/watchlist')
}

export async function logout(): Promise<void> {
  await deleteSession()
  redirect('/')
}
