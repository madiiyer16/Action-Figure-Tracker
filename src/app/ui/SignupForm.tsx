'use client'
import { useActionState } from 'react'
import Link from 'next/link'
import { signup, type AuthState } from '@/app/actions/auth'

export default function SignupForm() {
  const [state, action, pending] = useActionState<AuthState, FormData>(signup, undefined)

  return (
    <form action={action} className="space-y-4">
      {state?.message && (
        <p className="text-sm text-red-400 bg-red-950/40 border border-red-800 rounded-lg px-3 py-2">
          {state.message}
        </p>
      )}

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-1">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500"
          placeholder="you@example.com"
        />
        {state?.errors?.email && (
          <p className="text-xs text-red-400 mt-1">{state.errors.email[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-1">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500"
          placeholder="Min 8 characters"
        />
        {state?.errors?.password && (
          <p className="text-xs text-red-400 mt-1">{state.errors.password[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="zipCode" className="block text-sm font-medium text-zinc-300 mb-1">
          ZIP code{' '}
          <span className="text-zinc-600 font-normal">(optional — used for shipping estimates)</span>
        </label>
        <input
          id="zipCode"
          name="zipCode"
          type="text"
          autoComplete="postal-code"
          className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500"
          placeholder="e.g. 90210"
        />
      </div>

      <button
        type="submit"
        disabled={pending}
        className="w-full bg-zinc-100 text-zinc-900 font-medium py-2 rounded-lg text-sm hover:bg-white transition-colors disabled:opacity-50"
      >
        {pending ? 'Creating account…' : 'Create account'}
      </button>

      <p className="text-center text-sm text-zinc-500">
        Already have an account?{' '}
        <Link href="/login" className="text-zinc-300 hover:text-white transition-colors">
          Sign in
        </Link>
      </p>
    </form>
  )
}
