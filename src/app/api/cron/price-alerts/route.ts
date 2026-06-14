import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'
import { sendPriceAlert } from '@/lib/email'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'

export async function POST(req: NextRequest) {
  const authHeader = req.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const entries = await prisma.watchlist.findMany({
    where: { targetPriceUsd: { not: null } },
    include: {
      user: { select: { email: true } },
      figure: {
        include: {
          listings: {
            where: { currentPriceUsd: { lte: 5000 }, inStock: true },
            orderBy: { currentPriceUsd: 'asc' },
            take: 1,
          },
        },
      },
    },
  })

  let sent = 0
  for (const entry of entries) {
    const cheapest = entry.figure.listings[0]
    if (!cheapest) continue

    const currentPrice = Number(cheapest.currentPriceUsd)
    const targetPrice = Number(entry.targetPriceUsd)

    if (currentPrice <= targetPrice) {
      await sendPriceAlert({
        to: entry.user.email,
        figureName: entry.figure.name,
        currentPrice,
        targetPrice,
        figureUrl: `${SITE_URL}/figure/${entry.figureId}`,
      })
      sent++
    }
  }

  return Response.json({ checked: entries.length, sent })
}
