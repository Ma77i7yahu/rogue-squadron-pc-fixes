"""Builds Rogue Squadron.convergence.EXE (laser convergence v4) for testing.

Base = the live mod set (smallmoves exe: deadzones, aim-assist off, linear,
widescreen, small moves) with the aim-assist cones put back, because v4 needs
the game's own target finder to run. The PE header for the new .conv section
is copied from the old v3 convergence build.
usage: build_conv.py [min_depth]
"""
import hashlib, os, shutil, struct, subprocess, sys

GAME = r"G:\Game Files\LucasArts\Star Wars Rogue Squadron"
BIN = r"G:\msys64\mingw64\bin"
HERE = os.path.dirname(os.path.abspath(__file__))
def rd(n): return bytearray(open(os.path.join(GAME, "Rogue Squadron.%s.EXE" % n), "rb").read())

MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
AIM = [0x00C19A, 0x017BEB, 0x018DE3, 0x01B448, 0x0200D5, 0x024964, 0x025535]
HOOK_VA, HOOK_OFF = 0x40C91F, 0x40C91F - 0x400C00

orig, base = rd("original"), rd("smallmoves")
old3 = os.path.join(GAME, "Rogue Squadron.convergence-v3.EXE")
if not os.path.exists(old3):
    shutil.copy(os.path.join(GAME, "Rogue Squadron.convergence.EXE"), old3)
v3 = rd("convergence-v3")
for o in AIM: base[o:o + 4] = orig[o:o + 4]
# Each craft only turns a bolt part of the way toward the aim point (TIE 0.8,
# Naboo 0.4/0.8, Snowspeeder 0.6, V-wing 0.4/0.8/0.6, X-wing 0.4/0.8). Full
# convergence needs the whole turn. Each constant is referenced once, inside the
# craft's "has target" fire block.
TURN = [0x5BF674, 0x5BF6AC, 0x5BF6B0, 0x5BF72C, 0x5BF800, 0x5BF804, 0x5BF808, 0x5BF8E0, 0x5BF8E4]
for va in TURN:
    o = va - 0x400C00
    assert 0.3 < struct.unpack_from("<f", orig, o)[0] < 0.9
    struct.pack_into("<f", base, o, 1.0)

obj, binf = os.path.join(HERE, "conv.o"), os.path.join(HERE, "conv.bin")
subprocess.run([BIN + r"\as.exe", "--32", "-o", obj, os.path.join(HERE, "caves", "laser_convergence.s")], check=True)
subprocess.run([BIN + r"\objcopy.exe", "-O", "binary", "-j", ".text", obj, binf], check=True)
code = open(binf, "rb").read()
os.remove(obj); os.remove(binf)
assert len(code) <= 0x300

d = base
d[0:0x400] = v3[0:0x400]                      # headers incl. .conv section entry
assert d[0x400:] == base[0x400:]
assert bytes(d[HOOK_OFF:HOOK_OFF + 5]) == bytes.fromhex("83c41c5dc3")
d[HOOK_OFF:HOOK_OFF + 5] = b"\xe9" + struct.pack("<i", 0x7FF000 - (HOOK_VA + 5))
# settings store: GENERAL index 5 in the Get (0x4DCE99) and Set (0x4DCFEE) handlers
for va, old, cave in ((0x4DCE99, "8b55e88955c0837dc0067402eb17", 0x7FF100),
                      (0x4DCFEE, "8b550c8955f4837df4067402eb17", 0x7FF140)):
    o = va - 0x400C00
    assert bytes(d[o:o + 14]) == bytes.fromhex(old), hex(va)
    d[o:o + 14] = b"\xe9" + struct.pack("<i", cave - (va + 5)) + b"\x90" * 9
sec = bytearray(0x1000)
sec[:len(code)] = code
struct.pack_into("<f", sec, 0x300, MIN)

# Help-line text: the settings screens look up an object's explanation in a
# null-terminated (name, text) table at 0x6056E8 with no room to grow, so copy
# it into this section with a generalbox_8 entry and repoint the lookup.
TAB_OFF, TAB_END = 0x6056E8 - 0x401800, 0x2043B8
assert struct.unpack_from("<II", orig, TAB_END - 8) == (0, 0)
table = bytearray(orig[TAB_OFF:TAB_END - 8])
NEW_TAB, NEW_STR = 0x400, 0xA00
s_name = b"generalbox_8\0"
s_text = b"/TXT_EXP_GENERALBOX_8/When on, lasers converge at the range of the target in your crosshairs.\0"
sec[NEW_STR:NEW_STR + len(s_name)] = s_name
sec[NEW_STR + 0x20:NEW_STR + 0x20 + len(s_text)] = s_text
table += struct.pack("<II", 0x7FF000 + NEW_STR, 0x7FF000 + NEW_STR + 0x20) + bytes(8)
assert NEW_TAB + len(table) <= NEW_STR
sec[NEW_TAB:NEW_TAB + len(table)] = table
for va, old in ((0x4DD14B, 0x6056E8), (0x4DD15F, 0x6056E8), (0x4DD179, 0x6056EC), (0x4DD1A5, 0x6056EC)):
    o = va - 0x400C00
    assert struct.unpack_from("<I", d, o)[0] == old, hex(va)
    struct.pack_into("<I", d, o, old - 0x6056E8 + 0x7FF000 + NEW_TAB)
# section is now 0x1000 bytes (VirtualSize, SizeOfRawData); SizeOfImage already 0x400000
assert d[0x298:0x29D] == b".conv"
struct.pack_into("<I", d, 0x2A0, 0x1000)
struct.pack_into("<I", d, 0x2A8, 0x1000)
assert struct.unpack_from("<I", d, 0x128)[0] == 0x400000
d += sec
open(os.path.join(GAME, "Rogue Squadron.convergence.EXE"), "wb").write(d)
print("code %d bytes, min depth %g, md5 %s" % (len(code), MIN, hashlib.md5(d).hexdigest().upper()))
