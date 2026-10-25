// Reads the list prices from Anthropic's pricing page, in its Markdown form.
// The band checks prices.json against it each day, and
// tools/update-prices.ts writes prices.json from it.

import type { PriceList, Prices } from './prices.ts'

export const PRICING_PAGE = 'https://platform.claude.com/docs/en/about-claude/pricing.md'

// The heading of each price's column in the page's table of model prices.
const HEADINGS: Readonly<Record<keyof Prices, string>> = {
  input: 'Base input tokens',
  cacheWrite5m: '5m cache writes',
  cacheWrite1h: '1h cache writes',
  cacheRead: 'Cache hits and refreshes',
  output: 'Output tokens',
}

function cells(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map(cell => cell.trim())
}

// A model's id from its name on the page: "Claude Opus 5.5" is
// claude-opus-5-5.
function modelId(name: string): string {
  return name.toLowerCase().replace(/[ .]+/g, '-')
}

function priceIn(cell: string, model: string, heading: string): number {
  const match = /^\$\s*([0-9]+(?:\.[0-9]+)?)\s*\/\s*MTok/.exec(cell)
  if (match?.[1] === undefined) {
    throw new Error(`the pricing page's ${heading} of ${model} is not "$N / MTok": ${cell}`)
  }
  return Number(match[1])
}

// The prices in the page's table of model prices. A row's notes in
// parentheses, such as "(retired, …)", are dropped. A model with tiers ("for
// prompts up to 100,000 tokens") is left out: prices.json has one price of
// each kind. Throws an error that names what is wrong, so that a change to
// the page stops a read, not the costs.
export function parsePricingPage(markdown: string): PriceList {
  const lines = markdown.split('\n')
  const start = lines.findIndex(line => {
    const headings = cells(line)
    return headings[0] === 'Model' && Object.values(HEADINGS).every(heading => headings.includes(heading))
  })
  if (start < 0) throw new Error('the pricing page has no table of model prices with the columns that it had')
  const headings = cells(lines[start] ?? '')
  const models = new Map<string, Prices>()
  for (const line of lines.slice(start + 2)) {
    if (!line.trim().startsWith('|')) break
    const row = cells(line)
    const named = (row[0] ?? '').replace(/\[[^\]]*\]\([^)]*\)/g, '')
    const match = /^(Claude [^(]+?)\s*(?:\((.*)\))?$/.exec(named)
    if (match?.[1] === undefined) throw new Error(`the pricing page has a row that names no model: ${line}`)
    if (/prompts/.test(match[2] ?? '')) continue
    const id = modelId(match[1])
    if (models.has(id)) throw new Error(`the pricing page has two rows for ${id}`)
    const price = (field: keyof Prices): number =>
      priceIn(row[headings.indexOf(HEADINGS[field])] ?? '', id, HEADINGS[field])
    models.set(id, {
      input: price('input'),
      cacheWrite5m: price('cacheWrite5m'),
      cacheWrite1h: price('cacheWrite1h'),
      cacheRead: price('cacheRead'),
      output: price('output'),
    })
  }
  if (models.size === 0) throw new Error('the pricing page has no model prices in its table')
  return models
}
