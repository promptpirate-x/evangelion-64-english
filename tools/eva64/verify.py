"""Check a built ROM by doing what the game does: load each text overlay into
memory the way the game's loader would, follow every pointer to a string and
decode what is there.

  verify.py <name> [en]     checks games\\eva64\\work\\build\\<name>.z64

Prints every string that differs from the original, with the pixel width of
each of its lines, and fails if a pointer leads to something that is not a
properly ended string. Run it through verify.bat.
"""
import struct
import sys

import eva64lib as L
import extract as X
import build as B

LINE_LIMIT = 262  # pixels; 288 fits on ares but the user saw lines near that width clipped on Project64


def load_overlay(rom, index):
    entry = B.OVERLAY_TABLE + index * 0x28
    rom_start, rom_end, ram_start, ram_end, _, _, _, _, bss_start, bss_end = struct.unpack(">10I", rom[entry:entry + 0x28])
    mem = bytearray(rom[rom_start:rom_end])
    need = max(ram_end, bss_end) - ram_start
    mem += bytes(max(0, need - len(mem)))
    mem[bss_start - ram_start:bss_end - ram_start] = bytes(bss_end - bss_start)
    return ram_start, mem


def read_ref(mem, base, kind, ram_loc):
    i = ram_loc - base
    if kind == "word":
        return struct.unpack(">I", mem[i:i + 4])[0]
    hi = struct.unpack(">H", mem[i + 2:i + 4])[0]
    lo = struct.unpack(">h", mem[i + 6:i + 8])[0]
    return (hi << 16) + lo


def main():
    english = len(sys.argv) == 3 and sys.argv[2] == "en"
    rom = (L.WORK_DIR / "build" / f"{sys.argv[1]}.z64").read_bytes()
    orig = L.find_rom().read_bytes()
    tokens_new = X.load_charmap(B.CHARMAP_EN) if english else X.load_charmap()
    tokens_old = X.load_charmap()
    widths = rom[L.WIDTH_TABLE:L.WIDTH_TABLE + L.GLYPH_COUNT]
    strings = X.find_strings(orig)
    refs = B.find_refs(orig, strings)
    problems = 0
    checked = 0
    too_wide = 0
    for block, index in B.BLOCK_OVERLAY_INDEX.items():
        base, mem = load_overlay(rom, index)
        lo = B.BLOCK_OVERLAY[block][0]
        for n, (blk, off, codes) in enumerate(strings, 1):
            if blk != block:
                continue
            addrs = {read_ref(mem, base, kind, base + loc - lo) for kind, loc in refs[off]}
            if not addrs:  # nothing points at it: it is read where it always was
                addrs = {0x80000000 + off - B.BLOCK_DELTA[block]}
            if len(addrs) != 1:
                print(f"PROBLEM {n:04d}: its pointers disagree: {[hex(a) for a in addrs]}")
                problems += 1
                continue
            checked += len(refs[off])
            i = addrs.pop() - base
            got = []
            while 0 <= i < len(mem) - 1:
                c = struct.unpack(">H", mem[i:i + 2])[0]
                if c == 0:
                    break
                got.append(c)
                i += 2
            else:
                print(f"PROBLEM {n:04d}: pointer leads outside the overlay")
                problems += 1
                continue
            if any(not X.valid(c) for c in got):
                print(f"PROBLEM {n:04d}: pointer does not lead to a clean string")
                problems += 1
                continue
            if got != codes:
                text = X.decode(got, tokens_new)
                line_widths = []
                w = 0
                for c in got:
                    if c == L.CODE_NEWLINE:
                        line_widths.append(w)
                        w = 0
                    else:
                        w += widths[c - L.CODE_BASE]
                line_widths.append(w)
                flag = "  <-- WIDER THAN %d" % LINE_LIMIT if max(line_widths) > LINE_LIMIT else ""
                too_wide += bool(flag)
                print(f"{n:04d} {line_widths} px: {text}{flag}")
                print(f"       was: {X.decode(codes, tokens_old)}")
    ok = rom[0x10:0x18] == struct.pack(">II", *B.n64_checksum(rom))
    print(f"pointers followed: {checked}, problems: {problems}, lines over {LINE_LIMIT} px: {too_wide}, header checksum valid: {ok}")
    return 1 if problems or not ok else 0


if __name__ == "__main__":
    sys.exit(main())
