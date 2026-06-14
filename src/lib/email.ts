import 'server-only'
import nodemailer from 'nodemailer'

const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM } = process.env

function createTransport() {
  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS) return null
  return nodemailer.createTransport({
    host: SMTP_HOST,
    port: parseInt(SMTP_PORT ?? '587'),
    secure: parseInt(SMTP_PORT ?? '587') === 465,
    auth: { user: SMTP_USER, pass: SMTP_PASS },
  })
}

export async function sendPriceAlert({
  to,
  figureName,
  currentPrice,
  targetPrice,
  figureUrl,
}: {
  to: string
  figureName: string
  currentPrice: number
  targetPrice: number
  figureUrl: string
}): Promise<void> {
  const transport = createTransport()
  if (!transport) {
    console.log(`[price-alert] SMTP not configured — would have emailed ${to} about ${figureName}`)
    return
  }

  const from = SMTP_FROM ?? `FigureTrack <${SMTP_USER}>`
  await transport.sendMail({
    from,
    to,
    subject: `Price alert: ${figureName} is now $${currentPrice.toFixed(2)}`,
    text: [
      `Good news! ${figureName} has dropped to $${currentPrice.toFixed(2)}, which is at or below your target of $${targetPrice.toFixed(2)}.`,
      '',
      `View it here: ${figureUrl}`,
      '',
      '— FigureTrack',
    ].join('\n'),
    html: `
      <p>Good news! <strong>${figureName}</strong> has dropped to <strong>$${currentPrice.toFixed(2)}</strong>, which is at or below your target of $${targetPrice.toFixed(2)}.</p>
      <p><a href="${figureUrl}">View it on FigureTrack</a></p>
      <p style="color:#888">— FigureTrack</p>
    `,
  })
}
