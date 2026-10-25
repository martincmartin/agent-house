// The list prices, from agent-house's user/claude/prices.json, which the CLI
// status line reads too, and how they differ from the pricing page.

import type { PriceChange, PriceDiff } from '../types'

// Where prices.json is, from the plugin's folder.
export const PRICES_PATH = '../../user/claude/prices.json'

// A model's list prices, in USD for a million tokens.
export interface Prices {
  readonly input: number
  readonly cacheWrite5m: number
  readonly cacheWrite1h: number
  readonly cacheRead: number
  readonly output: number
}

// The list prices of each model, by its id. A response from a model that is
// not here, or in fast mode, is not split: its cost shows as "other".
export type PriceList = ReadonlyMap<string, Prices>

// Each price's key in prices.json, with its field in Prices.
const KEYS: readonly (readonly [string, keyof Prices])[] = [
  ['input', 'input'],
  ['cache_write_5m', 'cacheWrite5m'],
  ['cache_write_1h', 'cacheWrite1h'],
  ['cache_read', 'cacheRead'],
  ['output', 'output'],
]

type Fields = Readonly<Record<string, unknown>>

function isFields(value: unknown): value is Fields {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function pricesOf(fields: unknown, where: string): Prices {
  if (!isFields(fields)) throw new Error(`${where} is not an object`)
  const price = (key: string): number => {
    const value = fields[key]
    if (typeof value !== 'number') throw new Error(`${where}.${key} is not a number`)
    return value
  }
  return {
    input: price('input'),
    cacheWrite5m: price('cache_write_5m'),
    cacheWrite1h: price('cache_write_1h'),
    cacheRead: price('cache_read'),
    output: price('output'),
  }
}

// The price list in `models`, an object of each model's prices with the keys
// of prices.json. Throws an error that names what is wrong.
export function modelsOf(models: unknown, where = 'models'): PriceList {
  if (!isFields(models)) throw new Error(`${where} is not an object`)
  return new Map(
    Object.entries(models).map(([model, prices]) => [model, pricesOf(prices, `${where}.${model}`)]),
  )
}

// The price list in the text of prices.json.
export function parsePrices(text: string): PriceList {
  const data: unknown = JSON.parse(text)
  if (!isFields(data)) throw new Error('prices.json is not an object')
  return modelsOf(data['models'], 'prices.json: models')
}

// The price list as an object with the keys of prices.json, for JSON.
export function modelsJson(models: PriceList): Record<string, Record<string, number>> {
  return Object.fromEntries(
    [...models].map(([model, prices]) => [
      model,
      Object.fromEntries(KEYS.map(([key, field]) => [key, prices[field]])),
    ]),
  )
}

// The text of prices.json for `models`, read from `source` on `updated`
// (YYYY-MM-DD): one model on each line, so that a change is one line of a
// diff.
export function pricesJson(models: PriceList, source: string, updated: string): string {
  const lines = Object.entries(modelsJson(models)).map(([model, prices]) => {
    const fields = Object.entries(prices).map(([key, value]) => `${JSON.stringify(key)}: ${value}`)
    return `    ${JSON.stringify(model)}: {${fields.join(', ')}}`
  })
  return [
    '{',
    `  "source": ${JSON.stringify(source)},`,
    `  "updated": ${JSON.stringify(updated)},`,
    '  "unit": "USD for a million tokens",',
    '  "models": {',
    lines.join(',\n'),
    '  }',
    '}',
    '',
  ].join('\n')
}

// How the price list `file` differs from the price list `page`.
export function priceDiff(file: PriceList, page: PriceList): PriceDiff {
  const changed: PriceChange[] = []
  for (const [model, filePrices] of file) {
    const pagePrices = page.get(model)
    if (pagePrices === undefined) continue
    for (const [key, field] of KEYS) {
      if (filePrices[field] !== pagePrices[field]) {
        changed.push({ model, price: key, file: filePrices[field], page: pagePrices[field] })
      }
    }
  }
  return {
    added: [...page.keys()].filter(model => !file.has(model)),
    removed: [...file.keys()].filter(model => !page.has(model)),
    changed,
  }
}

export function isCurrent(diff: PriceDiff): boolean {
  return diff.added.length === 0 && diff.removed.length === 0 && diff.changed.length === 0
}

// What `diff` says, in parts: "claude-sonnet-5-5 cache_read 0.2 → 0.1",
// "new claude-opus-6", "gone claude-opus-4".
export function diffParts(diff: PriceDiff): string[] {
  return [
    ...diff.changed.map(change => `${change.model} ${change.price} ${change.file} → ${change.page}`),
    ...diff.added.map(model => `new ${model}`),
    ...diff.removed.map(model => `gone ${model}`),
  ]
}
