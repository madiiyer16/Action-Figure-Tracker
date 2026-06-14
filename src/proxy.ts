import { NextRequest, NextResponse } from 'next/server'
import { decrypt } from '@/lib/session'

const protectedRoutes = ['/watchlist']

export async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname

  if (protectedRoutes.some((r) => path === r || path.startsWith(r + '/'))) {
    const token = req.cookies.get('session')?.value
    const session = await decrypt(token)
    if (!session?.userId) {
      return NextResponse.redirect(new URL('/login', req.nextUrl))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.(?:png|ico|svg|jpg|jpeg|webp)$).*)'],
}
