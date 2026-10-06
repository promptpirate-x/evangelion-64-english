"""Extract the sampled sound (voices and effects) from the Evangelion 64 ROM as WAV files.

The game uses the "libmus" sound library: each bank is a pointer file
("N64 PtrTablesV2") describing the samples and a wave file ("N64 WaveTables")
holding them in Nintendo's ADPCM compression (9 bytes per 16 samples).

Writes games\\eva64\\work\\audio\\<bank>\\<bank>_<number>.wav and an index.tsv with
each sample's ROM position and length. The original ROM is only read.

  extract_audio.py [rate]     rate = playback rate written into the WAV files (default 22050)

Run it through extract_audio.bat.
"""
import struct
import sys
import wave

import eva64lib as L

OUT = L.WORK_DIR / "audio"
# (name, pointer bank offset, wave bank offset), from the bank table at ROM 0x3E670
BANKS = [
    ("sfx", 0x00EC08E0, 0x00EC9060),
    ("voice1", 0x011D89E0, 0x011E54C0),
    ("voice2", 0x01689D50, 0x01692C50),
    ("voice3", 0x01955CD0, 0x0195E4C0),
]


def decode_adpcm(data, book, order):
    out = []
    prev = [0] * order
    for f in range(0, len(data) - 8, 9):
        head = data[f]
        scale, pred = head >> 4, head & 15
        if pred >= len(book):
            pred = 0
        rows = book[pred]
        nib = []
        for b in data[f + 1:f + 9]:
            for v in (b >> 4, b & 15):
                nib.append((v - 16 if v >= 8 else v) << scale)
        for half in (0, 8):
            ix = nib[half:half + 8]
            cur = []
            for i in range(8):
                acc = ix[i] << 11
                for k in range(order):
                    acc += rows[k][i] * prev[k]
                for k in range(i):
                    acc += rows[order - 1][i - 1 - k] * ix[k]
                s = acc >> 11
                s = -32768 if s < -32768 else 32767 if s > 32767 else s
                cur.append(s)
            prev = cur[8 - order:]
            out += cur
    return out


NAME_TABLE = 0x3ED98      # 496 pointers to the developers' clip names: 189 for sfx, then 307 for voice1
MAIN_RAM = 0x80095400     # memory address = ROM offset + this, for the main program


def clip_names(rom):
    names = []
    for i in range(189 + 307):
        p = struct.unpack(">I", rom[NAME_TABLE + i * 4:NAME_TABLE + i * 4 + 4])[0] - MAIN_RAM
        end = rom.index(b"\0", p)
        names.append(rom[p:end].decode("ascii", "replace"))
    return {"sfx": names[:189], "voice1": names[189:]}


def main():
    rate = int(sys.argv[1]) if len(sys.argv) > 1 else 22050
    rom = L.find_rom().read_bytes()
    OUT.mkdir(parents=True, exist_ok=True)
    named = clip_names(rom)
    index = ["bank\tnumber\trom_offset\tbytes\tsamples\tseconds_at_rate\tbase_note\tfile"]
    for name, ptr, wbk in BANKS:
        if rom[ptr:ptr + 14] != b"N64 PtrTablesV" or rom[wbk:wbk + 14] != b"N64 WaveTables":
            raise SystemExit(f"bank {name}: headers not found")
        count, basenote, detune, wavelist = struct.unpack(">4I", rom[ptr + 0x20:ptr + 0x30])
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        total = 0
        for n in range(count):
            wt = ptr + struct.unpack(">I", rom[ptr + wavelist + n * 4:ptr + wavelist + n * 4 + 4])[0]
            base, length, kind, loop, bookp = struct.unpack(">IiIII", rom[wt:wt + 20])
            if kind >> 24 != 0 or bookp == 0 or length <= 0:
                index.append(f"{name}\t{n:03d}\t\t{length}\t0\t0\t\t(skipped: not ADPCM)")
                continue
            b = ptr + bookp
            order, npred = struct.unpack(">ii", rom[b:b + 8])
            vals = struct.unpack(f">{order * npred * 8}h", rom[b + 8:b + 8 + order * npred * 16])
            book = [[list(vals[(p * order + k) * 8:(p * order + k + 1) * 8]) for k in range(order)] for p in range(npred)]
            start = wbk + base
            pcm = decode_adpcm(rom[start:start + length], book, order)
            label = "_" + named[name][n] if name in named else ""
            path = folder / f"{name}_{n:03d}{label}.wav"
            with wave.open(str(path), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(struct.pack(f"<{len(pcm)}h", *pcm))
            note = rom[ptr + basenote + n]
            total += len(pcm)
            index.append(f"{name}\t{n:03d}\t{start:07X}\t{length}\t{len(pcm)}\t{len(pcm) / rate:.2f}\t{note}\t{path.name}")
        print(f"{name}: {count} samples, {total / rate / 60:.1f} minutes at {rate} Hz")
    (OUT / "index.tsv").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()
