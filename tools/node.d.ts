// The parts of Node's API that tools/update-prices.ts uses. The repo has no
// npm dependencies, so it declares them here, not with @types/node.

declare module 'node:fs/promises' {
  export function readFile(path: string, encoding: 'utf8'): Promise<string>
  export function writeFile(path: string, data: string): Promise<void>
}

declare module 'node:url' {
  export function fileURLToPath(url: URL): string
}

declare class URL {
  constructor(url: string, base?: string)
}

interface ImportMeta {
  readonly url: string
  readonly main: boolean
}

declare const process: { readonly argv: readonly string[]; exitCode: number | undefined }

declare const console: {
  log(...data: unknown[]): void
  error(...data: unknown[]): void
}

declare function fetch(
  url: string,
): Promise<{ readonly ok: boolean; readonly status: number; text(): Promise<string> }>
