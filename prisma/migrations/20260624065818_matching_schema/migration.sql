-- AlterTable
ALTER TABLE "figures" ADD COLUMN     "canonicalFigureId" INTEGER,
ADD COLUMN     "normalizedBrand" TEXT;

-- AlterTable
ALTER TABLE "listings" ADD COLUMN     "editionTokens" TEXT[],
ADD COLUMN     "itemNumber" TEXT,
ADD COLUMN     "normalizedTitle" TEXT,
ADD COLUMN     "scaleParsed" TEXT;

-- CreateTable
CREATE TABLE "match_candidates" (
    "id" SERIAL NOT NULL,
    "figureAId" INTEGER NOT NULL,
    "figureBId" INTEGER NOT NULL,
    "score" DECIMAL(5,4) NOT NULL,
    "method" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "scaleMatch" BOOLEAN,
    "priceMatch" BOOLEAN,
    "reviewedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "match_candidates_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "match_candidates_figureAId_figureBId_key" ON "match_candidates"("figureAId", "figureBId");

-- AddForeignKey
ALTER TABLE "figures" ADD CONSTRAINT "figures_canonicalFigureId_fkey" FOREIGN KEY ("canonicalFigureId") REFERENCES "figures"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match_candidates" ADD CONSTRAINT "match_candidates_figureAId_fkey" FOREIGN KEY ("figureAId") REFERENCES "figures"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match_candidates" ADD CONSTRAINT "match_candidates_figureBId_fkey" FOREIGN KEY ("figureBId") REFERENCES "figures"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
