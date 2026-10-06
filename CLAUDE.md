# Fan Translations Workspace

This folder is a workspace for translating Japanese games into English.
Each game gets its own subfolder under `games\`. This file holds the rules
that apply to every game.

## Read these before working

- `docs\PITFALLS.md` — the mistakes that ruin translation projects. Read before touching any game file.
- `docs\WORKFLOW.md` — the stages every game goes through, in order.
- `docs\STYLE_GUIDE.md` — how the English should read (names, honorifics, tone).
- `games\<game>\GAME.md` — engine, encoding, glossary and progress for that one game. Read it at the start of every session on that game, and update it at the end.

## How to work with me

- Explain technical things simply, as if to a beginner. Say what a term means the first time it comes up.
- Stop and check in after each major step (extraction, a translation batch, a reinsertion, a build). Never chain several operations without giving me a chance to respond.
- Never claim something worked without checking it. "The script ran without errors" is not proof. Proof is: the output file exists, has a sensible size, opens, and the Japanese/English text inside is readable. If you could not verify something, say so plainly.
- Bad news is fine. Tell me when something failed or when you are unsure.
- Be direct and concise.

## Hard rules

1. **Originals are read-only.** Game files as I got them live in `games\<game>\original\` and are never edited, moved or overwritten. All work happens on copies in `work\`.
2. **Never guess an encoding.** Detect it, test it on a known Japanese line, and record it in `GAME.md`. Wrong encoding silently destroys text.
3. **Round-trip test before translating anything.** Extract the text, reinsert it unchanged, and confirm the game still runs (or the rebuilt file is byte-identical). No translation starts until this passes.
4. **Never touch control codes.** Things like `\n`, `%s`, `{0}`, `<color=...>`, `\V[1]`, `@name` are instructions to the game, not text. They must come out of translation exactly as they went in. Run an automated check for this on every batch.
5. **Glossary first.** Check `GAME.md` for a name or term before translating it. If it is new, add it there, then use it. Never translate the same name two different ways.
6. **Translate with context.** Work scene by scene with speaker names and neighbouring lines visible, never on isolated or shuffled lines.
7. **Don't invent meaning.** If a Japanese line is ambiguous (missing subject, unclear speaker, wordplay), mark it `[CHECK]` with a note instead of guessing confidently.
8. **Nothing copyrighted goes into git or gets shared.** No ROMs, ISOs, game archives, extracted scripts in bulk, or game images. Releases are patch files only.
9. **Don't download or run tools without asking me.** Tell me the tool name, where it comes from, and why, then wait.

## Building tools

- Everything must be portable: I should be able to move this whole folder to another drive and have it still work.
- No hard-coded drive letters or absolute paths. Resolve paths relative to the script (`Path(__file__).parent` in Python, `%~dp0` in `.bat`).
- Each tool gets a `.bat` launcher that creates its own local venv if one is missing.
- Dependencies install into the local venv only. Never install into, upgrade or otherwise modify the global `C:\Python310` environment.
- Seed new venvs from Python 3.11 via the `py` launcher (`py -3.11 -m venv .venv`).
- Downloaded third-party tools live in `tools\` inside this workspace.
- Always open text files with an explicit encoding (`encoding="utf-8"`, `"cp932"`, etc.). Never rely on the Windows default.

## Layout

```
claude-fan-translations\
  CLAUDE.md
  docs\            PITFALLS.md, WORKFLOW.md, STYLE_GUIDE.md
  tools\           shared scripts and downloaded tools
  games\
    _TEMPLATE\     copy this to start a new game
    <game>\
      GAME.md      engine, encoding, glossary, progress log
      original\    untouched game files (read-only, not in git)
      work\        extracted and in-progress files (not in git)
      scripts\     translated text, the part worth versioning
      patch\       release patch files
```

## Starting a new game

1. Copy `games\_TEMPLATE\` to `games\<short-name>\`.
2. Fill in the top of `GAME.md` (title, platform, where the files came from).
3. Follow `docs\WORKFLOW.md` from Stage 1. Do not skip the round-trip test.
