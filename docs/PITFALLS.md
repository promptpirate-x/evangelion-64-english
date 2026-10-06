# Pitfalls

Things that go wrong in fan translation projects, roughly in the order you
will meet them. Each one has a "what to do" so it is a checklist, not just a
warning list.

## 1. Technical

### Encoding (the number one killer)
Computers store text as numbers, and an "encoding" is the table that says
which number means which character. Older Japanese games mostly use
Shift-JIS (called `cp932` on Windows); some use EUC-JP, UTF-16 or UTF-8.
Read a file with the wrong table and you get garbage ("mojibake"). Save it
with the wrong table and the original text is gone for good.

- Find the encoding per game, test it on a line you can read, write it in `GAME.md`.
- Always state the encoding in code. Windows defaults will not be right.
- Some games use a custom table (common on old consoles), where the bytes mean nothing without the game's own character map. That needs a "table file" built by hand.

### The game's locale
Many Japanese PC games misbehave or show garbage on a non-Japanese Windows.
The usual fix is a locale emulator tool, not changing the system locale.
Changing the system-wide locale can affect other programs, so ask first.

### Control codes and placeholders
Mixed into the dialogue are instructions to the game: line breaks, colour
changes, "insert player name here", wait-for-button. If a translation drops,
reorders or "fixes" one, the game can crash or show the wrong thing, often
hours into a playthrough where nobody tests.

- Count and compare control codes before and after every batch, automatically.
- AI translation is especially prone to quietly tidying these away.

### Text does not fit
English takes up far more room than Japanese. Japanese uses full-width
characters, and one kanji can be a whole English word.

- Text boxes overflow or get cut off. Lines need re-wrapping to the box width.
- Menus, item names and buttons often have a hard character limit.
- Some games store text at a fixed length or use "pointers" (a list of addresses saying where each line starts). Make a line longer without updating the pointers and everything after it breaks.
- The game's font may have no English letters, only full-width ones (which look l i k e  t h i s), or no proportional spacing. Fixing fonts can be a project of its own.

### Text that is not in the script files
- Text baked into images (title screens, buttons, chapter cards) needs image editing.
- Text inside the game's program file (the `.exe` or equivalent) needs more careful, riskier editing.
- Text assembled by code ("You got" + item + "!") follows Japanese word order and can come out backwards in English.

### Reinsertion is harder than extraction
Getting text out is usually easy. Getting it back in so the game still runs
is the real work. This is why the round-trip test (extract, reinsert
unchanged, confirm the game runs) comes before any translating. If the
round trip fails, weeks of translation would have nowhere to go.

### Windows path trouble
- Japanese characters in file or folder names can break tools. Keep game folders under short ASCII names.
- Very long paths break some older tools. This workspace's parent folder has spaces in its name, which some command-line tools also dislike; always quote paths.

### Engine differences
Every engine stores text differently, and the tool for one does nothing for
another: RPG Maker (several generations), Kirikiri, Ren'Py, Unity, Wolf RPG,
custom engines, console ROMs. Identify the engine first; it decides
everything else. Tool names I suggest from memory may be outdated, so
confirm a tool is current and maintained before relying on it.

### Updates break patches
A patch is made against one exact version of a game. If the game updates
(Steam auto-update, a different release), the patch may no longer apply.
Record the exact version and a file hash (a fingerprint of the file) in
`GAME.md`.

## 2. Translation quality

### Japanese leaves things out
Japanese routinely drops the subject, has no plural, and often does not mark
gender. "Went to the shop" could be I, he, she or they. A line translated
alone will be wrong surprisingly often.

- Translate whole scenes with speaker names attached.
- Keep a character sheet (gender, age, how they speak, who they are to each other) in `GAME.md`.
- Mark unclear lines `[CHECK]` rather than guessing.

### Consistency drift
Across thousands of lines and many sessions, names and terms drift: a place
gets three spellings, a spell gets two names. Claude Code does not remember
earlier sessions, so the glossary in `GAME.md` is the only memory there is.

### AI-specific failure modes
- **Confident mistranslation.** Fluent English that says the wrong thing, with no warning. Fluency is not accuracy.
- **Skipped or merged lines.** In long batches, lines get dropped or two get combined, shifting everything after. Always check line counts match.
- **Over-smoothing.** Distinct character voices flatten into the same neutral tone.
- **Softening or embellishing.** Content gets toned down or padded with things the original never said.
- **Refusals mid-batch.** Some content may get declined, leaving gaps. Check for untranslated lines after each batch.
- **Batch size.** Too large and quality drops toward the end; too small and context is lost. Start with one scene per batch.

### Hard-to-translate material
Puns, wordplay, honorifics, speech quirks (verbal tics, dialects, archaic
speech), jokes that rely on kanji, and cultural references. Decide your
approach once in `STYLE_GUIDE.md` and stick to it.

### No second pair of eyes
You need someone or something to check the Japanese. If you do not read
Japanese, be honest that the result is machine translation with editing,
and say so in the release notes. A second independent pass on `[CHECK]`
lines catches a lot.

## 3. Testing

- A game can have dozens of hours and many branches. Text that never gets displayed never gets tested.
- Find or make saves at many points, and learn whether the game has a debug mode or scene viewer.
- Test the worst cases on purpose: longest lines, longest names, menus, battle messages, endings.
- Old saves sometimes store text inside them and will keep showing Japanese after patching.

## 4. Legal and distribution

I am not a lawyer and this is not legal advice. Fan translation sits in a
legal grey area: the script is copyrighted, and a translation is a
derivative of it, even when done for free.

- Share patches only (files containing just your changes, such as xdelta or BPS), never the game, ROM, ISO or full translated script files.
- Work from a copy you own.
- Do not charge for it.
- Check whether an official English release exists or has been announced. That is when rights holders are most likely to object, and when the work may be wasted.
- Some publishers send takedown notices regardless. Be ready to pull a release.
- Breaking copy protection can be a separate legal issue from copyright in many countries, including Australia.
- If you reuse someone else's tools or an earlier partial translation, check the licence and credit them.
- Keep copyrighted game material out of git and out of any public repo (see `.gitignore`).

## 5. Project management

- **Check it has not already been done.** Search for existing or in-progress translations before starting.
- **Scope.** A text-heavy game can be hundreds of thousands of lines. Count the lines in Stage 2 before committing.
- **Pick an easy first game.** A short game on a well-documented engine teaches the whole pipeline. A custom-engine console game as a first project is where most people quit.
- **Back up.** Keep `original\` untouched and commit `scripts\` to git often.
- **Tools from the internet.** Many translation tools are small unsigned programs from forums or file hosts. Prefer open-source tools with a public repo, scan downloads, and do not run them with admin rights.
- **AI cost and time.** Large scripts use a lot of usage. Do a small sample first and estimate before a full run.
