import { PrismaClient } from '../src/generated/prisma/client'

const prisma = new PrismaClient()

const WEIGHTS = [300, 500, 750, 1000, 1500, 2000]
const ZONES   = [1, 2, 3, 4, 5]

// Japan Post EMS rates (USD) indexed by zone, one per weight tier
const JP_EMS: Record<number, number[]> = {
  1: [17.80, 20.65, 24.95, 28.75, 36.85, 44.50],
  2: [21.50, 25.00, 30.20, 34.80, 44.70, 53.85],
  3: [24.90, 28.90, 34.90, 40.20, 51.70, 62.30],
  4: [27.30, 31.70, 38.30, 44.10, 56.70, 68.25],
  5: [29.80, 34.60, 41.80, 48.15, 61.90, 74.50],
}

// Japan Post SAL rates (USD)
const JP_SAL: Record<number, number[]> = {
  1: [ 9.50, 11.80, 14.20, 16.90, 21.80, 26.30],
  2: [11.50, 14.20, 17.20, 20.40, 26.30, 31.80],
  3: [13.30, 16.40, 19.90, 23.60, 30.40, 36.80],
  4: [14.60, 18.00, 21.80, 25.90, 33.30, 40.30],
  5: [15.90, 19.60, 23.80, 28.20, 36.30, 43.90],
}

// US domestic standard (BBTS) — same rate regardless of zone
const US_STANDARD = [6.99, 8.99, 10.99, 12.99, 15.99, 18.99]

async function main() {
  const rows: {
    originCountry: string
    destinationZone: number
    weightGrams: number
    method: string
    rateUsd: number
  }[] = []

  for (const zone of ZONES) {
    for (let i = 0; i < WEIGHTS.length; i++) {
      rows.push({ originCountry: 'JP', destinationZone: zone, weightGrams: WEIGHTS[i], method: 'EMS', rateUsd: JP_EMS[zone][i] })
      rows.push({ originCountry: 'JP', destinationZone: zone, weightGrams: WEIGHTS[i], method: 'SAL', rateUsd: JP_SAL[zone][i] })
      rows.push({ originCountry: 'US', destinationZone: zone, weightGrams: WEIGHTS[i], method: 'standard', rateUsd: US_STANDARD[i] })
    }
  }

  const result = await prisma.shippingRate.createMany({ data: rows, skipDuplicates: true })
  console.log(`Inserted ${result.count} shipping rate rows (skipped existing)`)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(() => prisma.$disconnect())
