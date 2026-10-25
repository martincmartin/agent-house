// The parts of $.session.usage() that the band draws. The contract must not
// import from 'claude-code', so it declares them; SessionUsage is assignable.
export interface Usage {
  readonly context: { readonly tokens?: number; readonly window: number }
  readonly rateLimits: readonly {
    readonly kind: string
    readonly percentUsed: number
    readonly resetsAt?: string
  }[]
  readonly cost?: { readonly usd: number }
}

// What the session's responses cost, in USD, at list prices. Thinking is
// output, but apart from `output`.
export interface Costs {
  readonly input: number
  readonly cacheWrite: number
  readonly cacheRead: number
  readonly output: number
  readonly thinking: number
}

// The main conversation's prompt cache: when it goes cold, and its lifetime,
// in seconds.
export interface Cache {
  readonly expiresAt: number
  readonly ttl: number
}

// What the band draws. `compactWindow` is the model's autoCompactWindow in
// settings.json, or null; `cache` is null until a response wrote to the
// cache; `error` is the last refresh's failure, or null.
export interface View {
  readonly usage: Usage | null
  readonly compactWindow: number | null
  readonly cache: Cache | null
  readonly costs: Costs | null
  readonly error: string | null
}

declare module 'claude-code' {
  interface PluginState {
    'status-band': { view: Shaped<View> }
  }
}
