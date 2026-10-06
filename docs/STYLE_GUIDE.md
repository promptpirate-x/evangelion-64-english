# Style Guide

Defaults for every game. A game's `GAME.md` can override any of these; if it
does, the game's choice wins. Lines marked **DECIDE** are mine to settle
before the first game's Stage 5 sample.

## Goal
Natural English that keeps the meaning, tone and character voices of the
Japanese. Accuracy first, then readability. Do not add jokes, opinions or
content that is not in the original, and do not remove or soften what is.

## Choices to settle

| Topic | Options | Default until decided |
|---|---|---|
| Honorifics (-san, -chan, -sama, senpai) | keep / drop and convey through tone | **DECIDE** (keep) |
| Name order | Japanese (family first) / Western | **DECIDE** (Japanese) |
| Romanisation of long vowels | Yuuki / Yuki / Yūki | **DECIDE** (Yuuki) |
| Spelling | British/Australian / American | **DECIDE** (American, most common in game translations) |
| Food and cultural terms | keep (onigiri) / localise (rice ball) | keep, explain only if the game does |
| Translator notes | allowed / never | never in dialogue; put notes in the readme |

## Rules
- **Names and terms** come from the glossary in `GAME.md`. Never improvise a second spelling.
- **Official names win.** If a character or term has an official English name from another release, use it.
- **Character voice.** Each character keeps a distinct way of speaking. Record it in `GAME.md` (formal, rough, childish, archaic, dialect) and hold to it.
- **Speech quirks and dialects.** Convey with word choice and rhythm. Do not map Japanese dialects onto heavy real-world English accents.
- **Wordplay.** If a pun cannot survive, write an English line that does the same job in the scene, and mark it `[CHECK]` with what the original said.
- **Sound effects and interjections.** Use natural English equivalents ("Huh?", "Ugh") rather than romanised Japanese ("Ehh?", "Uu").
- **Ellipses and dashes.** Japanese uses long runs of dots. Use three dots. Keep stutters readable ("W-what?").
- **Punctuation.** Convert Japanese quotes and full-width punctuation to English forms, unless the game's font or engine needs otherwise.
- **Swearing and mature content.** Match the strength of the original. Do not escalate or tone down.
- **Line length.** Follow the limits recorded in `GAME.md`. Shorten the wording before shrinking the font.
- **System text.** Menus and item names are short, consistent and in title case. Same Japanese term, same English term, everywhere.

## Marking lines
- `[CHECK]` : meaning uncertain, with a note saying why.
- `[FIT]` : correct but too long for its box.
- `[IMG]` : the text is in an image and needs graphic editing.

These markers live in the working files only and must all be gone before a release build.
