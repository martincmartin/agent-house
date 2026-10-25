import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, TurnUsage } from 'claude-code'

import type { Usage, View } from '../types'

// A probe, not the status line. It records what the VS Code panel draws and
// what a mod can read, in probe-report.json beside plugin.json, for agent-house's
// tasks/2026-10-25-vscode-status/.

const PANE = 'status-probe'
const TICK_MS = 5000
const BAR_CELLS = 20
const SVG_WIDTH = 160
const SVG_HEIGHT = 10
// Unicode's left eighth blocks, as the CLI status line draws its bars.
const EIGHTHS = ['', '▏', '▎', '▍', '▌', '▋', '▊', '▉']
const FULL = '█'
// A braille blank: an empty cell that a surface does not trim.
const BLANK = '⠀'
const RATE_LABELS: Readonly<Record<string, string>> = { five_hour: '5h', seven_day: '7d' }

const EMPTY_VIEW: View = { usage: null, ticks: 0, measures: 0, lastChanged: [] }
const view = atom({ plugin: 'status-probe', key: 'view' } as const, EMPTY_VIEW, {
  shape: 'view-1',
})

interface Probe {
  readonly name: string
  readonly result: string
}

interface Step {
  readonly agentId: string | null
  readonly model: string
  readonly usage: TurnUsage | null
}

interface Gauge {
  readonly label: string
  readonly text: string
  readonly fraction: number
}

type Level = 'success' | 'warning' | 'error'

const SVG_COLOURS: Readonly<Record<Level, string>> = {
  success: '#3fb950',
  warning: '#d29922',
  error: '#f85149',
}

function level(fraction: number): Level {
  if (fraction >= 0.8) return 'error'
  if (fraction >= 0.5) return 'warning'
  return 'success'
}

function clamp(fraction: number): number {
  return Math.min(Math.max(fraction, 0), 1)
}

function blocks(fraction: number): { readonly filled: string; readonly empty: string } {
  const eighths = Math.round(clamp(fraction) * BAR_CELLS * 8)
  const partial = EIGHTHS[eighths % 8] ?? ''
  const cells = Math.floor(eighths / 8) + (partial === '' ? 0 : 1)
  return {
    filled: FULL.repeat(Math.floor(eighths / 8)) + partial,
    empty: BLANK.repeat(BAR_CELLS - cells),
  }
}

function svgBar(fraction: number): string {
  const filled = (clamp(fraction) * SVG_WIDTH).toFixed(1)
  const colour = SVG_COLOURS[level(fraction)]
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${SVG_WIDTH}" height="${SVG_HEIGHT}">` +
    `<rect width="${SVG_WIDTH}" height="${SVG_HEIGHT}" rx="5" fill="#80808060"/>` +
    `<rect width="${filled}" height="${SVG_HEIGHT}" rx="5" fill="${colour}"/></svg>`
  )
}

function countdown(milliseconds: number): string {
  const seconds = Math.max(0, Math.floor(milliseconds / 1000))
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const rest = seconds % 60
  const clock = `${hours}h${String(minutes).padStart(2, '0')}m${String(rest).padStart(2, '0')}s`
  return days > 0 ? `${days}d${clock}` : clock
}

function gauges(usage: Usage, now: number): Gauge[] {
  const { tokens, window } = usage.context
  const context: Gauge = {
    label: 'ctx',
    text: tokens === undefined ? '?' : `${Math.round(tokens / 1000)}k/${Math.round(window / 1000)}k`,
    fraction: tokens === undefined ? 0 : tokens / window,
  }
  const limits = usage.rateLimits.map(limit => ({
    label: RATE_LABELS[limit.kind] ?? limit.kind,
    text:
      `${limit.percentUsed.toFixed(1)}%` +
      (limit.resetsAt === undefined ? '' : ` ↻${countdown(Date.parse(limit.resetsAt) - now)}`),
    fraction: limit.percentUsed / 100,
  }))
  return [context, ...limits]
}

function sessionSlug(cwd: string): string {
  return cwd.replace(/[^A-Za-z0-9]/g, '-')
}

// What one session's probe found: the session's own side table, made new
// by each register.
interface Findings {
  readonly rendered: Set<string>
  readonly probes: Probe[]
  readonly steps: Step[]
  surfaces: readonly string[]
  current: View
}

async function probe(
  findings: Findings,
  name: string,
  run: () => Promise<string>,
): Promise<string | null> {
  try {
    const result = await run()
    findings.probes.push({ name, result })
    return result
  } catch (error) {
    findings.probes.push({ name, result: `error: ${String(error)}` })
    return null
  }
}

async function show($: EngineInterface, findings: Findings, next: View): Promise<void> {
  findings.current = next
  await update($, view, () => next)
}

async function writeReport($: EngineInterface, findings: Findings): Promise<void> {
  const report = {
    writtenAt: new Date(await $.clock.now()).toISOString(),
    surfaces: findings.surfaces,
    rendered: [...findings.rendered].sort(),
    probes: findings.probes,
    steps: findings.steps.slice(-20),
    view: findings.current,
  }
  await $.fs.write(`${$.plugin.root}/probe-report.json`, `${JSON.stringify(report, null, 2)}\n`)
}

async function tick($: EngineInterface, findings: Findings): Promise<void> {
  findings.surfaces = await $.session.surfaces()
  const { current } = findings
  await show($, findings, { ...current, usage: await $.session.usage(), ticks: current.ticks + 1 })
  $.ui.status(`status-probe: a plugin status line, tick ${findings.current.ticks}`)
  await writeReport($, findings)
}

export const register: Register = on => {
  const findings: Findings = {
    rendered: new Set(),
    probes: [],
    steps: [],
    surfaces: [],
    current: EMPTY_VIEW,
  }

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'probe-pane',
      description: 'Open the status probe pane, to see where the panel places it',
    })
    const cwd = await $.session.cwd()
    const home = (
      await probe(findings, 'process.run printenv HOME', async () => {
        const { exitCode, stdout } = await $.process.run(['printenv', 'HOME'])
        return exitCode === 0 ? stdout.trim() : `exit ${exitCode}`
      })
    )?.trim()
    await probe(findings, 'process.run git branch', async () => {
      const { exitCode, stdout } = await $.process.run(['git', 'branch', '--show-current'])
      return `exit ${exitCode}: ${stdout.trim()}`
    })
    const reads = [
      ['own plugin.json', `${$.plugin.root}/.claude-plugin/plugin.json`],
      ['file in cwd', 'user/claude/statusline.py'],
      ...(home === undefined
        ? []
        : [
            ['settings.json, outside cwd', `${home}/.claude/settings.json`],
            ['transcript', `${home}/.claude/projects/${sessionSlug(cwd)}/${await $.session.id()}.jsonl`],
          ]),
    ] as const
    for (const [name, path] of reads) {
      await probe(findings, `fs.read ${name}`, async () => `ok, ${(await $.fs.read(path)).length} chars: ${path}`)
    }
    // Reading only the bytes after an offset, for a transcript over fs.read's
    // 4 MiB; and what process.run does with more than 4 MiB of output.
    const transcript = reads.find(([name]) => name === 'transcript')?.[1]
    if (transcript !== undefined) {
      await probe(findings, 'process.run tail -c +1000001 transcript', async () => {
        const run = await $.process.run(['tail', '-c', '+1000001', transcript])
        return `exit ${run.exitCode}, ${run.stdout.length} chars, truncated ${String(run.isStdoutTruncated)}`
      })
    }
    await probe(findings, 'process.run head -c 5000000 /dev/zero', async () => {
      const run = await $.process.run(['head', '-c', '5000000', '/dev/zero'])
      return `exit ${run.exitCode}, ${run.stdout.length} chars, truncated ${String(run.isStdoutTruncated)}`
    })
    await probe(findings, 'config.list compact/model/effort', async () => {
      const rows = await $.config.list()
      return JSON.stringify(
        rows
          .filter(row => /compact|model|effort/i.test(row.key))
          .map(row => ({ key: row.key, value: row.value })),
      )
    })
    $.clock.every(TICK_MS, () => {
      tick($, findings).catch((error: unknown) => {
        findings.probes.push({ name: 'tick', result: `error: ${String(error)}` })
      })
    })
    await tick($, findings)
    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    const { current } = findings
    await show($, findings, { ...current, measures: current.measures + 1, lastChanged: e.changed })
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    findings.steps.push({ agentId: e.agentId ?? null, model: e.model, usage: result.usage })
    return result
  })

  on('command.run', { command: 'probe-pane' }, async $ => {
    const opened = await $.ui.open({ id: PANE, title: 'Status probe' })
    return { text: `Status probe pane: ${JSON.stringify(opened)}` }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    findings.rendered.add(`Pane:${e.surface}:${e.props.placement}`)
    const { Text } = $.ui.resolve(e)
    return (
      <Text>
        Status probe pane, on {e.surface}, placed {e.props.placement}
      </Text>
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    findings.rendered.add(`AbovePrompt:${e.surface}`)
    if (e.props.hasSurvey || e.surface !== 'vscode') return next(e)
    const { Box, Text, Svg } = $.ui.resolve(e)
    const { usage, ticks, measures, lastChanged } = await read($, view)
    const now = await $.clock.now()
    return (
      <Box flexDirection="column">
        <Text dimColor>
          status-probe band on {e.surface} · tick {ticks} · measures {measures} (last:{' '}
          {lastChanged.join(', ') || 'none'}) · cost{' '}
          {usage?.cost === undefined ? '?' : `$${usage.cost.usd.toFixed(2)}`}
        </Text>
        {usage !== null &&
          gauges(usage, now).map(gauge => {
            const { filled, empty } = blocks(gauge.fraction)
            return (
              <Box flexDirection="row" gap={1}>
                <Text mono>
                  {gauge.label} {gauge.text}
                </Text>
                <Box flexDirection="row">
                  <Text mono color={level(gauge.fraction)} backgroundColor="inactive">
                    {filled}
                  </Text>
                  <Text mono backgroundColor="inactive">
                    {empty}
                  </Text>
                </Box>
                <Box width={BAR_CELLS} height={1} backgroundColor="inactive">
                  <Box
                    width={`${Math.round(clamp(gauge.fraction) * 100)}%`}
                    height={1}
                    backgroundColor={level(gauge.fraction)}
                  />
                </Box>
                <Svg
                  source={svgBar(gauge.fraction)}
                  alt={`${gauge.label} ${gauge.text}`}
                  width={SVG_WIDTH}
                  height={SVG_HEIGHT}
                />
              </Box>
            )
          })}
      </Box>
    )
  })
}
