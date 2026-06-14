import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const origin = searchParams.get('origin') ?? 'JP'
  const zone = parseInt(searchParams.get('zone') ?? '1')
  const method = searchParams.get('method') ?? 'EMS'
  const weight = parseInt(searchParams.get('weight') ?? '300')

  const rate = await prisma.shippingRate.findFirst({
    where: {
      originCountry: origin,
      destinationZone: zone,
      method,
      weightGrams: { gte: weight },
    },
    orderBy: { weightGrams: 'asc' },
  })

  return Response.json({
    rateUsd: rate ? Number(rate.rateUsd) : 0,
    origin,
    zone,
    method,
    weight: rate?.weightGrams ?? weight,
    found: !!rate,
  })
}
