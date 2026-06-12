const STATIC_LISTINGS = [
  {
    retailer: "AmiAmi",
    country: "JP",
    priceUsd: 72.0,
    shippingUsd: 18.5,
    inStock: true,
    url: "#",
  },
  {
    retailer: "BigBadToyStore",
    country: "US",
    priceUsd: 89.99,
    shippingUsd: 0,
    inStock: true,
    url: "#",
  },
  {
    retailer: "HobbyLink Japan",
    country: "JP",
    priceUsd: 74.5,
    shippingUsd: 16.0,
    inStock: false,
    url: "#",
  },
];

export default function FigureDetailPage() {
  const sorted = [...STATIC_LISTINGS].sort(
    (a, b) => a.priceUsd + a.shippingUsd - (b.priceUsd + b.shippingUsd)
  );

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="flex gap-8 mb-10">
        <div className="w-40 h-40 rounded-xl bg-zinc-800 flex items-center justify-center text-5xl shrink-0">
          🗿
        </div>
        <div>
          <div className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">
            Good Smile Company · Scale Figure · 1/7
          </div>
          <h1 className="text-3xl font-bold mb-2">Miku Hatsune 1/7 Scale</h1>
          <div className="flex gap-2 flex-wrap">
            <span className="bg-green-900/50 text-green-400 border border-green-800 text-xs px-2 py-1 rounded-full font-medium">
              Buy Now
            </span>
            <span className="text-xs text-zinc-500 self-center">
              ML prediction: price likely rising · 74% confidence
            </span>
          </div>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
          Price comparison
        </h2>
        <div className="grid gap-3">
          {sorted.map((listing, i) => {
            const total = listing.priceUsd + listing.shippingUsd;
            return (
              <a
                key={listing.retailer}
                href={listing.url}
                className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${
                  listing.inStock
                    ? "bg-zinc-900 border-zinc-800 hover:border-zinc-600"
                    : "bg-zinc-900/50 border-zinc-800/50 opacity-60 cursor-default"
                }`}
              >
                {i === 0 && listing.inStock && (
                  <span className="text-xs font-medium bg-green-900/60 text-green-400 border border-green-800 px-2 py-0.5 rounded-full shrink-0">
                    Best price
                  </span>
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{listing.retailer}</div>
                  <div className="text-xs text-zinc-500 mt-0.5">
                    ${listing.priceUsd.toFixed(2)} base ·{" "}
                    {listing.shippingUsd === 0
                      ? "Free shipping"
                      : `$${listing.shippingUsd.toFixed(2)} shipping`}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-lg font-semibold">
                    ${total.toFixed(2)}
                  </div>
                  <div className="text-xs text-zinc-500">landed</div>
                  {!listing.inStock && (
                    <div className="text-xs text-red-400">Out of stock</div>
                  )}
                </div>
              </a>
            );
          })}
        </div>
      </section>

      <section className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider">
            Price history
          </h2>
          <span className="text-xs text-zinc-600">Last 90 days</span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl h-48 flex items-center justify-center text-zinc-600 text-sm">
          Chart renders here once data is collected (Phase 3)
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
          Shipping calculator
        </h2>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Your zip code"
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-500"
            />
            <select className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-500">
              <option>Standard</option>
              <option>EMS</option>
              <option>DHL</option>
            </select>
            <button className="bg-zinc-100 text-zinc-900 font-medium px-4 py-2.5 rounded-lg text-sm hover:bg-white transition-colors">
              Calculate
            </button>
          </div>
          <p className="text-xs text-zinc-600 mt-3">
            Shipping estimate is based on EMS/DHL zone tables and estimated
            figure weight (~300g standard figure).
          </p>
        </div>
      </section>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-center gap-4">
        <div className="flex-1">
          <div className="font-medium text-sm">Add to watchlist</div>
          <div className="text-xs text-zinc-500 mt-0.5">
            Set a target price and get an email alert when the landed cost
            drops below it.
          </div>
        </div>
        <button className="bg-zinc-100 text-zinc-900 font-medium px-4 py-2 rounded-lg text-sm hover:bg-white transition-colors shrink-0">
          Watch
        </button>
      </div>
    </div>
  );
}
