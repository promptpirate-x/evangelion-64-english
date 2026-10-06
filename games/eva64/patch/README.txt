NEON GENESIS EVANGELION (Nintendo 64) - English translation patch
Version 0.4 (beta), 2026-10-05

This is an unofficial fan translation. It is free. It contains no game data:
you need your own copy of the game.


WHAT YOU NEED
-------------
The Japanese ROM in big-endian (.z64) format, matching No-Intro's
"Neon Genesis Evangelion (Japan)":

    Size   33,554,432 bytes
    CRC32  A10A86AF
    SHA-1  A9BA0A4AFEED48080F54AA237850F3676B3D9980

If your file has a .v64 or .n64 extension it is in a different byte order and
must be converted to .z64 first, or the patch will not apply.

After patching, the ROM's SHA-1 is 2A5E4AA51C2F84A1AA9917BE50E35C6B535A7B4D.


HOW TO APPLY
------------
The patch is in xdelta format: eva64_english_v0.4.xdelta

Easiest: use a patcher with a window, such as "Delta Patcher" or the web page
"Rom Patcher JS". Choose your ROM as the original file and the .xdelta as the
patch.

Command line, with xdelta3:

    xdelta3 -d -s "Neon Genesis Evangelion (Japan).z64" eva64_english_v0.4.xdelta "Evangelion 64 (English).z64"

Keep your original ROM; the patch writes a new file.


EMULATORS AND HARDWARE
----------------------
Tested on Project64 3.0.1, ares v148, BizHawk 2.11.1 (both its Ares64 and
Mupen64Plus cores) and M64Plus FZ on Android.

Two things in the patch are there so that it runs without any setup:

- The patched ROM keeps the original game's header checksum
  (147E0EDB-36C5B12C), and that checksum is valid for the patched contents.
  Emulators that recognise games by it, such as Project64, apply the game's
  usual settings.
- The game normally stops with an "EEP-ROM SIZE IS 4K" error screen unless the
  cartridge has the larger "16K EEPROM" save chip. Emulators that recognise
  games by a hash of the whole file (Mupen64Plus and the many apps built on
  it, including phone emulators) do not know a modified ROM and give it the
  4K kind. The patch makes the game accept that, so it starts normally.

Starting and saving were confirmed on M64Plus FZ (Android), which is of this
kind.
Other emulators may store less for a 4K chip; if saving fails on yours and you
can set the save type for this ROM, choose "EEPROM 16K".

Not tested on a real console or flash cartridge (those have the 16K chip, so
the second change does nothing there).

Saves made with the Japanese ROM should keep working (the save format is not
changed), but this has not been tested.

WHAT IS TRANSLATED
------------------
- All subtitles, narration and mission briefings (missions 1 to 13).
- Mission title cards, "Angel destroyed" cards and story cards.
- Pause-screen control guides for every mission.
- Main menu decorations, the erase-data screen, the mission 5 practice/battle
  choice, simulation mode labels, the model viewer's name strips.
- Opening company credits and copyright lines. The first credit card also
  carries a small parrot emblem and the line "English translation by
  PromptPirate", which are not in
  the original game.


KNOWN ISSUES
------------
- BETA: most screens were checked by jumping to scenes with a scripted emulator,
  and the opening missions have been played by hand. Nobody has yet played the
  patched game from start to finish. Please report crashes, garbled text and
  anything still in Japanese.
- Voices are Japanese and most spoken lines have no subtitles in the original
  game, so they have none here either.
- Left in Japanese on purpose or for now: the staff names in the end credits
  (their readings would be guesses), the Japanese title logo, a few small
  labels in the battle display (power source, safety), a small caption in
  mission 3's intro, and three pictures with artwork behind the text.
- "Angel destroyed" cards read "No. 3 Angel Sachiel" rather than "3rd Angel
  Sachiel", because the game builds the card from pieces in a fixed order.
- Title cards and labels use a plain serif font, not the original's styled
  lettering. Some pause screens show faint marks where Japanese text was erased.
- Mission 4's "Target:" label looks thinner than the labels beside it.
- 日本重化学工業共同体 is shortened to "Japan Heavy Chemical Ind." to fit a line.


HOW THIS TRANSLATION WAS MADE
-----------------------------
The text was translated from the Japanese by an AI model (Anthropic's Claude),
which also wrote the extraction, insertion and testing tools, working with and
directed by a human who approved the glossary and style and tested builds.
It has not been checked by a professional translator. Names and terms follow
the long-standing official English releases of the TV series; Western name
order is used and honorifics are dropped. Mission titles are the usual English
renderings of the Japanese episode titles.

Technical notes: the game's font was given Latin letters (drawn from Noto
Serif); five instructions in the text routine were changed so that letter
spacing follows each letter's width and each text picture is followed by a few
blank rows; a short routine was added to give the first credit card four
extra colours for the translator's emblem; longer English text is stored in enlarged copies of two of the
game's code overlays placed in unused ROM space; and four unused words were
chosen so that the ROM's checksum equals the original's.


CHANGES
-------
v0.4  Mission 5's pause screen reworded so its lines are the same size. All 14
      pause screens have now been seen running.
v0.3  Starts on emulators that give an unrecognised ROM a 4K save chip (the
      "EEP-ROM SIZE IS 4K" error). Translator credit with emblem added to
      the first opening card.
v0.2  Original header checksum kept, so Project64 needs no setup. Fixed specks
      under subtitles and on the company credit cards in Project64. Smaller
      subtitle font and reworded lines so nothing is cut off at the screen
      edge. Smoother edges on labels and cards.
v0.1  First beta.


CREDITS
-------
- Translation, tools and testing: PromptPirate (promptpirate-x), with Claude
  (Anthropic).
- The Korean translation of this game (romhacking.net, translation 6260) was
  used as a reference for where the game's text and text images are.
- The Evangelion 64 decompilation project (github.com/farisawan-2000/evangelion)
  and its contributors' notes were used as a reference for the game's layout:
  farisawan-2000, IlDucci, Zoinkity, Dark_Kudoh, GriffithVIII. No code or data
  from it is included.
- Font: Noto Serif, (c) The Noto Project Authors, SIL Open Font License 1.1.
- Tools used: xdelta3, BizHawk, ares, capstone, Pillow.

Neon Genesis Evangelion is (c) GAINAX / Project Eva., TV Tokyo and its other
rights holders. The game is (c) 1999 BANDAI. This patch is not affiliated with
or endorsed by any of them. Do not sell it, and do not distribute it together
with the game.
