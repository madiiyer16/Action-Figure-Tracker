import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get('q')?.trim() ?? ''
  const limit = Math.min(parseInt(request.nextUrl.searchParams.get('limit') ?? '20'), 50)

  const figures = await prisma.figure.findMany({
    where: q
      ? {
          OR: [
            { name: { contains: q, mode: 'insensitive' } },
            { brand: { contains: q, mode: 'insensitive' } },
            { category: { contains: q, mode: 'insensitive' } },
          ],
        }
      : {},
    include: {
      listings: {
        where: { currentPriceUsd: { lte: 2000 } },
        orderBy: { currentPriceUsd: 'asc' },
        take: 1,
      },
    },
    orderBy: q ? { name: 'asc' } : { createdAt: 'desc' },
    take: limit,
  })

  return Response.json(figures)
}
