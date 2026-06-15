'use client'

import { useState } from 'react'
import { zipToZone } from '@/lib/zipToZone'

export type SerializedListing = {
  id: number
  retailer: string
  retailerUrl: string
  currentPriceUsd: number
  inStock: boolean
}

type ListingWithShipping = SerializedListing & {
  shippingUsd: number
  totalUsd: number
}

function originForRetailer(retailer: string): string {
  const map: Record<string, string> = { amiami: 'JP', bbts: 'US' }
  return map[retailer.toLowerCase()] ?? 'US'
}

function displayName(retailer: string): string {
  const map: Record<string, string> = { amiami: 'AmiAmi', bbts: 'BigBadToyStore' }
  return map[retailer.toLowerCase()] ?? retailer
}

export default function ShippingCalculator({ listings }: { listings: SerializedListing[] }) {
  const [zip, setZip] = useState('')
  const [method, setMethod] = useState('EMS')
  const [withShipping, setWithShipping] = useState<ListingWithShipping[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const baseSorted = [...listings].sort((a, b) => a.currentPriceUsd - b.currentPriceUsd)

  async function calculate(e: React.FormEvent) {
    e.preventDefault()
    if (!/^\d{5}/.test(zip)) {
      setError('Enter a valid 5-digit US zip code')
      return
    }
    setError('')
    setLoading(true)

    try {
      const zone = zipToZone(zip)
      const results = await Promise.all(
        listings.map(async (listing) => {
          const origin = originForRetailer(listing.retailer)
          const m = origin === 'US' ? 'standard' : method
          const res = await fetch(
            `/api/shipping?origin=${origin}&zone=${zone}&method=${m}&weight=300`
          )
          const data = await res.json()
          return {
            ...listing,
            shippingUsd: data.rateUsd as number,
            totalUsd: listing.currentPriceUsd + (data.rateUsd as number),
          }
        })
      )
      setWithShipping(results.sort((a, b) => a.totalUsd - b.totalUsd))
    } finally {
      setLoading(false)
    }
  }

  const displayListings: ListingWithShipping[] = withShipping
    ?? baseSorted.map((l) => ({ ...l, shippingUsd: 0, totalUsd: l.currentPriceUsd }))

  const hasShipping = withShipping !== null

  return (
    <div className="space-y-4">
      <div className="grid gap-3">
        {displayListings.map((listing, i) => {
          const isFirst = i === 0 && listing.inStock
          return (
            <a
              key={listing.id}
              href={listing.retailerUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${
                listing.inStock
                  ? 'bg-zinc-900 border-zinc-800 hover:border-zinc-600'
                  : 'bg-zinc-900/50 border-zinc-800/50 opacity-60 pointer-events-none'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  {isFirst && (
                    <span className="text-xs font-medium bg-green-900/60 text-green-400 border border-green-800 px-2 py-0.5 rounded-full shrink-0">
                      Best price
                    </span>
                  )}
                  <div className="font-medium">{displayName(listing.retailer)}</div>
                </div>
                <div className="text-xs text-zinc-500 mt-0.5">
                  ${listing.currentPriceUsd.toFixed(2)} base
                  {hasShipping && listing.shippingUsd > 0 && (
                    <> + ${listing.shippingUsd.toFixed(2)} shipping</>
                  )}
                  {hasShipping && listing.shippingUsd === 0 && <> + free shipping</>}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className="text-lg font-semibold">
                  ${(hasShipping ? listing.totalUsd : listing.currentPriceUsd).toFixed(2)}
                </div>
                <div className="text-xs text-zinc-500">{hasShipping ? 'landed' : 'base'}</div>
                {!listing.inStock && (
                  <div className="text-xs text-red-400">Out of stock</div>
                )}
              </div>
            </a>
          )
        })}
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <h3 className="text-sm font-medium text-zinc-400 mb-3">Calculate shipping</h3>
        <form onSubmit={calculate} className="flex gap-3">
          <input
            type="text"
            placeholder="US zip code"
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            maxLength={10}
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-500"
          />
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-500"
          >
            <option value="EMS">EMS (fast)</option>
            <option value="SAL">SAL (economy)</option>
          </select>
          <button
            type="submit"
            disabled={loading}
            className="bg-zinc-100 text-zinc-900 font-medium px-4 py-2.5 rounded-lg text-sm hover:bg-white transition-colors disabled:opacity-50"
          >
            {loading ? '…' : 'Calculate'}
          </button>
        </form>
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
        <p className="text-xs text-zinc-600 mt-2">
          Estimates based on Japan Post EMS/SAL zone tables · assumes 300g figure weight
        </p>
      </div>
    </div>
  )
}
