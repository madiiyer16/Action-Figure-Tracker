import SearchSection from './ui/SearchSection'

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>
}) {
  const { q = '' } = await searchParams

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3 tracking-tight">
          Find the best price.{' '}
          <span className="text-zinc-400">Including shipping.</span>
        </h1>
        <p className="text-zinc-400 text-lg">
          Compare total landed cost across AmiAmi, BBTS, HLJ, and more — with
          ML-powered buy/wait predictions.
        </p>
      </div>

      <SearchSection initialQ={q} />

      <p className="text-center text-xs text-zinc-600 mt-8">
        Prices shown are base price before shipping. Add your zip code on the
        figure page to see landed cost.
      </p>
    </div>
  )
}
