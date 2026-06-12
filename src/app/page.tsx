const FEATURED_FIGURES = [
  {
    id: 1,
    name: "Miku Hatsune 1/7 Scale",
    brand: "Good Smile Company",
    category: "Scale Figure",
    lowestPriceUsd: 89.99,
    retailer: "AmiAmi",
    inStock: true,
    imageUrl: null,
  },
  {
    id: 2,
    name: "Nendoroid Naruto Uzumaki",
    brand: "Good Smile Company",
    category: "Nendoroid",
    lowestPriceUsd: 54.99,
    retailer: "BBTS",
    inStock: true,
    imageUrl: null,
  },
  {
    id: 3,
    name: "RG Nu Gundam",
    brand: "Bandai",
    category: "Gunpla",
    lowestPriceUsd: 34.99,
    retailer: "HLJ",
    inStock: false,
    imageUrl: null,
  },
];

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3 tracking-tight">
          Find the best price.{" "}
          <span className="text-zinc-400">Including shipping.</span>
        </h1>
        <p className="text-zinc-400 text-lg">
          Compare total landed cost across AmiAmi, BBTS, HLJ, and more — with
          ML-powered buy/wait predictions.
        </p>
      </div>

      <form className="flex gap-3 mb-12">
        <input
          type="search"
          name="q"
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

      <section>
        <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-4">
          Featured figures
        </h2>
        <div className="grid gap-4">
          {FEATURED_FIGURES.map((figure) => (
            <a
              key={figure.id}
              href={`/figure/${figure.id}`}
              className="flex items-center gap-4 bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-600 transition-colors"
            >
              <div className="w-16 h-16 rounded-lg bg-zinc-800 flex items-center justify-center text-2xl shrink-0">
                🗿
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{figure.name}</div>
                <div className="text-sm text-zinc-400">
                  {figure.brand} · {figure.category}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className="font-semibold">
                  ${figure.lowestPriceUsd.toFixed(2)}
                </div>
                <div className="text-xs text-zinc-500">{figure.retailer}</div>
                {!figure.inStock && (
                  <div className="text-xs text-red-400 mt-0.5">
                    Out of stock
                  </div>
                )}
              </div>
            </a>
          ))}
        </div>
      </section>

      <p className="text-center text-xs text-zinc-600 mt-8">
        Prices shown are base price before shipping. Shipped costs calculated on
        figure detail page.
      </p>
    </div>
  );
}
