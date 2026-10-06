# Workflow

Every game goes through these stages in order. Check in with me at the end
of each stage. Record the result of each stage in the game's `GAME.md`.

## Stage 0: Before committing to a game
- Search for an existing or in-progress English translation, and for an official English release.
- Confirm I own a copy.
- Note the exact version and where the files came from.

## Stage 1: Identify
- Copy the game into `games\<game>\original\` and leave it untouched from then on.
- Record a hash (a fingerprint) of the main files so we can prove later they are unchanged.
- Work out the engine and the platform.
- Find where the text lives: script files, archives, the program file, images.
- Research what tools exist for this engine. Propose them to me (name, source, why) and wait for a yes before downloading anything.

**Done when:** `GAME.md` names the engine and lists where text is stored.

## Stage 2: Extract
- Copy what is needed from `original\` into `work\`.
- Unpack archives and extract the text into a plain, readable format.
- Detect the encoding and confirm it on a line of readable Japanese.
- Count lines and characters so we know the size of the job.

**Done when:** extracted Japanese is readable, and the line count is in `GAME.md`.

## Stage 3: Round-trip test (do not skip)
- Reinsert the extracted text with no changes and rebuild.
- Check the rebuilt files are byte-identical to the originals, or failing that, that the game runs and shows text correctly.
- Then change one single line to English, rebuild, and see it in the running game.

**Done when:** I have seen the test line on screen in the game. If this
fails, stop and fix the pipeline. Nothing gets translated until it passes.

## Stage 4: Prepare
- Build the glossary: character names, places, items, skills, recurring terms.
- Write character notes: gender, age, speech style, relationships.
- List every control code the game uses and what each does.
- Measure limits: characters per line, lines per text box, menu and name length limits.
- Check the font can show English letters at a sensible width.
- Settle the choices in `docs\STYLE_GUIDE.md` for this game (honorifics, name order).

**Done when:** the glossary and limits sections of `GAME.md` are filled in and I have approved them.

## Stage 5: Sample
- Translate one short scene from start to finish.
- Reinsert it, run the game, look at it on screen.
- Use it to estimate time and usage for the whole script.

**Done when:** I have read the sample in-game and approved the style.

## Stage 6: Translate
- One scene or file per batch, with speaker names and surrounding lines for context.
- After every batch, run the automatic checks:
  - line count matches the original
  - control codes match exactly
  - no line left in Japanese by accident
  - no line over the length limits
  - glossary terms used consistently
- Mark uncertain lines `[CHECK]` with a short note.
- Save translated text in `scripts\` and commit it to git.
- Update the progress log in `GAME.md`.

## Stage 7: Edit
- Second pass over all `[CHECK]` lines.
- Read-through for voice and consistency, character by character.
- Re-wrap text to fit the boxes.

## Stage 8: Reinsert and test
- Rebuild the game from the translated text.
- Play it. Cover the opening, menus, battles or systems, long lines, each branch and each ending where possible.
- Log every problem found in `GAME.md` and fix it at the source, in `scripts\`, never in the built files.

## Stage 9: Images and leftovers
- Text inside images, text inside the program file, and anything else missed.
- Often the most fiddly part. Decide per item whether it is worth doing.

## Stage 10: Patch and release
- Build a patch file containing only the differences from the original.
- Test the patch on a fresh untouched copy of the game.
- Write a readme: game version and hash needed, how to apply, credits, known issues, and an honest note on how the translation was made.
- Share the patch only. Never the game files.
