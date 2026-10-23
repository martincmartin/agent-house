---
name: typescript-practices
description: >
  TypeScript practices: strict types, running .ts files with Node, scripts,
  promises and resources, tests, lint, speed, and Playwright from TypeScript.
  Read before you plan, write or review TypeScript, in an app or in a script
  or a test.
---

You are an expert TypeScript engineer.

## Types

- Turn on the strict compiler options: `strict`, `noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`,
  `verbatimModuleSyntax`. On an existing project, keep its options.
- Do not use `any`, the non-null assertion `!`, or `as`. The one exception is
  `as` at a boundary, after a check at run time.
- A type does not check data at run time. Type data from outside (JSON, a
  file, a page) as `unknown`, and check each value where you read it.
- Make invalid states impossible to write: a union of objects with a `kind`
  field, not flags and optional fields.
- Give data fields `readonly`. Use an interface for a value, and a class for
  a thing with identity or with resources.
- Under `noUncheckedIndexedAccess`, `array[index]` is `T | undefined`. Write
  `array[index] ?? 0` in arithmetic, or check the value.

## Run `.ts` files with Node

- Node runs a `.ts` file directly: it removes the types. Use no build step,
  `ts-node` or `tsx` for scripts and tests.
- Node only removes types, so use only syntax that it can remove: no `enum`,
  `namespace` or constructor parameter properties. Turn on
  `erasableSyntaxOnly`.
- Import with the `.ts` extension (`allowImportingTsExtensions`), and import a
  type with `import type`.
- Find a file next to the module from `import.meta.url` (`fileURLToPath`),
  not from the working directory.

## Scripts

- Parse arguments with `parseArgs` from `node:util`. It ignores extra
  positional arguments, so check their exact count, and print the usage if it
  is wrong.
- Set `process.exitCode` to give the result. Exit with status 2 after a usage
  error.
- Put the command-line part in `if (import.meta.main)`, so that a test can
  import the script's functions.
- Do not add a dependency for what `node:` modules do: `node:fs/promises`,
  `node:path`, `node:util`, `node:zlib`, `node:http`, `node:test`.

## Promises and resources

- Await or return every promise. A promise that nothing awaits hides its
  error.
- Run independent work in parallel with `Promise.all`.
- When a promise that can reject is used only in a `Promise.race`, attach a
  `.catch` to it. Otherwise a rejection that comes after the race ends stops
  Node.
- Release a resource in `try`/`finally`, or give the caller a function that
  takes a callback (`withBrowser(use)`) and releases the resource after the
  callback.
- When you wrap an error, give the new error the old one as its `cause`.
- Test an error's kind by its `name`, not with `instanceof`, when its class
  can come from more than one copy of a package. For example,
  `playwright-chromium` and `playwright-webkit` share one `TimeoutError`
  only while they resolve to one copy of `playwright-core`.
- In a loop that must go on after one item fails, catch the error of that
  item, record it with the item's name, and go on. Do not let one item's
  error end the run with a stack trace that names no item.

## Tests

- Use `node:test` and `node:assert/strict`. Add a test framework only when
  these cannot do the job.
- Test the logic as pure functions. Keep input and output (files, browsers)
  in a thin layer around them.

## Lint and format

- Use typescript-eslint's `strictTypeChecked` and `stylisticTypeChecked`
  configurations, and Prettier.
- Fail on a warning (`eslint --max-warnings 0`).

## Speed

- In a loop over many bytes, use a typed array (`Uint8Array`), and read with
  an index. A method call for each byte, such as `Buffer.readUInt8`, can be
  several times slower.
- A `Uint8Array` keeps the low 8 bits of each value that you write to it. Use
  that when you need arithmetic modulo 256.

## Data shared with another language

- Python and JavaScript write some numbers differently in JSON: Python writes
  `1.0` and `1e-05`, and JavaScript writes `1` and `0.00001`. Python's
  `json.dumps` also puts spaces after `,` and `:`. So a file that both write
  is the same data, but not always the same bytes.

## Playwright from TypeScript

- Give `page.evaluate` and `page.waitForFunction` a function, not a string,
  so that the compiler checks the code that runs in the page.
- Declare the page's globals (`declare global { interface Window { ... } }`)
  in a `.ts` module that the app and the scripts both include. A declaration
  in a `.vue` file reaches only `vue-tsc`, not the type-aware lint of a `.ts`
  file.
- A page that throws while it loads may never become ready. Make the wait for
  it fail at the first `pageerror`, with that error, not at the timeout.
