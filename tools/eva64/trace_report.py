"""Turn a harness trace log into a list of which strings each scene draws.

  trace_report.py <rom name> <plan>

Reads games\\eva64\\work\\harness\\<rom name>\\<plan>\\log.txt (from a run of a trace
build made from the ORIGINAL text, e.g. eva64_jp_trace) and writes
games\\eva64\\work\\harness\\<rom name>\\<plan>\\strings_by_scene.tsv with one line per
string drawn: scene, frame, string id, Japanese text. Also lists strings never drawn.
"""
import re
import sys

import eva64lib as L
import extract as X
import build as B


def main():
    folder = L.WORK_DIR / "harness" / sys.argv[1] / sys.argv[2]
    rom = L.find_rom().read_bytes()
    tokens = X.load_charmap()
    strings = X.find_strings(rom)
    by_ram = {0x80000000 + off - B.BLOCK_DELTA[blk]: (n, X.decode(codes, tokens)) for n, (blk, off, codes) in enumerate(strings, 1)}
    rows = ["scene\tframe\tid\ttext"]
    seen = set()
    unknown = {}
    last = None
    for line in (folder / "log.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"frame (\d+) scene (\d+) draw ([0-9A-F]{8})", line)
        if not m:
            continue
        frame, scene, ptr = int(m.group(1)), int(m.group(2)), int(m.group(3), 16)
        if ptr in by_ram:
            n, text = by_ram[ptr]
            if (scene, n) != last:
                rows.append(f"{scene}\t{frame}\t{n:04d}\t{text}")
            last = (scene, n)
            seen.add(n)
        else:
            unknown.setdefault(scene, set()).add(ptr)
    (folder / "strings_by_scene.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    never = [n for n in range(1, len(strings) + 1) if n not in seen]
    print(f"{len(rows) - 1} draws of {len(seen)} different strings; {len(never)} strings never drawn")
    print("never drawn:", " ".join(f"{n:04d}" for n in never))
    for scene, ptrs in sorted(unknown.items()):
        print(f"scene {scene}: {len(ptrs)} drawn strings are not in the extracted list, e.g. {[hex(p) for p in sorted(ptrs)[:6]]}")


if __name__ == "__main__":
    main()
