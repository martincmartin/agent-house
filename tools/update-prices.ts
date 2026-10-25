#!/usr/bin/env node
// Write user/claude/prices.json from Anthropic's pricing page, and print what
// changed; print nothing when the file is current. Usage:
// tools/update-prices.ts
//
// The status band and the CLI status line read the file
// (docs/statusline.md). The band says when the page differs from it.

import { readFile, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

import { parsePricingPage, PRICING_PAGE } from '../plugins/status-band/hooks/pricing-page.ts'
import { diffParts, isCurrent, parsePrices, priceDiff, pricesJson } from '../plugins/status-band/hooks/prices.ts'

const PRICES_FILE = fileURLToPath(new URL('../user/claude/prices.json', import.meta.url))

async function main(): Promise<void> {
  if (process.argv.length !== 2) {
    console.error('usage: tools/update-prices.ts')
    process.exitCode = 2
    return
  }
  const response = await fetch(PRICING_PAGE)
  if (!response.ok) throw new Error(`${PRICING_PAGE}: HTTP ${response.status}`)
  const page = parsePricingPage(await response.text())
  const diff = priceDiff(parsePrices(await readFile(PRICES_FILE, 'utf8')), page)
  if (isCurrent(diff)) return
  await writeFile(PRICES_FILE, pricesJson(page, PRICING_PAGE, new Date().toISOString().slice(0, 10)))
  for (const part of diffParts(diff)) console.log(part)
}

if (import.meta.main) await main()
