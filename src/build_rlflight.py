"""Builds Rogue Squadron.rlflight.EXE: Rogue Leader style flight on top of the
current mod set (Rogue Squadron.convergence.EXE, which owns the .conv section).
usage: build_rlflight.py [normal_dps 36] [tight_k 0] [bank_deg 50] [bank_rate 2.0]
                         [ramp_in_s 0.3] [ramp_out_s 0.3] [pitch_k 0] [button 9]
Holding the button blends to the game's own (stock) flight; tight_k/pitch_k add extra on top.
"""
import hashlib, os, struct, subprocess, sys

GAME = r"G:\Game Files\LucasArts\Star Wars Rogue Squadron"
BIN = r"G:\msys64\mingw64\bin"
HERE = os.path.dirname(os.path.abspath(__file__))
a = [float(x) for x in sys.argv[1:]]
WN, TK, BANK, KR, TIN, TOUT, PK, BUTTON = (a + [36.0, 0.0, 50.0, 2.0, 0.3, 0.3, 0.0, 9][len(a):])[:8]
BUTTON = int(BUTTON)
RMAX, UPMIN = 150.0, 0.1
import math
V_START, V_END = 35.0, 55.0     # climb/dive angle where the blend to stock flight starts / ends
U_START, U_END = 0.4, 0.1       # up.y (cos of roll) where the blend to stock starts / ends

d = bytearray(open(os.path.join(GAME, "Rogue Squadron.convergence.EXE"), "rb").read())
SEC, CODE, DATA = 0x260A00, 0xB00, 0xF00          # .conv raw offset, our offsets in it
assert d[0x298:0x29D] == b".conv" and len(d) == SEC + 0x1000
assert not any(d[SEC + CODE:SEC + 0x1000]), "code area not empty"

obj, binf = os.path.join(HERE, "rl.o"), os.path.join(HERE, "rl.bin")
subprocess.run([BIN + r"\as.exe", "--32", "-o", obj, os.path.join(HERE, "caves", "rl_flight.s")], check=True)
subprocess.run([BIN + r"\objcopy.exe", "-O", "binary", "-j", ".text", obj, binf], check=True)
code = open(binf, "rb").read()
os.remove(obj); os.remove(binf)
assert len(code) <= DATA - CODE, hex(len(code))
d[SEC + CODE:SEC + CODE + len(code)] = code

D = SEC + DATA
struct.pack_into("<5I", d, D, 0, 0, 0, 0, 0)
struct.pack_into("<11f", d, D + 0x14, 1 / TIN, 1 / TOUT, WN, TK, PK, BANK, KR, RMAX, UPMIN, 57.29578, 0.0)
struct.pack_into("<4I", d, D + 0x40, *[0x7FFFFFFF] * 4)
struct.pack_into("<4I", d, D + 0x50, *[0x80000000] * 4)
struct.pack_into("<2f", d, D + 0x60, 1.0, -1.0)

def hook(va, old, to):
    o = va - 0x400C00
    assert bytes(d[o:o + len(old) // 2]) == bytes.fromhex(old), hex(va)
    n = len(old) // 2
    d[o:o + n] = b"\xe9" + struct.pack("<i", to - (va + 5)) + b"\x90" * (n - 5)

V = 0x7FF000
hook(0x40F530, "8b55088b82b8000000", V + CODE)
hook(0x40FB7D, "8b4508d980dc000000d8a544ffffff8b4d08d999dc000000", V + CODE + 0x200)
hook(0x41052E, "8b4d08d981d8000000", V + CODE + 0x280)
struct.pack_into("<I", d, D + 0x68, 1 << (BUTTON - 1))   # tight-turn joystick button
sa, sb = math.sin(math.radians(V_START)), math.sin(math.radians(V_END))
struct.pack_into("<3f", d, D + 0x74, sa, 1 / (sb - sa), U_START)
struct.pack_into("<f", d, D + 0xA0, 1 / (U_START - U_END))

out = os.path.join(GAME, "Rogue Squadron.rlflight.EXE")
open(out, "wb").write(d)
print("button %d, turn %g deg/s (tight x%g at full stick), bank %g deg, bank rate %g/s, ramp %g/%g s, pitch k %g, code %d bytes"
      % (BUTTON, WN, 1 + TK, BANK, KR, TIN, TOUT, PK, len(code)))
print("md5", hashlib.md5(d).hexdigest().upper())
