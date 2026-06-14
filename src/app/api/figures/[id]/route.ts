import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const figureId = parseInt(id)
  if (isNaN(figureId)) {
    return Response.json({ error: 'Invalid id' }, { status: 400 })
  }

  const figure = await prisma.figure.findUnique({
    where: { id: figureId },
    include: {
      listings: {
        where: { currentPriceUsd: { lte: 5000 } },
        orderBy: { currentPriceUsd: 'asc' },
        include: {
          priceHistory: {
            orderBy: { recordedAt: 'asc' },
          },
        },
      },
    },
  })

  if (!figure) {
    return Response.json({ error: 'Not found' }, { status: 404 })
  }

  return Response.json(figure)
}
