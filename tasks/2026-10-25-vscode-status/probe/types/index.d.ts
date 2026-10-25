// The parts of SessionUsage that the band draws. The contract must not import
// from 'claude-code', so it declares them; SessionUsage is assignable to it.
export interface Usage {
  readonly context: { readonly tokens?: number; readonly window: number }
  readonly rateLimits: readonly {
    readonly kind: string
    readonly percentUsed: number
    readonly resetsAt?: string
  }[]
  readonly cost?: { readonly usd: number }
}

// What the band draws: the last usage that a tick read, and the measurements.
export interface View {
  readonly usage: Usage | null
  readonly ticks: number
  readonly measures: number
  readonly lastChanged: readonly ('context' | 'rateLimits' | 'cost')[]
}

declare module 'claude-code' {
  interface PluginState {
    'status-probe': { view: Shaped<View> }
  }
}
