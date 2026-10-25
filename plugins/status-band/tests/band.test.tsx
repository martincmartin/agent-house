import { expect, test } from 'claude-code/testing'

import type { View } from '../types'
import {
  ALERT,
  cacheGauge,
  cacheTtlOf,
  compactWindowOf,
  contextGauge,
  costOf,
  costParts,
  gauges,
  NO_COSTS,
  OK,
  responseOf,
  svgBar,
  tokens,
  until,
  WARN,
} from '../hooks/gauges.ts'
import { parsePrices } from '../hooks/prices.ts'
import { addLines, cacheOf, newTranscriptState, OUTPUT_LIMIT, takeLines } from '../hooks/transcript.ts'

// 2026-10-25T14:00:00Z, in epoch seconds.
const NOW = 1792936800

// The prices of user/claude/prices.json on 2026-10-25. A test cannot read a
// file, so the sums below use this copy.
const PRICES = parsePrices(
  JSON.stringify({
    cache_write_5m: 1.25,
    cache_write_1h: 2.0,
    models: {
      'claude-opus-5-5': { input: 4.0, output: 20.0, cache_read: 0.2 },
      'claude-sonnet-5-5': { input: 2.0, output: 10.0, cache_read: 0.2 },
    },
  }),
)

function assistant(
  id: string,
  usage: object,
  model = 'claude-opus-5-5',
  timestamp = '2026-10-25T14:00:00.000Z',
): string {
  return JSON.stringify({ type: 'assistant', timestamp, message: { id, model, usage } })
}

test('a token count is in thousands, or whole millions', () => {
  expect(tokens(164_400)).toBe('164k')
  expect(tokens(164_500)).toBe('165k')
  expect(tokens(1_000_000)).toBe('1M')
  expect(tokens(1_500_000)).toBe('1500k')
})

test('a countdown is in days and hours, hours and minutes, or minutes', () => {
  expect(until(NOW + 3 * 86400 + 4 * 3600 + 59, NOW)).toBe('3d4h')
  expect(until(NOW + 2 * 3600 + 5 * 60 + 59, NOW)).toBe('2h05m')
  expect(until(NOW + 12 * 60 + 30, NOW)).toBe('12m')
  expect(until(NOW - 10, NOW)).toBe('0m')
})

test('the context is measured against the smaller of the window and autoCompactWindow', () => {
  const gauge = contextGauge({ tokens: 300_000, window: 1_000_000 }, 500_000)
  expect(gauge.value).toBe('300k')
  expect(gauge.detail).toBe('/500k')
  expect(gauge.colour).toBe(WARN.text)
  expect(gauge.segments).toEqual([{ end: 0.6, colour: WARN.solid }])
  expect(contextGauge({ tokens: 100_000, window: 200_000 }, 500_000).detail).toBe('/200k')
  expect(contextGauge({ tokens: 100_000, window: 1_000_000 }, null).detail).toBe('/1M')
})

test('an unknown context is "?", with an empty bar', () => {
  for (const tokens of [undefined, 0]) {
    const gauge = contextGauge(tokens === undefined ? { window: 1_000_000 } : { tokens, window: 1_000_000 }, null)
    expect(gauge.value).toBe('?')
    expect(gauge.colour).toBeNull()
    expect(gauge.segments).toEqual([])
  }
})

test('a window ahead of pace is marked, with a shade between pace and use', () => {
  // Half of the 5 hours has passed, and 60% is used: it runs out before it
  // resets, but not within a tenth of the window.
  const resetsAt = new Date((NOW + 2.5 * 3600) * 1000).toISOString()
  const usage = {
    context: { window: 1_000_000 },
    rateLimits: [{ kind: 'five_hour', percentUsed: 60, resetsAt }],
  }
  const [, fiveHour] = gauges(usage, null, null, NOW)
  expect(fiveHour?.label).toBe('5h ')
  expect(fiveHour?.value).toBe('60%')
  expect(fiveHour?.colour).toBe(WARN.text)
  expect(fiveHour?.isAhead).toBe(true)
  expect(fiveHour?.detail).toBe(' ↻2h30m')
  expect(fiveHour?.segments).toEqual([
    { end: 0.5, colour: WARN.solid },
    { end: 0.6, colour: WARN.shade },
  ])
})

test('a window that runs out soon is red, and one on pace is green', () => {
  const resetsAt = new Date((NOW + 3 * 86400) * 1000).toISOString()
  const ahead = { kind: 'seven_day', percentUsed: 95, resetsAt }
  const behind = { kind: 'seven_day', percentUsed: 30, resetsAt }
  expect(gauges({ context: { window: 1 }, rateLimits: [ahead] }, null, null, NOW)[1]?.colour).toBe(ALERT.text)
  const onPace = gauges({ context: { window: 1 }, rateLimits: [behind] }, null, null, NOW)[1]
  expect(onPace?.colour).toBe(OK.text)
  expect(onPace?.isAhead).toBe(false)
})

test('a window without a reset time has the level of its use alone', () => {
  const [, sevenDay] = gauges(
    { context: { window: 1 }, rateLimits: [{ kind: 'seven_day', percentUsed: 85.5 }] },
    null,
    null,
    NOW,
  )
  expect(sevenDay?.value).toBe('85.5%')
  expect(sevenDay?.colour).toBe(ALERT.text)
  expect(sevenDay?.detail).toBe('')
  expect(sevenDay?.segments).toEqual([{ end: 0.855, colour: ALERT.solid }])
})

test('a bar has the track, then each segment from the end of the one before', () => {
  const svg = svgBar(
    [
      { end: 0.25, colour: '#111' },
      { end: 0.5, colour: '#222' },
    ],
    120,
    6,
  )
  expect(svg).toMatch(/<rect width="120" height="6" fill="#80808060"\/>/)
  expect(svg).toMatch(/<rect x="0" width="30" height="6" fill="#111"\/>/)
  expect(svg).toMatch(/<rect x="30" width="30" height="6" fill="#222"\/>/)
})

test('the cache is the time until it goes cold, over the part of its lifetime that has passed', () => {
  const fresh = cacheGauge({ expiresAt: NOW + 2700, ttl: 3600 }, NOW)
  expect(fresh.label + fresh.value).toBe('cache 45m')
  expect(fresh.colour).toBe(OK.text)
  expect(fresh.segments).toEqual([{ end: 0.25, colour: OK.solid }])
  expect(cacheGauge({ expiresAt: NOW + 299, ttl: 3600 }, NOW).colour).toBe(WARN.text)
})

test('an expired cache is "cold", with a full red bar', () => {
  const cold = cacheGauge({ expiresAt: NOW, ttl: 300 }, NOW)
  expect(cold.label + cold.value).toBe('cache cold')
  expect(cold.colour).toBe(ALERT.text)
  expect(cold.segments).toEqual([{ end: 1, colour: ALERT.solid }])
})

test("the cache's lifetime is that of the entries a response wrote", () => {
  const ttlOf = (creation: object): number | null => {
    const response = responseOf(assistant('a', { cache_creation: creation }))
    return response === null ? null : cacheTtlOf(response)
  }
  expect(ttlOf({ ephemeral_1h_input_tokens: 10, ephemeral_5m_input_tokens: 0 })).toBe(3600)
  expect(ttlOf({ ephemeral_1h_input_tokens: 0, ephemeral_5m_input_tokens: 10 })).toBe(300)
  expect(ttlOf({ ephemeral_1h_input_tokens: 0, ephemeral_5m_input_tokens: 0 })).toBeNull()
})

test('the cache goes cold a lifetime after the last response, which may only read it', () => {
  const transcript = newTranscriptState()
  expect(cacheOf(transcript)).toBeNull()
  addLines(transcript, [
    assistant('a', { cache_creation: { ephemeral_1h_input_tokens: 10 } }, 'claude-opus-5-5', '2026-10-25T14:00:00.000Z'),
    assistant('b', { cache_read_input_tokens: 10 }, 'claude-opus-5-5', '2026-10-25T14:10:00.000Z'),
  ], PRICES)
  expect(cacheOf(transcript)).toEqual({ expiresAt: NOW + 600 + 3600, ttl: 3600 })
})

test('autoCompactWindow is read for the model id without its suffix', () => {
  const settings = { modelSettings: { 'claude-opus-5-5': { autoCompactWindow: 500000 } } }
  expect(compactWindowOf(settings, 'claude-opus-5-5[1m]')).toBe(500000)
  expect(compactWindowOf(settings, 'claude-sonnet-5-5')).toBeNull()
  expect(compactWindowOf(null, 'claude-opus-5-5')).toBeNull()
})

test('a response costs its tokens at list prices, with thinking and 1-hour writes apart', () => {
  const response = responseOf(
    assistant('a', {
      input_tokens: 1_000_000,
      cache_creation_input_tokens: 3_000_000,
      cache_creation: { ephemeral_1h_input_tokens: 1_000_000 },
      cache_read_input_tokens: 10_000_000,
      output_tokens: 1_000_000,
      output_tokens_details: { thinking_tokens: 250_000 },
    }),
  )
  expect(response === null ? null : costOf(response, PRICES)).toEqual({
    input: 4,
    // 2M at 1.25 times $4, and 1M at 2 times $4.
    cacheWrite: 18,
    cacheRead: 2,
    output: 15,
    thinking: 5,
  })
})

test('a response of a model without prices, or in fast mode, has no cost', () => {
  const unknown = responseOf(assistant('a', { output_tokens: 10 }, 'claude-haiku-5-5'))
  const fast = responseOf(assistant('b', { output_tokens: 10, speed: 'fast' }))
  expect(unknown === null ? undefined : costOf(unknown, PRICES)).toBeNull()
  expect(fast === null ? undefined : costOf(fast, PRICES)).toBeNull()
})

test('a price list that is not in the shape of prices.json is refused, with what is wrong', () => {
  expect(() => parsePrices('[]')).toThrow('prices.json: not an object')
  expect(() => parsePrices('{"models": {"m": {"input": 1}}}')).toThrow('models.m.output is not a number')
  expect(() => parsePrices('{"models": {}, "cache_write_5m": 1.25}')).toThrow('prices.cache_write_1h')
})

test('only an assistant line with an id and a usage is a response', () => {
  expect(responseOf('{"type":"user","message":{}}')).toBeNull()
  expect(responseOf('{"type":"assistant","message":{"id":"a"}}')).toBeNull()
  expect(responseOf('{"type":"assistant","mess')).toBeNull()
})

test('a response that the transcript splits into entries counts once', () => {
  const transcript = newTranscriptState()
  const line = assistant('a', { output_tokens: 1_000_000 })
  addLines(transcript, [line, line], PRICES)
  expect(transcript.costs).toEqual({ ...NO_COSTS, output: 20 })
  expect(transcript.lastModel).toBe('claude-opus-5-5')
})

test('a read keeps a line still being written for the next read', () => {
  const cursor = { offset: 10, isSkipping: false }
  expect(takeLines(cursor, 'é1\nab2\npart', false)).toEqual(['é1', 'ab2'])
  // "é" is two bytes in UTF-8.
  expect(cursor.offset).toBe(10 + 8)
  expect(takeLines(cursor, 'part', false)).toEqual([])
  expect(cursor.offset).toBe(18)
})

test('a line longer than the output limit is dropped', () => {
  const cursor = { offset: 0, isSkipping: false }
  expect(takeLines(cursor, 'x'.repeat(100), true)).toEqual([])
  expect(cursor).toEqual({ offset: OUTPUT_LIMIT, isSkipping: true })
  expect(takeLines(cursor, 'rest of it\nnext\n', false)).toEqual(['next'])
  expect(cursor.isSkipping).toBe(false)
})

test('the cost is split, with "other" for what the transcripts do not explain', () => {
  const costs = { ...NO_COSTS, cacheRead: 1.94, output: 0.61, input: 0.001 }
  const parts = costParts(3, costs)
  expect(parts.map(part => part.name)).toEqual(['read', 'out', 'other'])
  expect(Math.abs((parts[2]?.usd ?? 0) - 0.449) < 1e-9).toBe(true)
})

const VIEW: View = {
  usage: {
    context: { tokens: 164_000, window: 1_000_000 },
    rateLimits: [
      { kind: 'five_hour', percentUsed: 25, resetsAt: new Date((NOW + 3 * 3600) * 1000).toISOString() },
      { kind: 'seven_day', percentUsed: 74, resetsAt: new Date((NOW + 1500) * 1000).toISOString() },
    ],
    cost: { usd: 3.85 },
  },
  compactWindow: 500_000,
  cache: { expiresAt: NOW + 3420, ttl: 3600 },
  costs: { ...NO_COSTS, cacheRead: 1.94, cacheWrite: 0.98, output: 0.61, thinking: 0.22 },
  error: null,
}

const BAND = {
  plugin: 'status-band',
  component: 'AbovePrompt',
  requestId: 'above-prompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 10,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 10 },
    view: {},
  },
} as const

test('the band draws the gauges and the cost on VS Code', async ($, on) => {
  on('state.get', () => ({ value: { value: { shape: 'view-2', value: VIEW }, version: 1 } }))
  on('clock.now', () => ({ value: NOW * 1000 }))

  const ui = await $.ui.mount({ ...BAND, surface: 'vscode' })

  expect((await ui.find({ type: 'Text', text: /^cache 57m$/ }))?.text).toBe('cache 57m')
  expect((await ui.find({ type: 'Text', text: /^ctx 164k\/500k$/ }))?.text).toBe('ctx 164k/500k')
  expect((await ui.find({ type: 'Text', text: /^5h 25% ↻3h00m$/ }))?.text).toBe('5h 25% ↻3h00m')
  expect((await ui.find({ type: 'Text', text: /^7d 74% ↻25m$/ }))?.text).toBe('7d 74% ↻25m')
  expect((await ui.find({ type: 'Text', text: /^\$3\.85 = / }))?.text).toBe(
    '$3.85 = read 1.94 · write 0.98 · out 0.61 · think 0.22 · other 0.10',
  )
  await ui.unmount()
})

test('the band leaves the terminal to the CLI status line', async ($, on) => {
  on('state.get', () => ({ value: { value: { shape: 'view-2', value: VIEW }, version: 1 } }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine</Text>
  })

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })

  expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
  await ui.unmount()
})
