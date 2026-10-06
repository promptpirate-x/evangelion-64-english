# Tools

Shared scripts and downloaded third-party tools live here, one subfolder each.

For every tool added, record below: name, version, where it was downloaded
from, date, and what it is for. Nothing gets downloaded without my approval
first (see rule 9 in `CLAUDE.md`).

| Tool | Version | Source | Date added | Used for |
|---|---|---|---|---|
| eva64 (own scripts) | - | written in this workspace | 2026-10-03 | Evangelion 64: `extract.bat`, `build.bat`, `makefont.bat`. Local venv, Python 3.11. |
| Pillow | 11.3.0 | PyPI, installed into `tools\eva64\.venv` only | 2026-10-03 | Drawing font glyphs and previews. |
| BizHawk | 2.11.1 (win-x64) | https://github.com/TASEmulators/BizHawk/releases/tag/2.11.1 | 2026-10-05 | Scriptable emulator for the automated screenshot harness (`eva64\harness.bat`). Portable, in `tools\bizhawk\BizHawk-2.11.1`. Use the Ares64 core. |
| ares | v148 (windows-x64) | https://github.com/ares-emulator/ares/releases/tag/v148 | 2026-10-05 | N64 emulator for testing builds. Portable, in `tools\ares\ares-v148`. |
| evangelion-decomp | master, shallow clone | https://github.com/farisawan-2000/evangelion | 2026-10-05 | Reference only: overlay map, text table notes, character map. Not built. No licence file, so nothing is copied from it into this project. |
| numpy | 2.2.6 | PyPI, installed into `tools\eva64\.venv` only | 2026-10-05 | Searching images for text during investigation. Not needed to build. |
| capstone | 5.0.6 | PyPI, installed into `tools\eva64\.venv` only | 2026-10-03 | Disassembler, for reading the game's MIPS code during investigation. Not needed to build. |
| Noto Serif (variable font) | from google/fonts `main` | https://github.com/google/fonts/tree/main/ofl/notoserif | 2026-10-03 | Source of the English letters. SIL Open Font License (`tools\fonts\NotoSerif-OFL.txt`); credit it in the patch readme. |
| evajo (own scripts) | - | written in this workspace | 2026-10-05 | Evangelion: Jo (PS2): `extract.bat`, `strings.bat`, `applytext.bat`, `build.bat`, `sysfont.py` (proportional English font), `rewrap.bat`, `tm.bat`, `show.py`, `setline.py`, `grep.py`, `idbuild.py`, `makedebug.py`, `makefont.py` (old half-width font), `gim.py`, `pcsx2drive.bat`, `sheet.bat`, `survey.py`, `maketest.py`, `probe1-7.py`. Local venv, Python 3.11, standard library only (`probe6.py` needs capstone and is run with the eva64 venv). |
| PCSX2 | 2.8.2 (Qt, portable) | copied from the user's own install at `C:\Emulators\PCSX2` (program files only: no saves, settings or BIOS) | 2026-10-05 | PS2 emulator for the evajo screenshot harness (`evajo\pcsx2drive.bat`). In `tools\pcsx2\PCSX2-2.8.2`. Uses the BIOS from the user's install. |
| Pillow | 11.3.0 | PyPI, installed into `tools\evajo\.venv` only | 2026-10-05 | Contact sheets of harness screenshots (`evajo\sheet.bat`). |
| xdelta3 | 3.1.0 (x86_64) | https://github.com/jmacd/xdelta-gpl/releases/tag/v3.1.0 | 2026-10-03 | Apply and create `.xdelta` patches. Does not accept non-ASCII filenames. |

### evajo additions (2026-10-05, system text)
- `evajo\wrapsys.py/.bat` - fits and checks menu, notice and page text against the size of its box (see GAME.md).
- `evajo\btnfit.py` - re-spaces button captions in menu XML files; called by `applytext`.
- `evajo\elfstrings.py/.bat` - lists Japanese strings stored inside the game program (read-only).
- `evajo\probe10.py` - finds code in the debug build that loads a given string or address.
- `evajo\todo.py`, `addlines.py` - list untranslated strings; merge a batch file into `scripts\en`.
| soe (own scripts) | - | written in this workspace | 2026-10-05 | Secret of Evangelion (PS2): `g2.py` (G2 compiled-script reader/writer), `extract.bat`, `build.bat`, `spd.py` (SPD/TIM2 image decoder, contact sheets), `pcsx2drive.bat` (copy of the evajo harness, paths changed), `sheet.bat` (contact sheets; runs with the evajo venv's Pillow). Local venv, Python 3.11, standard library only. |
| PCSX2 (second copy) | 2.8.2 (Qt, portable) | copied from `tools\pcsx2\PCSX2-2.8.2` (program files only; same binaries as the user's install) | 2026-10-05 | Private emulator copy for the Secret of Evangelion harness (`soe\pcsx2drive.bat`), so it never shares settings, states or screenshots with the evajo session. In `tools\pcsx2\PCSX2-2.8.2-soe`. Uses the BIOS from the user's install. |
- `evajo\bintopics.py/.bat` - translates the conversation topic names in binary table 0050 (fixed 32-byte fields).
- `evajo\elflib.py`, `elftext.py/.bat` - translate text inside the game program in place (from `scripts\en\elf_strings.tsv`); `elflib` finds addresses and references in the program.
- `evajo\bintable.py/.bat` - translates the typed binary tables 1756 (weapons) and 0957 (enemy and mock-battle names); rewrites the string pool and offsets.
