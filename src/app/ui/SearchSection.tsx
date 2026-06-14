'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'

type Listing = {
  id: number
  retailer: string
  currentPriceUsd: string | number
  inStock: boolean
}

type Figure = {
  id: number
  name: string
  brand: string
  category: string
  imageUrl: string | null
  listings: Listing[]
}

function retailerLabel(retailer: string): string {
  const map: Record<string, string> = { amiami: 'AmiAmi', bbts: 'BigBadToyStore' }
  return map[retailer.toLowerCase()] ?? retailer
}

export default function SearchSection({ initialQ }: { initialQ: string }) {
  const [query, setQuery] = useState(initialQ)
  const [results, setResults] = useState<Figure[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const search = useCallback(async (q: string) => {
    setLoading(true)
    setSearched(false)
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=20`)
      const data: Figure[] = await res.json()
      setResults(data)
    } finally {
      setLoading(false)
      setSearched(true)
    }
  }, [])

  useEffect(() => {
    search(initialQ)
  }, [initialQ, search])

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    search(query)
  }

  return (
    <>
      <form onSubmit={handleSubmit} className="flex gap-3 mb-12">
        <input
          type="search"
          name="q"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search figures, brands, or categories…"
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-500"
        />
        <button
          type="submit"
          className="bg-zinc-100 text-zinc-900 font-medium px-6 py-3 rounded-lg text-sm hover:bg-white transition-colors"
        >
          Search
        </button>
      </form>

      {loading && (
        <div className="text-center text-zinc-500 text-sm py-12">Searching…</div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="text-center text-zinc-500 text-sm py-12">
          No results{query ? ` for "${query}"` : ''}
        </div>
      )}

      {!loading && results.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-4">
            {query ? `Results for "${query}"` : 'Latest figures'}
          </h2>
          <div className="grid gap-4">
            {results.map((figure) => {
              const listing = figure.listings[0]
              return (
                <Link
                  key={figure.id}
                  href={`/figure/${figure.id}`}
                  className="flex items-center gap-4 bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-600 transition-colors"
                >
                  {figure.imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={figure.imageUrl}
                      alt={figure.name}
                      className="w-16 h-16 rounded-lg object-cover shrink-0 bg-zinc-800"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-lg bg-zinc-800 flex items-center justify-center text-2xl shrink-0">
                      🗿
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{figure.name}</div>
                    <div className="text-sm text-zinc-400">
                      {figure.brand} · {figure.category}
                    </div>
                  </div>
                  {listing && (
                    <div className="text-right shrink-0">
                      <div className="font-semibold">
                        ${parseFloat(String(listing.currentPriceUsd)).toFixed(2)}
                      </div>
                      <div className="text-xs text-zinc-500">
                        {retailerLabel(listing.retailer)}
                      </div>
                      {!listing.inStock && (
                        <div className="text-xs text-red-400 mt-0.5">Out of stock</div>
                      )}
                    </div>
                  )}
                </Link>
              )
            })}
          </div>
        </section>
      )}
    </>
  )
}
