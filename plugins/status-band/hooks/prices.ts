// The list prices, from agent-house's user/claude/prices.json, which the CLI
// status line reads too.

// Where prices.json is, from the plugin's folder.
export const PRICES_PATH = '../../user/claude/prices.json'

// A model's list prices, in USD for a million tokens.
export interface Prices {
  readonly input: number
  readonly output: number
  readonly cacheRead: number
}

// The list prices of each model, by its id. A cache write costs `write5m`
// times the input price for the 5-minute lifetime, and `write1h` times for
// the 1-hour one. A response from a model that is not here, or in fast mode,
// is not split: its cost shows as "other".
export interface PriceList {
  readonly models: ReadonlyMap<string, Prices>
  readonly write5m: number
  readonly write1h: number
}

type Fields = Readonly<Record<string, unknown>>

function isFields(value: unknown): value is Fields {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function price(fields: Fields, key: string, where: string): number {
  const value = fields[key]
  if (typeof value !== 'number') throw new Error(`prices.json: ${where}.${key} is not a number`)
  return value
}

// The price list in the text of prices.json. Throws an error that names what
// is wrong.
export function parsePrices(text: string): PriceList {
  const data: unknown = JSON.parse(text)
  if (!isFields(data)) throw new Error('prices.json: not an object')
  const models = data['models']
  if (!isFields(models)) throw new Error('prices.json: models is not an object')
  return {
    models: new Map(
      Object.entries(models).map(([model, prices]) => {
        if (!isFields(prices)) throw new Error(`prices.json: models.${model} is not an object`)
        const where = `models.${model}`
        return [
          model,
          {
            input: price(prices, 'input', where),
            output: price(prices, 'output', where),
            cacheRead: price(prices, 'cache_read', where),
          },
        ]
      }),
    ),
    write5m: price(data, 'cache_write_5m', 'prices'),
    write1h: price(data, 'cache_write_1h', 'prices'),
  }
}
