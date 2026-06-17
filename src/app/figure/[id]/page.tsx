import { notFound } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import PriceChart, { type ChartPoint } from '@/app/ui/PriceChart'
import ShippingCalculator from '@/app/ui/ShippingCalculator'
import WatchButton from '@/app/ui/WatchButton'
import { getOptionalSession } from '@/lib/dal'

type Prediction =
  | { status: 'insufficient_data' }
  | { status: 'ok'; recommendation: 'buy' | 'wait'; confidence: number; change_pct: number }

async function getPrediction(figureId: number): Promise<Prediction> {
  const url = process.env.ML_SERVICE_URL
  if (!url) return { status: 'insufficient_data' }
  try {
    const res = await fetch(`${url}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ figure_id: figureId }),
      signal: AbortSignal.timeout(2000),
      next: { revalidate: 3600 },
    })
    if (!res.ok) return { status: 'insufficient_data' }
    return res.json()
  } catch {
    return { status: 'insufficient_data' }
  }
}

export default async function FigureDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const figureId = parseInt(id)
  if (isNaN(figureId)) notFound()

  const session = await getOptionalSession()

  const [figure, watchEntry, prediction] = await Promise.all([
    prisma.figure.findUnique({
      where: { id: figureId },
      include: {
        listings: {
          where: { currentPriceUsd: { lte: 2000 } },
          orderBy: { currentPriceUsd: 'asc' },
          include: {
            priceHistory: {
              orderBy: { recordedAt: 'asc' },
            },
          },
        },
      },
    }),
    session
      ? prisma.watchlist.findUnique({
          where: { userId_figureId: { userId: session.userId, figureId } },
        })
      : null,
    getPrediction(figureId),
  ])

  if (!figure) notFound()

  // Serialize Prisma Decimal/Date types to plain JS primitives for client props
  const listings = figure.listings.map((l) => ({
    id: l.id,
    retailer: l.retailer,
    retailerUrl: l.retailerUrl,
    currentPriceUsd: Number(l.currentPriceUsd),
    inStock: l.inStock,
    priceHistory: l.priceHistory.map((ph) => ({
      id: ph.id,
      priceUsd: Number(ph.priceUsd),
      inStock: ph.inStock,
      recordedAt: ph.recordedAt.toISOString(),
    })),
  }))

  // Build chart data: daily price points per retailer
  const retailers = listings.map((l) => l.retailer)

  const allDates = Array.from(
    new Set(
      listings.flatMap((l) =>
        l.priceHistory.map((ph) => ph.recordedAt.slice(0, 10))
      )
    )
  ).sort()

  const chartData: ChartPoint[] = allDates.map((date) => {
    const point: ChartPoint = { date }
    for (const listing of listings) {
      const latest = listing.priceHistory
        .filter((ph) => ph.recordedAt.slice(0, 10) <= date)
        .at(-1)
      if (latest) point[listing.retailer] = latest.priceUsd
    }
    return point
  })

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Hero */}
      <div className="flex gap-8 mb-10">
        {figure.imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={figure.imageUrl}
            alt={figure.name}
            className="w-40 h-40 rounded-xl object-cover shrink-0 bg-zinc-800"
          />
        ) : (
          <div className="w-40 h-40 rounded-xl bg-zinc-800 flex items-center justify-center text-5xl shrink-0">
            🗿
          </div>
        )}
        <div>
          <div className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">
            {figure.brand} · {figure.category}
            {figure.scale ? ` · ${figure.scale}` : ''}
          </div>
          <h1 className="text-3xl font-bold mb-2">{figure.name}</h1>
          {prediction.status === 'ok' ? (
            <div className="flex gap-2 flex-wrap">
              <span className={`text-xs px-2 py-1 rounded-full font-medium border ${
                prediction.recommendation === 'buy'
                  ? 'bg-green-900/50 text-green-400 border-green-800'
                  : 'bg-yellow-900/50 text-yellow-400 border-yellow-800'
              }`}>
                {prediction.recommendation === 'buy' ? 'Buy Now' : 'Wait'}
              </span>
              <span className="text-xs text-zinc-500 self-center">
                ML prediction: price likely {prediction.recommendation === 'buy' ? 'rising' : 'falling'} · {Math.round(prediction.confidence * 100)}% confidence
              </span>
            </div>
          ) : (
            <div className="flex gap-2 flex-wrap">
              <span className="bg-zinc-800 text-zinc-400 border border-zinc-700 text-xs px-2 py-1 rounded-full font-medium">
                Collecting data
              </span>
              <span className="text-xs text-zinc-600 self-center">
                ML prediction available after 30 days of price history
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Price comparison + shipping calculator */}
      <section className="mb-8">
        <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
          Price comparison
        </h2>
        {listings.length === 0 ? (
          <div className="text-zinc-500 text-sm text-center py-8">
            No listings available
          </div>
        ) : (
          <ShippingCalculator listings={listings} />
        )}
      </section>

      {/* Price history chart */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider">
            Price history
          </h2>
          <span className="text-xs text-zinc-600">Last 90 days</span>
        </div>
        <PriceChart retailers={retailers} data={chartData} />
      </section>

      {/* Watchlist CTA */}
      <WatchButton
        figureId={figureId}
        initialWatching={!!watchEntry}
        initialEntryId={watchEntry?.id ?? null}
        initialTarget={watchEntry?.targetPriceUsd ? Number(watchEntry.targetPriceUsd) : null}
        isLoggedIn={!!session}
      />
    </div>
  )
}
