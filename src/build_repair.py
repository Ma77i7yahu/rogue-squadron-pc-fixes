"""Every craft repairs itself: assembles caves/repair_all.s over the repair fn 40EBE8 in place.
Usage: build_repair.py <base exe> <out exe>"""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = r"G:\msys64\mingw64\bin"
VA, END, FILE_OFF = 0x40EBE8, 0x40ECCE, 0xE0CE - (0x40ECCE - 0x40EBE8)
# original bytes of the whole function (+ its jump/byte tables) must match before patching
ORIG_TABLE = bytes([0, 0, 3, 3, 3, 1, 3, 3, 2])

def assemble():
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        obj, out = os.path.join(tmp, "r.o"), os.path.join(tmp, "r.bin")
        subprocess.check_call([os.path.join(BIN, "as"), "--32", "-o", obj, os.path.join(HERE, "caves", "repair_all.s")])
        # only relative jumps and absolute addresses, so no link step is needed
        subprocess.check_call([os.path.join(BIN, "objcopy"), "-O", "binary", "-j", ".text", obj, out])
        return open(out, "rb").read()

def main(src, dst):
    code = assemble()
    size = END - VA
    assert len(code) <= size, "code too big: %d > %d" % (len(code), size)
    b = bytearray(open(src, "rb").read())
    assert b[FILE_OFF:FILE_OFF + 2] == b"\x55\x8b" and b[0xE0C5:0xE0CE] == ORIG_TABLE, "base exe has a changed repair fn"
    b[FILE_OFF:FILE_OFF + size] = code + b"\xCC" * (size - len(code))
    open(dst, "wb").write(b)
    print("repair fn: %d of %d bytes -> %s" % (len(code), size, dst))

if __name__ == "__main__":
    main(*sys.argv[1:3])
