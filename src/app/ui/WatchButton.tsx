'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

type Props = {
  figureId: number
  initialWatching: boolean
  initialEntryId: number | null
  initialTarget: number | null
  isLoggedIn: boolean
}

export default function WatchButton({
  figureId,
  initialWatching,
  initialEntryId,
  initialTarget,
  isLoggedIn,
}: Props) {
  const router = useRouter()
  const [watching, setWatching] = useState(initialWatching)
  const [entryId, setEntryId] = useState(initialEntryId)
  const [target, setTarget] = useState(initialTarget?.toString() ?? '')
  const [showInput, setShowInput] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleWatch() {
    if (!isLoggedIn) {
      router.push('/login')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const body: { figureId: number; targetPriceUsd?: number } = { figureId }
      const parsed = parseFloat(target)
      if (!isNaN(parsed) && parsed > 0) body.targetPriceUsd = parsed

      const res = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error('Failed to add to watchlist')
      const data = await res.json()
      setEntryId(data.id)
      setWatching(true)
      setShowInput(false)
    } catch {
      setError('Something went wrong. Try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleUnwatch() {
    if (!entryId) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/watchlist/${entryId}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to remove from watchlist')
      setWatching(false)
      setEntryId(null)
    } catch {
      setError('Something went wrong. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-start gap-4">
      <div className="flex-1">
        <div className="font-medium text-sm">
          {watching ? 'Watching this figure' : 'Add to watchlist'}
        </div>
        <div className="text-xs text-zinc-500 mt-0.5">
          {watching
            ? target
              ? `Alert when price drops to $${parseFloat(target).toFixed(2)}`
              : 'No target price set — tracking price changes'
            : 'Set a target price and get an email alert when the landed cost drops below it.'}
        </div>
        {error && <p className="text-xs text-red-400 mt-1">{error}</p>}

        {showInput && !watching && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm text-zinc-400">$</span>
            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="Target price (optional)"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500 w-44"
            />
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2 shrink-0">
        {watching ? (
          <button
            onClick={handleUnwatch}
            disabled={loading}
            className="bg-zinc-800 text-zinc-300 font-medium px-4 py-2 rounded-lg text-sm hover:bg-zinc-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Removing…' : 'Unwatch'}
          </button>
        ) : showInput ? (
          <div className="flex gap-2">
            <button
              onClick={() => setShowInput(false)}
              className="text-sm text-zinc-500 hover:text-zinc-300 px-2"
            >
              Cancel
            </button>
            <button
              onClick={handleWatch}
              disabled={loading}
              className="bg-zinc-100 text-zinc-900 font-medium px-4 py-2 rounded-lg text-sm hover:bg-white transition-colors disabled:opacity-50"
            >
              {loading ? 'Adding…' : 'Confirm'}
            </button>
          </div>
        ) : (
          <button
            onClick={() => {
              if (!isLoggedIn) { router.push('/login'); return }
              setShowInput(true)
            }}
            className="bg-zinc-100 text-zinc-900 font-medium px-4 py-2 rounded-lg text-sm hover:bg-white transition-colors"
          >
            Watch
          </button>
        )}
      </div>
    </div>
  )
}
