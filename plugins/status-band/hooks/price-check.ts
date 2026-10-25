// Reads Anthropic's pricing page at most once a day, for all sessions, so
// that the band can say when prices.json is out of date. $.store keeps the
// last read across sessions.

import type { EngineInterface } from 'claude-code'

import { parsePricingPage, PRICING_PAGE } from './pricing-page.ts'
import { modelsJson, modelsOf } from './prices.ts'
import type { PriceList } from './prices.ts'

const STORE_KEY = 'pricingPage'
// A read is good for a day. After a failed read, the next try waits an hour.
const DAY_MS = 86_400_000
const RETRY_MS = 3_600_000

// The last read of the page: when it last succeeded and when it was last
// tried, in $.clock.now()'s milliseconds, its prices (null before the first
// success), and the last try's failure (null after a success).
export interface PageRead {
  readonly readAt: number
  readonly triedAt: number
  readonly models: PriceList | null
  readonly error: string | null
}

const NO_READ: PageRead = { readAt: 0, triedAt: 0, models: null, error: null }

// The read that $.store holds; NO_READ if it holds none, or one that an
// earlier version wrote in another shape.
export function storedRead(value: unknown): PageRead {
  if (typeof value !== 'object' || value === null) return NO_READ
  const { readAt, triedAt, models, error } = value as Record<string, unknown>
  if (typeof readAt !== 'number' || typeof triedAt !== 'number') return NO_READ
  try {
    return {
      readAt,
      triedAt,
      models: models === null ? null : modelsOf(models),
      error: typeof error === 'string' ? error : null,
    }
  } catch {
    return NO_READ
  }
}

// Whether the page should be read again at `now`.
export function isDue(read: PageRead, now: number): boolean {
  if (now - read.triedAt < RETRY_MS) return false
  return read.models === null || now - read.readAt >= DAY_MS
}

// The prices on the pricing page: the stored read, or a new one when it is
// due. A failed read keeps the last prices, and says why it failed.
export async function pagePrices($: EngineInterface, now: number): Promise<PageRead> {
  const stored = storedRead(await $.store.get(STORE_KEY))
  if (!isDue(stored, now)) return stored
  let read: PageRead
  try {
    const response = await $.http.fetch(PRICING_PAGE)
    if (!response.ok) throw new Error(`${PRICING_PAGE}: HTTP ${response.status}`)
    read = { readAt: now, triedAt: now, models: parsePricingPage(response.text), error: null }
  } catch (error) {
    read = { ...stored, triedAt: now, error: String(error) }
  }
  await $.store.set(STORE_KEY, {
    readAt: read.readAt,
    triedAt: read.triedAt,
    models: read.models === null ? null : modelsJson(read.models),
    error: read.error,
  })
  return read
}
