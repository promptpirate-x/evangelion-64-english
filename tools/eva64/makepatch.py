"""Make the release patch for the Evangelion 64 English translation.

  makepatch.py <version>      e.g. makepatch.py 0.1

Rebuilds games\\eva64\\work\\build\\eva64_en.z64 from the scripts, makes an xdelta
patch against the original ROM in games\\eva64\\patch, then proves the patch works
by applying it to a fresh copy of the original and comparing the result.
Run it through makepatch.bat.
"""
import hashlib
import shutil
import subprocess
import sys

import eva64lib as L

XDELTA = L.WORKSPACE / "tools" / "xdelta3" / "xdelta3-3.1.0-x86_64.exe"
PATCH_DIR = L.GAME_DIR / "patch"


def sha1(path):
    return hashlib.sha1(path.read_bytes()).hexdigest().upper()


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    version = sys.argv[1]
    for step in ("makefont.py", "makeimages.py", "makescreens.py"):
        subprocess.run([sys.executable, str(L.TOOL_DIR / step)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(L.TOOL_DIR / "build.py"), "scripts\\strings_en.tsv", "eva64_en", "en"], check=True)
    subprocess.run([sys.executable, str(L.TOOL_DIR / "verify.py"), "eva64_en", "en"], check=True, stdout=subprocess.DEVNULL)
    original = L.find_rom()
    built = L.WORK_DIR / "build" / "eva64_en.z64"
    patch = PATCH_DIR / f"eva64_english_v{version}.xdelta"
    # xdelta3 cannot open paths with non-ASCII characters and is fussy about spaces: work on plain copies
    tmp = L.WORK_DIR / "patchtest"
    tmp.mkdir(exist_ok=True)
    src = tmp / "original.z64"
    shutil.copyfile(original, src)
    subprocess.run([str(XDELTA), "-e", "-9", "-S", "none", "-f", "-s", str(src), str(built), str(patch)], check=True)
    out = tmp / "patched.z64"
    subprocess.run([str(XDELTA), "-d", "-f", "-s", str(src), str(patch), str(out)], check=True)
    ok = out.read_bytes() == built.read_bytes()
    print(f"patch: {patch} ({patch.stat().st_size} bytes)")
    print(f"original SHA-1: {sha1(original)}")
    print(f"patched  SHA-1: {sha1(out)}")
    print("applying the patch to a fresh copy of the original reproduces the build:", "YES" if ok else "NO")
    shutil.rmtree(tmp)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
