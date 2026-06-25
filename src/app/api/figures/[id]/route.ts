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
        where: { currentPriceUsd: { lte: 2000 } },
        orderBy: { currentPriceUsd: 'asc' },
        include: {
          priceHistory: { orderBy: { recordedAt: 'asc' } },
        },
      },
      duplicates: {
        include: {
          listings: {
            where: { currentPriceUsd: { lte: 2000 } },
            orderBy: { currentPriceUsd: 'asc' },
            include: {
              priceHistory: { orderBy: { recordedAt: 'asc' } },
            },
          },
        },
      },
    },
  })

  if (!figure) {
    return Response.json({ error: 'Not found' }, { status: 404 })
  }

  // Redirect duplicate figures to their canonical URL
  if (figure.canonicalFigureId) {
    return Response.redirect(`/api/figures/${figure.canonicalFigureId}`, 308)
  }

  const listings = [
    ...figure.listings,
    ...figure.duplicates.flatMap((d) => d.listings),
  ].sort((a, b) => Number(a.currentPriceUsd) - Number(b.currentPriceUsd))

  const { duplicates: _d, listings: _l, ...figureData } = figure
  return Response.json({ ...figureData, listings })
}
