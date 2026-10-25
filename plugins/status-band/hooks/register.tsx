import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { View } from '../types'
import { ALERT, addCosts, compactWindowOf, costParts, gauges, NO_COSTS, svgBar, WARN } from './gauges.ts'
import { pagePrices } from './price-check.ts'
import { diffParts, isCurrent, parsePrices, priceDiff, PRICES_PATH } from './prices.ts'
import { cacheOf, newTranscriptState, readTranscript, transcriptPaths } from './transcript.ts'
import type { TranscriptState } from './transcript.ts'

// The prompt cache, the context, the 5-hour and 7-day rate limits and the
// session's cost, with bars, in the band above the prompt. VS Code only: the CLI has
// agent-house's status line (user/claude/statusline.py).

// The countdowns show minutes, so a refresh each 10 s keeps them right.
const REFRESH_MS = 10_000
const BAR_WIDTH = 120
const BAR_HEIGHT = 6

const EMPTY_VIEW: View = {
  usage: null,
  compactWindow: null,
  cache: null,
  costs: null,
  prices: null,
  priceCheckError: null,
  error: null,
}
const view = atom({ plugin: 'status-band', key: 'view' } as const, EMPTY_VIEW, { shape: 'view-3' })

// One session's side table, made new by each session.start. `refreshes`
// runs one refresh at a time, so that two reads of a transcript do not
// count its lines twice.
interface Session {
  readonly transcript: string
  readonly settings: string
  readonly transcripts: Map<string, TranscriptState>
  refreshes: Promise<void>
}

async function readSettings($: EngineInterface, path: string): Promise<unknown> {
  try {
    return JSON.parse(await $.fs.read(path))
  } catch {
    return null
  }
}

async function refresh($: EngineInterface, session: Session): Promise<void> {
  try {
    const usage = await $.session.usage()
    const prices = parsePrices(await $.fs.read(`${$.plugin.root}/${PRICES_PATH}`))
    for (const path of await transcriptPaths($, session.transcript)) {
      const before = session.transcripts.get(path) ?? newTranscriptState()
      session.transcripts.set(path, await readTranscript($, path, before, prices))
    }
    const costs = [...session.transcripts.values()].reduce(
      (sum, transcript) => addCosts(sum, transcript.costs),
      NO_COSTS,
    )
    const main = session.transcripts.get(session.transcript)
    const model = main?.lastModel ?? null
    const compactWindow =
      model === null ? null : compactWindowOf(await readSettings($, session.settings), model)
    const cache = main === undefined ? null : cacheOf(main)
    const page = await pagePrices($, await $.clock.now())
    await update($, view, () => ({
      usage,
      compactWindow,
      cache,
      costs,
      prices: page.models === null ? null : priceDiff(prices, page.models),
      priceCheckError: page.error,
      error: null,
    }))
  } catch (error) {
    await update($, view, last => ({ ...last, error: String(error) }))
  }
}

function schedule($: EngineInterface, session: Session): void {
  session.refreshes = session.refreshes.then(() => refresh($, session))
}

export const register: Register = on => {
  let session: Session | null = null

  on('session.start', async ($, e, next) => {
    const home = (await $.env.get('HOME')) ?? ''
    const config = (await $.env.get('CLAUDE_CONFIG_DIR')) ?? `${home}/.claude`
    // Claude Code keeps a session's transcript under its directory, with each
    // character that is not a letter or a digit as "-".
    const project = (await $.session.cwd()).replace(/[^A-Za-z0-9]/g, '-')
    const started: Session = {
      transcript: `${config}/projects/${project}/${await $.session.id()}.jsonl`,
      settings: `${config}/settings.json`,
      transcripts: new Map(),
      refreshes: Promise.resolve(),
    }
    session = started
    $.clock.every(REFRESH_MS, () => {
      schedule($, started)
    })
    schedule($, started)
    return next(e)
  })

  on('session.measure', ($, e, next) => {
    if (session !== null) schedule($, session)
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || e.surface !== 'vscode') return next(e)
    const { usage, compactWindow, cache, costs, prices, priceCheckError, error } = await read($, view)
    const { Box, Text, Svg } = $.ui.resolve(e)
    if (usage === null) {
      return error === null ? next(e) : <Text dimColor>status-band: {error}</Text>
    }
    const now = (await $.clock.now()) / 1000
    const total = usage.cost?.usd
    return (
      <Box flexDirection="column">
        <Box flexDirection="row" gap={3}>
          {gauges(usage, compactWindow, cache, now).map(gauge => (
            <Box flexDirection="column">
              <Text tabular>
                {gauge.label}
                <Text {...(gauge.colour === null ? { dimColor: true } : { color: gauge.colour })}>
                  {gauge.value}
                </Text>
                {gauge.isAhead && <Text color={ALERT.text}>▲</Text>}
                <Text dimColor>{gauge.detail}</Text>
              </Text>
              <Svg
                source={svgBar(gauge.segments, BAR_WIDTH, BAR_HEIGHT)}
                alt={`${gauge.label}${gauge.value}${gauge.detail}`}
                width={BAR_WIDTH}
                height={BAR_HEIGHT}
              />
            </Box>
          ))}
        </Box>
        {total !== undefined && (
          <Text tabular>
            ${total.toFixed(2)}
            {costs !== null &&
              costParts(total, costs).map((part, index) => (
                <Text>
                  <Text dimColor>{index === 0 ? ' = ' : ' · '}</Text>
                  {part.name} {part.usd.toFixed(2)}
                </Text>
              ))}
          </Text>
        )}
        {prices !== null && !isCurrent(prices) && (
          <Text color={WARN.text}>
            prices.json differs from the pricing page: {diffParts(prices).join(' · ')} (run
            tools/update-prices.ts)
          </Text>
        )}
        {priceCheckError !== null && (
          <Text dimColor>status-band: could not read the pricing page: {priceCheckError}</Text>
        )}
        {error !== null && <Text dimColor>status-band: {error}</Text>}
      </Box>
    )
  })
}
