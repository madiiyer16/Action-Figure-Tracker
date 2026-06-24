-- DropIndex
DROP INDEX "listings_figureId_retailer_key";

-- CreateIndex (partial — Prisma does not support partial indexes in schema.prisma;
-- this index is the canonical uniqueness constraint for listings going forward)
CREATE UNIQUE INDEX "listings_retailer_sku_unique"
  ON listings (retailer, "retailerSku")
  WHERE "retailerSku" IS NOT NULL;
