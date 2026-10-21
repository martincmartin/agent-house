---
name: slidev
description: >
  Create and modify Slidev presentations. Use when working on Slidev
  presentations, including slides, Vue components, layouts, themes,
  presenter notes, animations, and Slidev configuration.
---

# Assets

The goal is to be able to run the Slidev presentation on any recent MacOS or
Windows laptop, even when not connected to the internet.  To verify, build and
load the deck with outside requests blocked; it must make none.

The deck must work in Chrome, Firefox, and Safari, in regular and private or
incognito windows, with default privacy protections enabled. Whenever a change
needs browser checks, test all three engines: Playwright Chromium, Firefox, and
WebKit. Use fresh non-persistent browser contexts.

Playwright WebKit is not Safari itself. Its contexts do not reproduce all Safari
private-window protections. For a Safari-specific failure or a change to
privacy-sensitive APIs, also test Safari directly in regular and private windows
when it is available. State which tests ran and which could not run. Do not
disable privacy protection to make the deck work.

## Fonts

The following 14 font families are available on both Windows and MacOS, even in
Firefox's Private Browsing mode and with strict tracking protection:

Arial
Arial Black
Comic Sans MS
Courier New
Georgia
Impact
Microsoft Sans Serif
Symbol
Tahoma
Times New Roman
Trebuchet MS
Verdana
Webdings
Wingdings

Use Fontsource for other fonts, unless there's a font that isn't one of the 14
baseline and isn't in fontsource, in that case ask the user before including it,
and it should probably go in public/fonts.

Slidev's `fonts:` setting (headmatter or a theme's defaults) loads fonts from
Google unless it says `provider: none`, even when Fontsource is installed. Import
every weight you use: a missing weight fails silently (nearest weight or faux
bold).

# Export and print

A click and a slide are the same to the audience, so an export has one page for
each click: `slidev export --with-clicks`. Without it, Slidev prints each slide
once, at its last click.

Anything that looks different in print, export or the overview must take its
state from the click of its page, never from a constant. The usual case is a
live canvas that print mode replaces with a still, or an animated SVG that
print mode shows at time 0. Read the click from the slide context
(`useSlideContext().$clicks`) or the nav that Slidev gives the page, not from
the global nav: each printed page has a fixed nav of its own.

Verify with `slidev export --with-clicks`: each page must match the live slide
at the same click. A still that is right at click 0 and wrong at clicks 1 and
up is the usual mistake, and a check of the live slide alone does not find it.
