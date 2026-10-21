---
name: slidev
description: >
  Slidev traps that fail silently, and how to check for them. Read before you
  edit slides.md or pages/*.md, a layout, global-top.vue or global-bottom.vue,
  a Slidev addon or theme, or the headmatter, and before you export, print or
  build a deck. Covers: offline and private-window browsers, fonts, one
  exported page per click, v-click classes, going back a click or a slide,
  slide classes and .slidev-layout, CSS-transform scaling, speaker notes,
  routes, Slidev internals, Prettier and pnpm.
---

# Slidev traps that fail silently

Each item here is a way that a Slidev deck breaks with no error message, and
what to do about it. A project's own docs can add house rules on top of these.

## Offline, in every browser

A deck must run on any recent macOS or Windows laptop with no network. To
check, build it and load it with every outside request blocked: it must make
none.

The deck must work in Chrome, Firefox and Safari, in regular and private or
incognito windows, with the default privacy protections on. When a change needs
browser checks, test all three engines: Playwright Chromium, Firefox and
WebKit, each in a fresh non-persistent context.

Playwright WebKit is not Safari. Its contexts do not reproduce all of Safari's
private-window protections. For a Safari-only failure, or a change to a
privacy-sensitive API, also test Safari itself, in regular and private windows,
when it is available. Say which tests ran and which could not. Do not turn off
a privacy protection to make the deck work.

## Fonts

These 14 font families are on both Windows and macOS, also in Firefox's
private browsing with strict tracking protection: Arial, Arial Black, Comic Sans
MS, Courier New, Georgia, Impact, Microsoft Sans Serif, Symbol, Tahoma, Times
New Roman, Trebuchet MS, Verdana, Webdings, Wingdings.

For any other font, use Fontsource. If a font is in neither, ask the user
before you add it; it then probably goes in `public/fonts/`.

- **Slidev's `fonts:` setting loads from Google** (in the headmatter or a
  theme's defaults), even when Fontsource is installed, unless it says
  `provider: none`.
- **Import every weight that you use.** A missing weight fails silently: the
  browser uses the nearest weight, or fakes a bold.

## Export and print: one page for each click

A click and a slide are the same to the audience, so an export has one page
for each click: `slidev export --with-clicks`. Without it, Slidev prints each
slide once, at its last click.

- **Anything that looks different in print, export or the overview takes its
  state from the click of its page, never from a constant.** The usual case is
  a live canvas that print mode replaces with a still, or an animated SVG that
  print mode shows at time 0. Read the click from the slide's context
  (`useSlideContext().$clicks`) or from the nav that Slidev gives the page, not
  from the global nav: each printed page has a fixed nav of its own.
- **A page of one slide** (`/N?print=clicks`, which `slidev export --format png`
  opens) mounts every slide but shows only its own. A component that draws for
  each slide must draw only for the slide of its page.
- **A built deck has a `/print` route only if its headmatter sets `download`**
  (to `true` or `auto`). To look at printed pages in any build, open
  `/N?print=clicks`: the client reads `print` from the query.

To check, run `slidev export --with-clicks`: each page must match the live
slide at the same click. A still that is right at click 0 and wrong at clicks 1
and up is the usual mistake, and a check of the live slide alone does not find
it.

## Clicks, slides and going back

- **The settled screen depends only on the slide and the click,** not on how
  the viewer got there: forward, back, a jump or a reload. Only the phase of
  something that runs on its own (a clock, a simulation) may differ.
- **A slide names a target for each click, never a move.** Put the target in the
  slide's frontmatter or its `v-click`s, and let the code that draws it move
  from what is on the screen now to the new target. A move back is then the
  move forward reversed, with no code of its own. Do not write code that asks
  which way the viewer went (`navDirection`, `clicksDirection`).
- **A visual that changes from one slide to the next is one element**: it
  moves, animates or changes state. Slidev mounts a slide before it shows it,
  so one copy on each slide starts each change from its own last state, not
  from what was on the screen. A visual that does not change (a logo, a static
  diagram) can be a copy on each slide. Put the visual in a layer that
  stays mounted for the whole deck (`global-bottom.vue` or `global-top.vue`),
  and let it take its target from each slide.
- **A step animates; a jump does not.** A step is one click, or the next or the
  previous slide. Anything else (a reload, a link, the overview, a slide that is
  not a neighbour) is a jump: show the target at once. A printed page shows its
  click's target, posed.
- **`v-click` gives its element classes:** `slidev-vclick-current` while its
  click is the current one, and `slidev-vclick-prior` after it. CSS can use
  them, for example to dim the earlier items of a list.
- **Do not bind `:class` on an element that has `v-click`.** When the binding
  changes, Vue rewrites the element's classes and removes the `v-click` ones,
  with no error.

## Slide classes and styles

- **A slide's `class:` goes on its `.slidev-layout` element.** A rule with the
  selector `.slidev-layout.<class>` changes those slides only.
- **A slide's own `class:` replaces the headmatter's `defaults: { class: … }`**;
  it does not add to it. So a default class cannot mark every slide.
- **A global layer is outside every slide's `.slidev-layout`**
  (`global-top.vue`, `global-bottom.vue`, `slide-bottom.vue`), so a rule on a
  slide's class does not reach it. A layer that must follow the current slide's
  class has to read it itself.
- **An addon cannot set `colorSchema`.** Slidev reads that default only from the
  theme and the headmatter.
- **Slidev merges each addon's `index.html` into the page,** so an addon can put
  a class on `<html>` with no JavaScript.

## Scaling

Slidev draws a fixed canvas (980 CSS px wide by default, `canvasWidth`) and
scales it to the window with a CSS transform. `clientWidth` and `offsetWidth`
give the unscaled size. To size a canvas or a drawing to what is on the screen,
use `getBoundingClientRect()`.

## Speaker notes

Slidev takes only a slide's last HTML comment as its speaker note. Earlier
comments show neither in the presenter view nor on the slide. So a comment
that is not a note must come before the note.

## Routes

Slidev's `go()` always makes a play, presenter or export path. A page at a
route of its own for a mode of the slides (for example `/narrated/3`) goes back
to `/4` at the first key press. For a mode of the slides, use a query flag
(`?narration`): `go()` keeps it. A page that is not a slide can have its own
route.

## Slidev internals

`PrintSlideClick`, `useFixedNav`, `createFixedClicks`, `slideWidth`,
`slideHeight` and `configs` are not a public API, and they change between
releases. Code that uses them: pin the deck's Slidev version, and look at what
uses them after each upgrade.

## Prettier

Send every deck file to `prettier-plugin-slidev` (an override with
`parser: "slidev"`): `slides.md`, and each file that it imports. Prettier's own
Markdown parser reads a slide's frontmatter as a thematic break and a
paragraph. It adds a blank line after the `---` and removes the indentation from
nested YAML keys, which breaks the slide with no error.

## pnpm

A deck in a subdirectory of a pnpm workspace needs its own
`pnpm-workspace.yaml`, unless it is a member of that workspace. Without one,
pnpm uses the parent's workspace, installs nothing for the deck, and reports no
error.
