// Reads the session's transcripts as they grow: what their responses cost,
// and when the cache goes cold. Each read starts where the last one stopped, with
// `tail -c`: $.fs.read refuses a file over 4 MiB, and $.process.run cuts its
// output at 4 MiB, so a long transcript comes in parts.

import type { EngineInterface } from 'claude-code'

import type { Cache, Costs } from '../types'
import { addCosts, cacheTtlOf, costOf, NO_COSTS, responseOf } from './gauges.ts'
import type { PriceList } from './prices.ts'

// The bytes of output that $.process.run keeps (its isStdoutTruncated).
export const OUTPUT_LIMIT = 4194304

// How far a transcript is read: the bytes of its complete lines. While
// `isSkipping`, the line at `offset` is longer than OUTPUT_LIMIT, and the
// read drops it.
export interface Cursor {
  offset: number
  isSkipping: boolean
}

// The complete lines in `text`, the output of a read from `cursor.offset`,
// and `cursor` moved past them. A line still being written stays for the
// next read.
export function takeLines(cursor: Cursor, text: string, isTruncated: boolean): string[] {
  const end = text.lastIndexOf('\n')
  if (end < 0) {
    if (isTruncated) {
      cursor.offset += OUTPUT_LIMIT
      cursor.isSkipping = true
    }
    return []
  }
  const complete = text.slice(0, end + 1)
  cursor.offset += new TextEncoder().encode(complete).length
  const lines = complete.split('\n').slice(0, -1)
  if (cursor.isSkipping) {
    cursor.isSkipping = false
    return lines.slice(1)
  }
  return lines
}

// What one transcript's responses tell so far: their cost, and the model of
// the last one, when it was written (epoch seconds) and the lifetime of the
// cache entries that the last writer wrote. A response that the transcript
// splits into entries repeats its usage in each, so only its first entry
// counts.
export interface TranscriptState {
  readonly cursor: Cursor
  readonly seen: Set<string>
  costs: Costs
  lastModel: string | null
  lastWrittenAt: number | null
  cacheTtl: number | null
}

export function newTranscriptState(): TranscriptState {
  return {
    cursor: { offset: 0, isSkipping: false },
    seen: new Set(),
    costs: NO_COSTS,
    lastModel: null,
    lastWrittenAt: null,
    cacheTtl: null,
  }
}

export function addLines(
  transcript: TranscriptState,
  lines: readonly string[],
  prices: PriceList,
): void {
  for (const line of lines) {
    const response = responseOf(line)
    if (response === null || transcript.seen.has(response.id)) continue
    transcript.seen.add(response.id)
    transcript.lastModel = response.model
    transcript.lastWrittenAt = response.writtenAt ?? transcript.lastWrittenAt
    transcript.cacheTtl = cacheTtlOf(response) ?? transcript.cacheTtl
    const cost = costOf(response, prices)
    if (cost !== null) transcript.costs = addCosts(transcript.costs, cost)
  }
}

// One conversation: its main transcript, and what was read so far from it and
// from its subagents' transcripts, by path. A /clear or a resume starts a new
// conversation in the same process, under a new session id, with no new
// session.start.
export interface Conversation {
  readonly main: string
  readonly transcripts: Map<string, TranscriptState>
}

// The conversation whose main transcript is at `main`: `last` if it is the
// same one, else a new one with nothing read.
export function conversationAt(last: Conversation | null, main: string): Conversation {
  return last?.main === main ? last : { main, transcripts: new Map() }
}

// The cache that the transcript's last response refreshed; null until a
// response wrote to it.
export function cacheOf(transcript: TranscriptState): Cache | null {
  const { lastWrittenAt, cacheTtl } = transcript
  return lastWrittenAt === null || cacheTtl === null
    ? null
    : { expiresAt: lastWrittenAt + cacheTtl, ttl: cacheTtl }
}

// Reads what was added to the file at `path` since the last read, and adds
// it to `transcript`, at `prices`. A file that shrank was written again: it is read from
// the start.
export async function readTranscript(
  $: EngineInterface,
  path: string,
  transcript: TranscriptState,
  prices: PriceList,
): Promise<TranscriptState> {
  const { size } = await $.fs.stat(path)
  const current = size < transcript.cursor.offset ? newTranscriptState() : transcript
  while (size > current.cursor.offset) {
    const run = await $.process.run(['tail', '-c', `+${current.cursor.offset + 1}`, path])
    if (run.exitCode !== 0) {
      throw new Error(`tail exited with ${run.exitCode} on ${path}: ${run.stderr.trim()}`)
    }
    addLines(current, takeLines(current.cursor, run.stdout, run.isStdoutTruncated), prices)
    if (!run.isStdoutTruncated) break
  }
  return current
}

// The session's transcript, and its subagents' transcripts beside it.
export async function transcriptPaths($: EngineInterface, main: string): Promise<string[]> {
  const subagents = `${main.replace(/\.jsonl$/, '')}/subagents`
  const entries = (await $.fs.exists(subagents)) ? await $.fs.list(subagents) : []
  const paths = entries
    .filter(entry => entry.kind === 'file' && entry.name.endsWith('.jsonl'))
    .map(entry => `${subagents}/${entry.name}`)
  return [main, ...paths.sort()]
}
