import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'
import { getSession } from '@/lib/session'

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getSession()
  if (!session) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const { id } = await params
  const entryId = parseInt(id)
  if (isNaN(entryId)) return Response.json({ error: 'Invalid id' }, { status: 400 })

  const entry = await prisma.watchlist.findUnique({ where: { id: entryId } })
  if (!entry) return Response.json({ error: 'Not found' }, { status: 404 })
  if (entry.userId !== session.userId) return Response.json({ error: 'Forbidden' }, { status: 403 })

  await prisma.watchlist.delete({ where: { id: entryId } })
  return new Response(null, { status: 204 })
}
