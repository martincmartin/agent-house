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

// A price that prices.json and the pricing page give differently, in USD
// for a million tokens. `price` is its key in prices.json.
export interface PriceChange {
  readonly model: string
  readonly price: string
  readonly file: number
  readonly page: number
}

// How prices.json differs from Anthropic's pricing page: the models that
// only the page has, those that only the file has, and the changed prices.
export interface PriceDiff {
  readonly added: readonly string[]
  readonly removed: readonly string[]
  readonly changed: readonly PriceChange[]
}

// What the band draws. `compactWindow` is the model's autoCompactWindow in
// settings.json, or null; `cache` is null until a response wrote to the
// cache; `prices` is null until the pricing page was read; `priceCheckError`
// is the last read's failure, and `error` the last refresh's, or null.
export interface View {
  readonly usage: Usage | null
  readonly compactWindow: number | null
  readonly cache: Cache | null
  readonly costs: Costs | null
  readonly prices: PriceDiff | null
  readonly priceCheckError: string | null
  readonly error: string | null
}

declare module 'claude-code' {
  interface PluginState {
    'status-band': { view: Shaped<View> }
  }
}
