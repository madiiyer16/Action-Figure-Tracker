import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'
import { getSession } from '@/lib/session'

export async function POST(request: NextRequest) {
  const session = await getSession()
  if (!session) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await request.json().catch(() => null)
  const figureId = typeof body?.figureId === 'number' ? body.figureId : null
  const targetPriceUsd =
    typeof body?.targetPriceUsd === 'number' && body.targetPriceUsd > 0
      ? body.targetPriceUsd
      : null

  if (!figureId) return Response.json({ error: 'figureId required' }, { status: 400 })

  const figure = await prisma.figure.findUnique({ where: { id: figureId } })
  if (!figure) return Response.json({ error: 'Figure not found' }, { status: 404 })

  const entry = await prisma.watchlist.upsert({
    where: { userId_figureId: { userId: session.userId, figureId } },
    create: { userId: session.userId, figureId, targetPriceUsd },
    update: { targetPriceUsd },
  })

  return Response.json({ id: entry.id, figureId: entry.figureId }, { status: 201 })
}
