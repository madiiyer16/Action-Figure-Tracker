-- CreateTable
CREATE TABLE "figures" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "brand" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "scale" TEXT,
    "releaseDate" TIMESTAMP(3),
    "originalMsrpJpy" INTEGER,
    "originalMsrpUsd" DECIMAL(10,2),
    "imageUrl" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "figures_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "listings" (
    "id" SERIAL NOT NULL,
    "figureId" INTEGER NOT NULL,
    "retailer" TEXT NOT NULL,
    "retailerUrl" TEXT NOT NULL,
    "currentPriceUsd" DECIMAL(10,2) NOT NULL,
    "inStock" BOOLEAN NOT NULL DEFAULT true,
    "lastScrapedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "listings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "price_history" (
    "id" SERIAL NOT NULL,
    "listingId" INTEGER NOT NULL,
    "priceUsd" DECIMAL(10,2) NOT NULL,
    "inStock" BOOLEAN NOT NULL,
    "recordedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "price_history_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "shipping_rates" (
    "id" SERIAL NOT NULL,
    "originCountry" TEXT NOT NULL,
    "destinationZone" INTEGER NOT NULL,
    "weightGrams" INTEGER NOT NULL,
    "method" TEXT NOT NULL,
    "rateUsd" DECIMAL(10,2) NOT NULL,

    CONSTRAINT "shipping_rates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "users" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "zipCode" TEXT,
    "country" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "watchlist" (
    "id" SERIAL NOT NULL,
    "userId" INTEGER NOT NULL,
    "figureId" INTEGER NOT NULL,
    "targetPriceUsd" DECIMAL(10,2),
    "addedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "watchlist_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "price_predictions" (
    "id" SERIAL NOT NULL,
    "figureId" INTEGER NOT NULL,
    "predictionScore" DECIMAL(5,4) NOT NULL,
    "recommendation" TEXT NOT NULL,
    "confidence" DECIMAL(5,4) NOT NULL,
    "predictedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modelVersion" TEXT NOT NULL,

    CONSTRAINT "price_predictions_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "shipping_rates_originCountry_destinationZone_weightGrams_me_key" ON "shipping_rates"("originCountry", "destinationZone", "weightGrams", "method");

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "watchlist_userId_figureId_key" ON "watchlist"("userId", "figureId");

-- AddForeignKey
ALTER TABLE "listings" ADD CONSTRAINT "listings_figureId_fkey" FOREIGN KEY ("figureId") REFERENCES "figures"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "price_history" ADD CONSTRAINT "price_history_listingId_fkey" FOREIGN KEY ("listingId") REFERENCES "listings"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "watchlist" ADD CONSTRAINT "watchlist_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "watchlist" ADD CONSTRAINT "watchlist_figureId_fkey" FOREIGN KEY ("figureId") REFERENCES "figures"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "price_predictions" ADD CONSTRAINT "price_predictions_figureId_fkey" FOREIGN KEY ("figureId") REFERENCES "figures"("id") ON DELETE CASCADE ON UPDATE CASCADE;
