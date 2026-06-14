import Link from 'next/link'
import { prisma } from '@/lib/prisma'
import { verifySession } from '@/lib/dal'

export default async function WatchlistPage() {
  const session = await verifySession()

  const entries = await prisma.watchlist.findMany({
    where: { userId: session.userId },
    include: {
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
    orderBy: { addedAt: 'desc' },
  })

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-bold mb-1">Your watchlist</h1>
      <p className="text-zinc-500 text-sm mb-8">
        You&apos;ll get an email when a figure&apos;s price drops to or below your target.
      </p>

      {entries.length === 0 ? (
        <div className="text-center py-16 text-zinc-500">
          <div className="text-4xl mb-4">👁</div>
          <p className="text-sm">Nothing here yet.</p>
          <Link href="/" className="text-zinc-300 hover:text-white text-sm mt-2 inline-block">
            Browse figures →
          </Link>
        </div>
      ) : (
        <div className="divide-y divide-zinc-800 border border-zinc-800 rounded-xl overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 px-4 py-2 text-xs font-medium text-zinc-500 uppercase tracking-wider bg-zinc-900">
            <span>Figure</span>
            <span className="text-right">Target</span>
            <span className="text-right">Current price</span>
            <span className="text-right">Status</span>
          </div>

          {entries.map((entry) => {
            const cheapest = entry.figure.listings[0]
            const currentPrice = cheapest ? Number(cheapest.currentPriceUsd) : null
            const target = entry.targetPriceUsd ? Number(entry.targetPriceUsd) : null
            const atTarget = target != null && currentPrice != null && currentPrice <= target

            return (
              <div
                key={entry.id}
                className="grid grid-cols-[1fr_auto_auto_auto] gap-4 px-4 py-4 items-center hover:bg-zinc-900/50 transition-colors"
              >
                <div>
                  <Link
                    href={`/figure/${entry.figureId}`}
                    className="font-medium text-sm hover:text-zinc-300 transition-colors"
                  >
                    {entry.figure.name}
                  </Link>
                  <div className="text-xs text-zinc-600 mt-0.5">
                    {entry.figure.brand} · {entry.figure.category}
                  </div>
                </div>

                <div className="text-right text-sm text-zinc-400">
                  {target != null ? `$${target.toFixed(2)}` : '—'}
                </div>

                <div className={`text-right text-sm font-medium ${atTarget ? 'text-green-400' : 'text-zinc-100'}`}>
                  {currentPrice != null ? `$${currentPrice.toFixed(2)}` : 'Out of stock'}
                </div>

                <div className="text-right">
                  {atTarget ? (
                    <span className="text-xs bg-green-900/50 text-green-400 border border-green-800 rounded-full px-2 py-0.5 font-medium">
                      At target
                    </span>
                  ) : (
                    <span className="text-xs text-zinc-600">Watching</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
