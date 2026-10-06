"""List which voice clips play in which scene, next to the subtitles shown around them.

  sound_report.py <rom name> <plan>

Reads the harness log of a trace build (e.g. eva64_en_trace, plan trace_all) and writes
games\\eva64\\work\\audio\\voices_by_scene.tsv: one line per event in play order,
either a voice clip (with its file name and length) or a subtitle (English text).
Also lists voice clips that never played. Needs extract_audio.bat to have been run.
"""
import csv
import re
import struct
import sys

import eva64lib as L
import extract as X
import build as B
import verify as V

SFX = 189
SCENES = {43: "M1 intro/briefing", 44: "M1 launch", 45: "M1 battle", 46: "M1 win", 47: "M2 intro", 48: "M2 battle",
          49: "M2 win", 50: "M2 end", 51: "M3 intro", 52: "M3 sniping", 53: "M3 result", 54: "M3 ending",
          55: "M4 intro", 56: "M4 game", 57: "M4 ending", 58: "M5 intro", 59: "M5 game", 60: "M5 ending",
          61: "M6 intro", 62: "M6 game", 63: "M6 ending", 64: "M7 intro", 65: "M7 game", 66: "M7 ending",
          67: "M8 intro", 68: "M8 battle", 69: "M8 ending", 70: "M9 intro", 71: "M9 battle", 72: "M9 ending",
          73: "M10 intro", 74: "M10 game", 75: "M10 ending", 76: "M11 intro", 77: "M11 battle", 78: "M11 ending",
          79: "M12 intro", 80: "M12 battle", 81: "M13 intro", 82: "M13 battle", 83: "M13 cutscene", 84: "M13 final battle",
          85: "scene 85", 86: "scene 86", 33: "simulation", 35: "opening", 37: "opening"}


def main():
    folder = L.WORK_DIR / "harness" / sys.argv[1] / sys.argv[2]
    audio = L.WORK_DIR / "audio"
    clips = {int(r["number"]): r for r in csv.DictReader(open(audio / "index.tsv", encoding="utf-8"), delimiter="\t") if r["bank"] == "voice1"}
    # subtitle addresses in the traced build -> string id and text
    rom = (L.WORK_DIR / "build" / f"{sys.argv[1]}.z64").read_bytes()
    orig = L.find_rom().read_bytes()
    tokens = X.load_charmap(B.CHARMAP_EN)
    strings = X.find_strings(orig)
    refs = B.find_refs(orig, strings)
    text_at = {}
    for block, index in B.BLOCK_OVERLAY_INDEX.items():
        base, mem = V.load_overlay(rom, index)
        lo = B.BLOCK_OVERLAY[block][0]
        for n, (blk, off, codes) in enumerate(strings, 1):
            if blk != block or not refs[off]:
                continue
            kind, loc = refs[off][0]
            addr = V.read_ref(mem, base, kind, base + loc - lo)
            i = addr - base
            got = []
            while 0 <= i < len(mem) - 1:
                c = struct.unpack(">H", mem[i:i + 2])[0]
                if c == 0 or not X.valid(c):
                    break
                got.append(c)
                i += 2
            text_at[(block, addr)] = (n, X.decode(got, tokens))
    rows = ["scene\tscene_name\tframe\tkind\tid\tfile_or_text\tseconds"]
    played = set()
    last = None
    for line in (folder / "log.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"frame (\d+) scene (\d+) (sound|draw) ([0-9A-F]+)", line)
        if not m:
            continue
        frame, scene, kind = int(m.group(1)), int(m.group(2)), m.group(3)
        name = SCENES.get(scene, f"scene {scene}")
        if kind == "sound":
            num = int(m.group(4))
            if num < SFX:
                continue
            clip = clips.get(num - SFX)
            if clip is None or (scene, num) == last:
                continue
            last = (scene, num)
            played.add(num - SFX)
            rows.append(f"{scene}\t{name}\t{frame}\tvoice\t{num - SFX:03d}\t{clip['file']}\t{clip['seconds_at_rate']}")
        else:
            addr = int(m.group(4), 16)
            hit = text_at.get((1, addr)) or text_at.get((2, addr))
            if hit:
                rows.append(f"{scene}\t{name}\t{frame}\tsubtitle\t{hit[0]:04d}\t{hit[1]}\t")
    (audio / "voices_by_scene.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    never = sorted(set(clips) - played)
    (audio / "voices_never_played.txt").write_text("\n".join(clips[n]["file"] for n in never) + "\n", encoding="utf-8")
    voices = sum(1 for r in rows if "\tvoice\t" in r)
    print(f"{voices} voice plays of {len(played)} different clips; {len(never)} of {len(clips)} clips never played")
    print(f"written: {audio / 'voices_by_scene.tsv'} and voices_never_played.txt")


if __name__ == "__main__":
    main()
