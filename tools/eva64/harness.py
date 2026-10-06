"""Run a built Evangelion 64 ROM in BizHawk under a script and save screenshots.

  harness.py <name> <plan>

<name> is a ROM in games\\eva64\\work\\build (without .z64). <plan> is a file in
tools\\eva64\\plans describing what to press and when to take pictures, one
step per line:

    wait 300            run 300 frames (60 frames = 1 second)
    press Start 4       hold a button for 4 frames, then release
    shot title          save a screenshot called title.png
    record 3600 60 intro   run 3600 frames, saving a screenshot every 60
    save menu / load menu  save or reload an emulator save state
    timeout 7200        allow the run this many seconds (default 900)
    autoshot 50         trace builds only: screenshot 50 frames after each string is drawn
    sheet 8 6 160 120   contact sheet layout: columns, rows, thumbnail width, height
    watch 0D5114 2      log a memory value (hex RAM offset, size in bytes) whenever it changes
    poke 0D5114 2 36    write a value (decimal) to memory
    # comment

Screenshots and a log of every text string the game draws go to
games\\eva64\\work\\harness\\<name>\\. Run it through harness.bat.
"""
import subprocess
import sys

import eva64lib as L

BIZHAWK = L.WORKSPACE / "tools" / "bizhawk" / "BizHawk-2.11.1" / "EmuHawk.exe"
PLANS = L.TOOL_DIR / "plans"
TIMEOUT = 900  # seconds

LUA = r'''
local out = "%(out)s"
local steps = {
%(steps)s
}
local log = io.open(out .. "/log.txt", "w")
local function say(s) log:write(s .. "\n"); log:flush(); console.log(s) end
say("core: " .. emu.getsystemid() .. " rom: " .. gameinfo.getromname())
client.speedmode(6400)
emu.limitframerate(false)
client.SetSoundOn(false)
local watches = {}
local function peek(addr, size)
  if size == 1 then return memory.read_u8(addr, "RDRAM") end
  if size == 2 then return memory.read_u16_be(addr, "RDRAM") end
  return memory.read_u32_be(addr, "RDRAM")
end
-- "Trace" builds (build.bat ... trace) keep a count of text-draw calls at RAM 0x284 and the
-- last 16 string addresses at 0x290. Log each new one with the frame and scene number.
local drawn = nil
local autoshot = %(autoshot)s   -- frames to wait after a string is drawn before taking a picture, or nil
local shot_at = nil
local function advance()
  emu.frameadvance()
  local count = memory.read_u32_be(0x284, "RDRAM")
  if drawn == nil or count < drawn or count - drawn > 16 then drawn = count end
  while drawn < count do
    local ptr = memory.read_u32_be(0x290 + (drawn %% 16) * 4, "RDRAM")
    if ptr >= 0x80000000 then
      say(string.format("frame %%d scene %%d draw %%08X", emu.framecount(), peek(0x0D5114, 2), ptr))
    else
      say(string.format("frame %%d scene %%d sound %%d", emu.framecount(), peek(0x0D5114, 2), ptr %% 0x10000000))
    end
    drawn = drawn + 1
    if autoshot then shot_at = emu.framecount() + autoshot end
  end
  if shot_at and emu.framecount() >= shot_at then
    client.screenshot(string.format("%%s/auto_s%%03d_%%06d.png", out, peek(0x0D5114, 2), emu.framecount()))
    shot_at = nil
  end
  for _, w in ipairs(watches) do
    local v = peek(w.addr, w.size)
    if v ~= w.last then
      say(string.format("frame %%d  [%%06X] %%s -> %%d (0x%%X)", emu.framecount(), w.addr, tostring(w.last), v, v))
      w.last = v
    end
  end
end
local ok, err = pcall(function()
  for _, st in ipairs(steps) do
    if st[1] == "wait" then
      for i = 1, st[2] do advance() end
    elseif st[1] == "press" then
      for i = 1, st[3] do joypad.set({["P1 " .. st[2]] = true}); advance() end
      advance()
    elseif st[1] == "save" then
      savestate.save(out .. "/" .. st[2] .. ".State")
    elseif st[1] == "load" then
      savestate.load(out .. "/" .. st[2] .. ".State")
      for _, w in ipairs(watches) do w.last = peek(w.addr, w.size) end
    elseif st[1] == "findpal" then
      -- look through memory for a 16-colour palette whose entries 6-10 are red and 1, 11 are white
      local bytes = memory.read_bytes_as_array(0, 0x400000, "RDRAM")
      local function col(i) return bytes[i + 1] * 256 + bytes[i + 2] end
      local function red(v) local r = math.floor(v / 2048); return r >= 6 and (math.floor(v / 64) %% 32) <= r / 4 and (math.floor(v / 2) %% 32) <= r / 4 end
      local function white(v) local r = math.floor(v / 2048); return r >= 20 and math.abs(r - math.floor(v / 64) %% 32) <= 3 and math.abs(r - math.floor(v / 2) %% 32) <= 3 end
      local found = 0
      for a = 0, 0x400000 - 34, 2 do
        if red(col(a + 12)) and red(col(a + 20)) and white(col(a + 2)) and white(col(a + 22)) then
          local s = string.format("palette at %%06X:", a)
          for k = 0, 15 do s = s .. string.format(" %%04X", col(a + 2 * k)) end
          say(s); found = found + 1
          if found >= 12 then break end
        end
      end
      say("findpal: " .. found .. " candidates")
    elseif st[1] == "dumpram" then
      local bytes = memory.read_bytes_as_array(0, 0x400000, "RDRAM")
      local f = io.open(out .. "/" .. st[2] .. ".bin", "wb")
      local chunk = {}
      for i = 1, #bytes do
        chunk[#chunk + 1] = string.char(bytes[i])
        if #chunk == 4096 then f:write(table.concat(chunk)); chunk = {} end
      end
      f:write(table.concat(chunk)); f:close()
      say("frame " .. emu.framecount() .. " dumped memory to " .. st[2] .. ".bin")
    elseif st[1] == "watch" then
      table.insert(watches, {addr = st[2], size = st[3], last = nil})
    elseif st[1] == "poke" then
      if st[3] == 1 then memory.write_u8(st[2], st[4], "RDRAM")
      elseif st[3] == 2 then memory.write_u16_be(st[2], st[4], "RDRAM")
      else memory.write_u32_be(st[2], st[4], "RDRAM") end
      say(string.format("frame %%d poke [%%06X] = %%d", emu.framecount(), st[2], st[4]))
    elseif st[1] == "record" then
      for i = 1, st[2] do
        advance()
        if i %% st[3] == 0 then client.screenshot(string.format("%%s/%%s_%%05d.png", out, st[4], emu.framecount())) end
      end
      say("frame " .. emu.framecount() .. " recorded " .. st[4])
    elseif st[1] == "shot" then
      client.screenshot(out .. "/" .. st[2] .. ".png")
      say("frame " .. emu.framecount() .. " shot " .. st[2])
    end
  end
end)
if not ok then say("ERROR " .. tostring(err)) end
say("done")
log:close()
client.exit()
'''


def make_sheets(shots, folder, cols=4, rows=4, size=(320, 240)):
    """Contact sheets of the screenshots, skipping ones identical to the one before."""
    from PIL import Image, ImageDraw
    folder.mkdir(exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    kept = []
    last = None
    for path in shots:
        data = Image.open(path).convert("RGB").resize(size)
        raw = data.tobytes()
        if raw != last:
            kept.append((path.stem, data))
            last = raw
    per = cols * rows
    for page in range(0, len(kept), per):
        sheet = Image.new("RGB", (cols * size[0], rows * (size[1] + 14)), (40, 40, 40))
        draw = ImageDraw.Draw(sheet)
        for i, (label, img) in enumerate(kept[page:page + per]):
            x, y = (i % cols) * size[0], (i // cols) * (size[1] + 14)
            sheet.paste(img, (x, y + 14))
            draw.text((x + 2, y + 1), label, fill=(255, 255, 0))
        sheet.save(folder / f"sheet_{page // per:02d}.png")
    print(f"{len(kept)} distinct screenshots on {(len(kept) + per - 1) // per} contact sheets in {folder}")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    name, plan_name = sys.argv[1], sys.argv[2]
    rom = L.WORK_DIR / "build" / f"{name}.z64"
    if name == "original":
        rom = L.find_rom()
    out = L.WORK_DIR / "harness" / name / plan_name
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    steps = []
    timeout = TIMEOUT
    core = "ares"
    autoshot = "nil"
    sheet = (4, 4, 320, 240)
    for n, line in enumerate((PLANS / f"{plan_name}.txt").read_text(encoding="utf-8-sig").splitlines(), 1):
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "wait":
            steps.append(f'  {{"wait", {int(parts[1])}}},')
        elif parts[0] == "press":
            steps.append(f'  {{"press", "{parts[1]}", {int(parts[2]) if len(parts) > 2 else 4}}},')
        elif parts[0] == "watch":
            steps.append(f'  {{"watch", 0x{int(parts[1], 16):X}, {int(parts[2])}}},')
        elif parts[0] == "poke":
            steps.append(f'  {{"poke", 0x{int(parts[1], 16):X}, {int(parts[2])}, {int(parts[3])}}},')
        elif parts[0] == "record":
            steps.append(f'  {{"record", {int(parts[1])}, {int(parts[2])}, "{len(steps):03d}_{parts[3]}"}},')
        elif parts[0] == "shot":
            steps.append(f'  {{"shot", "{len(steps):03d}_{parts[1]}"}},')
        elif parts[0] in ("save", "load"):
            steps.append(f'  {{"{parts[0]}", "{parts[1]}"}},')
        elif parts[0] == "dumpram":
            steps.append(f'  {{"dumpram", "{parts[1]}"}},')
        elif parts[0] == "findpal":
            steps.append('  {"findpal"},')
        elif parts[0] == "core":
            core = parts[1]
        elif parts[0] == "timeout":
            timeout = int(parts[1])
        elif parts[0] == "autoshot":
            autoshot = str(int(parts[1]))
        elif parts[0] == "sheet":
            sheet = tuple(int(p) for p in parts[1:5])
        else:
            raise SystemExit(f"plan line {n}: unknown step {parts[0]!r}")
    script = out / "run.lua"
    script.write_text(LUA % {"out": out.as_posix(), "steps": "\n".join(steps), "autoshot": autoshot}, encoding="utf-8")
    config = L.WORK_DIR / "harness" / "bizhawk_config.ini"
    if core == "mupen":
        # a second config that stays on BizHawk's default N64 core, to test ROM recognition
        config = L.WORK_DIR / "harness" / "bizhawk_config_mupen.ini"
        if not config.exists():
            config.write_text('{"PreferredCores": {"N64": "Mupen64Plus"}}', encoding="utf-8")
    # BizHawk's default N64 core (Mupen64Plus) shows a black screen for ROMs it does not
    # recognise, because it picks settings by ROM identity. The Ares64 core does not.
    elif config.exists():
        text = config.read_text(encoding="utf-8")
        if '"N64": "Mupen64Plus"' in text:
            config.write_text(text.replace('"N64": "Mupen64Plus"', '"N64": "Ares64"'), encoding="utf-8")
    else:
        config.write_text('{"PreferredCores": {"N64": "Ares64"}}', encoding="utf-8")
    cmd = [str(BIZHAWK), f"--config={config}", f"--lua={script}", str(rom)]
    try:
        subprocess.run(cmd, cwd=BIZHAWK.parent, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"BizHawk did not finish within {timeout} seconds and was stopped.")
    log = out / "log.txt"
    print(log.read_text(encoding="utf-8") if log.exists() else "no log written: the script never started")
    shots = sorted(out.glob("*.png"))
    print(f"{len(shots)} screenshots in {out}")
    make_sheets(shots, out / "sheets", cols=sheet[0], rows=sheet[1], size=sheet[2:4])
    return 0


if __name__ == "__main__":
    sys.exit(main())
