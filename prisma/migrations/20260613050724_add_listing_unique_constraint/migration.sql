/*
  Warnings:

  - A unique constraint covering the columns `[figureId,retailer]` on the table `listings` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "listings_figureId_retailer_key" ON "listings"("figureId", "retailer");
