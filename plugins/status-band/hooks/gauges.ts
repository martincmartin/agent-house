// The band's rules, with no input or output: the gauges' levels and pace,
// their text and bars, and the cost of each response. Ported from agent-house's
// user/claude/statusline.py; its legend is the statusline-legend skill.

import type { Cache, Costs, Usage } from '../types'
import type { PriceList } from './prices.ts'

const FIVE_HOURS = 5 * 3600
const SEVEN_DAYS = 7 * 86400

// The numbers that a user can tune.
export interface Config {
  // A rate-limit window is ahead of pace when its use is ahead of the part of
  // the window that has passed, and more than this percentage. The floor
  // hides the mark early in a window, when a few requests are ahead of the
  // short time that has passed.
  readonly paceMinUsed: number
  // A window that is ahead of pace is yellow: at its average rate so far, it
  // runs out before it resets. It is red when it runs out within this part of
  // the window: 0.1 is 30 minutes of 5 hours, or 17 hours of 7 days.
  readonly alertWithin: number
  // Seconds: in its last seconds, the prompt cache turns yellow.
  readonly cacheWarning: number
}

export const DEFAULT_CONFIG: Config = { paceMinUsed: 10, alertWithin: 0.1, cacheWarning: 300 }

// How much a gauge needs attention: the colour of its text, and of its bar,
// solid and shaded (greyer). Hex, because VS Code does not draw every theme
// key (`warning` drew grey on 2026-10-25).
export interface Level {
  readonly text: string
  readonly solid: string
  readonly shade: string
}

export const OK: Level = { text: '#2da44e', solid: '#3fb950', shade: '#93c9a0' }
export const WARN: Level = { text: '#bf8700', solid: '#d29922', shade: '#cdb27a' }
export const ALERT: Level = { text: '#cf222e', solid: '#f85149', shade: '#d9938f' }
// The empty part of a bar: grey at part opacity, for light and dark themes.
const TRACK = '#80808060'

// A part of a bar, filled from the end of the part before it to `end`, a
// fraction of the bar.
export interface Segment {
  readonly end: number
  readonly colour: string
}

// A gauge: "5h 64%▲ ↻2h05m" over a bar. `value` is in its level's colour,
// or dim when `colour` is null; `isAhead` adds the mark; `detail` is dim.
export interface Gauge {
  readonly label: string
  readonly value: string
  readonly colour: string | null
  readonly isAhead: boolean
  readonly detail: string
  readonly segments: readonly Segment[]
}

function clamp(fraction: number): number {
  return Math.min(Math.max(fraction, 0), 1)
}

// OK below half of `limit`, WARN below 80%, ALERT from 80%.
export function levelOf(value: number, limit: number): Level {
  if (value * 100 >= limit * 80) return ALERT
  if (value * 2 >= limit) return WARN
  return OK
}

// A token count as 412k or 1M.
export function tokens(count: number): string {
  if (count >= 1_000_000 && count % 1_000_000 === 0) return `${count / 1_000_000}M`
  return `${Math.floor((count + 500) / 1000)}k`
}

// The time from `now` until `moment`, in epoch seconds: 3d4h, 2h05m or 12m.
export function until(moment: number, now: number): string {
  const left = Math.max(moment - now, 0)
  const days = Math.floor(left / 86400)
  const hours = Math.floor((left % 86400) / 3600)
  const minutes = Math.floor((left % 3600) / 60)
  if (days > 0) return `${days}d${hours}h`
  if (hours > 0) return `${hours}h${String(minutes).padStart(2, '0')}m`
  return `${minutes}m`
}

// The prompt cache: the time until it goes cold, over a bar of the part of
// its lifetime that has passed; "cold", with a full bar, when it has expired.
// `now` is in epoch seconds.
export function cacheGauge(cache: Cache, now: number, config: Config = DEFAULT_CONFIG): Gauge {
  const left = cache.expiresAt - now
  if (left <= 0) {
    return {
      label: 'cache ',
      value: 'cold',
      colour: ALERT.text,
      isAhead: false,
      detail: '',
      segments: [{ end: 1, colour: ALERT.solid }],
    }
  }
  const level = left < config.cacheWarning ? WARN : OK
  return {
    label: 'cache ',
    value: until(cache.expiresAt, now),
    colour: level.text,
    isAhead: false,
    detail: '',
    segments: [{ end: 1 - left / cache.ttl, colour: level.solid }],
  }
}

// The context's tokens, against the smaller of the context window and the
// model's autoCompactWindow.
export function contextGauge(context: Usage['context'], compactWindow: number | null): Gauge {
  const limit = compactWindow === null ? context.window : Math.min(context.window, compactWindow)
  if (context.tokens === undefined || context.tokens === 0) {
    // 0 is not known: the context always holds the system prompt.
    return { label: 'ctx ', value: '?', colour: null, isAhead: false, detail: '', segments: [] }
  }
  const level = levelOf(context.tokens, limit)
  return {
    label: 'ctx ',
    value: tokens(context.tokens),
    colour: level.text,
    isAhead: false,
    detail: `/${tokens(limit)}`,
    segments: [{ end: context.tokens / limit, colour: level.solid }],
  }
}

// The model's autoCompactWindow in settings.json (modelSettings), for its id
// without a "[1m]" suffix; null if it is not set.
export function compactWindowOf(settings: unknown, modelId: string): number | null {
  const modelSettings = isFields(settings) ? settings['modelSettings'] : undefined
  const model = isFields(modelSettings) ? modelSettings[modelId.split('[')[0] ?? ''] : undefined
  const window = isFields(model) ? model['autoCompactWindow'] : undefined
  return typeof window === 'number' && Number.isInteger(window) && window > 0 ? window : null
}

// The part of the window that has passed, from 0 to 1.
function passedPart(resetsAt: number, length: number, now: number): number {
  return 1 - Math.min(Math.max(resetsAt - now, 0), length) / length
}

// OK on or behind pace, WARN ahead of it, ALERT when it runs out soon.
// Without a reset time, the level of the use alone.
function windowLevel(percentUsed: number, passed: number | null, config: Config): Level {
  if (passed === null) return levelOf(Math.round(percentUsed), 100)
  const used = percentUsed / 100
  if (percentUsed <= config.paceMinUsed || used <= passed) return OK
  // At the average rate so far, the part of the window until it runs out.
  const runsOutIn = ((1 - used) * passed) / used
  return runsOutIn < config.alertWithin ? ALERT : WARN
}

// A rate-limit window, over a bar of its use and of the part of the window
// that has passed. The bar is solid to the lower of the two, and shaded
// between them. `now` is in epoch seconds.
function windowGauge(
  label: string,
  length: number,
  limit: Usage['rateLimits'][number],
  now: number,
  config: Config,
): Gauge {
  const resetsAt = limit.resetsAt === undefined ? null : Date.parse(limit.resetsAt) / 1000
  const passed = resetsAt === null ? null : passedPart(resetsAt, length, now)
  const level = windowLevel(limit.percentUsed, passed, config)
  const used = limit.percentUsed / 100
  return {
    label,
    value: `${limit.percentUsed}%`,
    colour: level.text,
    isAhead: passed !== null && level !== OK,
    detail: resetsAt === null ? '' : ` ↻${until(resetsAt, now)}`,
    segments:
      passed === null
        ? [{ end: used, colour: level.solid }]
        : [
            { end: Math.min(used, passed), colour: level.solid },
            { end: Math.max(used, passed), colour: level.shade },
          ],
  }
}

const WINDOWS: readonly { readonly kind: string; readonly label: string; readonly length: number }[] = [
  { kind: 'five_hour', label: '5h ', length: FIVE_HOURS },
  { kind: 'seven_day', label: '7d ', length: SEVEN_DAYS },
]

// The cache's gauge when a response wrote to it, the context's, then the
// 5-hour and the 7-day window's when the usage has them. `now` is in epoch
// seconds.
export function gauges(
  usage: Usage,
  compactWindow: number | null,
  cache: Cache | null,
  now: number,
  config: Config = DEFAULT_CONFIG,
): Gauge[] {
  const windows = WINDOWS.flatMap(window => {
    const limit = usage.rateLimits.find(rateLimit => rateLimit.kind === window.kind)
    return limit === undefined ? [] : [windowGauge(window.label, window.length, limit, now, config)]
  })
  const caches = cache === null ? [] : [cacheGauge(cache, now, config)]
  return [...caches, contextGauge(usage.context, compactWindow), ...windows]
}

function round(value: number): string {
  return value.toFixed(1).replace(/\.0$/, '')
}

// An SVG bar of `width` by `height` CSS pixels, with round ends. The
// segments' ends must not decrease; after the last end, the track.
export function svgBar(segments: readonly Segment[], width: number, height: number): string {
  let start = 0
  const rects = segments.map(segment => {
    const left = clamp(start) * width
    const right = clamp(segment.end) * width
    start = Math.max(start, segment.end)
    return right > left
      ? `<rect x="${round(left)}" width="${round(right - left)}" height="${height}" fill="${segment.colour}"/>`
      : ''
  })
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">` +
    `<clipPath id="bar"><rect width="${width}" height="${height}" rx="${height / 2}"/></clipPath>` +
    `<g clip-path="url(#bar)"><rect width="${width}" height="${height}" fill="${TRACK}"/>` +
    `${rects.join('')}</g></svg>`
  )
}

export const NO_COSTS: Costs = { input: 0, cacheWrite: 0, cacheRead: 0, output: 0, thinking: 0 }

export function totalOf(costs: Costs): number {
  return costs.input + costs.cacheWrite + costs.cacheRead + costs.output + costs.thinking
}

export function addCosts(first: Costs, second: Costs): Costs {
  return {
    input: first.input + second.input,
    cacheWrite: first.cacheWrite + second.cacheWrite,
    cacheRead: first.cacheRead + second.cacheRead,
    output: first.output + second.output,
    thinking: first.thinking + second.thinking,
  }
}

type Fields = Readonly<Record<string, unknown>>

function isFields(value: unknown): value is Fields {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function count(fields: Fields | undefined, key: string): number {
  const value = fields?.[key]
  return typeof value === 'number' ? value : 0
}

// One response in a transcript: the API's message id, its model and usage,
// and when Claude Code wrote it, in epoch seconds (null if not known).
export interface Response {
  readonly id: string
  readonly model: string
  readonly usage: Fields
  readonly writtenAt: number | null
}

const CACHE_TTLS: readonly { readonly key: string; readonly seconds: number }[] = [
  { key: 'ephemeral_1h_input_tokens', seconds: 3600 },
  { key: 'ephemeral_5m_input_tokens', seconds: 300 },
]

// The lifetime of the cache entries that a response wrote, in seconds; null
// if it wrote none.
export function cacheTtlOf(response: Response): number | null {
  const creation = response.usage['cache_creation']
  const written = isFields(creation) ? creation : undefined
  return CACHE_TTLS.find(ttl => count(written, ttl.key) > 0)?.seconds ?? null
}

// The response in a transcript's line, or null for any other line. A line
// that does not parse is one that Claude Code is still writing.
export function responseOf(line: string): Response | null {
  let entry: unknown
  try {
    entry = JSON.parse(line)
  } catch {
    return null
  }
  if (!isFields(entry) || entry['type'] !== 'assistant') return null
  const message = entry['message']
  if (!isFields(message)) return null
  const { id, model, usage } = message
  if (typeof id !== 'string' || !isFields(usage)) return null
  const timestamp = entry['timestamp']
  const written = typeof timestamp === 'string' ? Date.parse(timestamp) / 1000 : Number.NaN
  return {
    id,
    model: typeof model === 'string' ? model : '',
    usage,
    writtenAt: Number.isNaN(written) ? null : written,
  }
}

// What a response cost, at `prices`; null for a model that is not there, or
// a response in fast mode.
export function costOf(response: Response, prices: PriceList): Costs | null {
  const price = prices.models.get(response.model)
  const speed = response.usage['speed']
  if (price === undefined || (speed !== undefined && speed !== null && speed !== 'standard')) {
    return null
  }
  const { usage } = response
  const creation = usage['cache_creation']
  const details = usage['output_tokens_details']
  const written1h = count(isFields(creation) ? creation : undefined, 'ephemeral_1h_input_tokens')
  const written5m = count(usage, 'cache_creation_input_tokens') - written1h
  const thought = count(isFields(details) ? details : undefined, 'thinking_tokens')
  return {
    input: (count(usage, 'input_tokens') * price.input) / 1e6,
    cacheWrite: ((written5m * prices.write5m + written1h * prices.write1h) * price.input) / 1e6,
    cacheRead: (count(usage, 'cache_read_input_tokens') * price.cacheRead) / 1e6,
    output: ((count(usage, 'output_tokens') - thought) * price.output) / 1e6,
    thinking: (thought * price.output) / 1e6,
  }
}

// A part of the session's cost, in USD.
export interface CostPart {
  readonly name: string
  readonly usd: number
}

// What the session's cost was spent on, in the CLI line's order. "other" is
// the part of Claude Code's total that the transcripts do not explain. A part
// under half a cent is left out.
export function costParts(totalUsd: number, costs: Costs): CostPart[] {
  const parts: CostPart[] = [
    { name: 'in', usd: costs.input },
    { name: 'read', usd: costs.cacheRead },
    { name: 'write', usd: costs.cacheWrite },
    { name: 'out', usd: costs.output },
    { name: 'think', usd: costs.thinking },
    { name: 'other', usd: totalUsd - totalOf(costs) },
  ]
  return parts.filter(part => part.usd >= 0.005)
}
