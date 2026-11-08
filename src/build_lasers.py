"""Faster player lasers (Rogue Leader-like): bolt speed x SPEED, fire rate x RATE.
Applies to the player craft's own fire code only (AI fire calls are separate and untouched).
usage: build_lasers.py [speed_mult 2.0] [rate_mult 1.0] [base rlflight] [out rllasers] [bolt_w 2] [bolt_l 4] [stretch_a8 1] [stretch_b4 1]  (+0xA8 = bolt length, +0xB4 = thickness)
"""
import hashlib, os, struct, sys

GAME = r"G:\Game Files\LucasArts\Star Wars Rogue Squadron"
a = sys.argv[1:]
SPEED = float(a[0]) if len(a) > 0 else 2.0
RATE = float(a[1]) if len(a) > 1 else 1.0   # user prefers the stock fire rate
BASE = a[2] if len(a) > 2 else "rlflight"
OUT = a[3] if len(a) > 3 else "rllasers"
d = bytearray(open(os.path.join(GAME, "Rogue Squadron.%s.EXE" % BASE), "rb").read())
D = 0x400C00

def scale_push(va, mult, allowed):
    """push imm32 float at va (opcode 68) -> imm * mult"""
    o = va - D
    assert d[o] == 0x68, hex(va)
    v = struct.unpack_from("<f", d, o + 1)[0]
    assert v in allowed, (hex(va), v)
    struct.pack_into("<f", d, o + 1, v * mult)
    return v

# bolt speed argument of each player craft's FireWeapon (0x4C3D33) call
FIRE_SPEED = [0x40CAA2, 0x416DAD, 0x416E06, 0x4184DE, 0x419700, 0x41B747, 0x41B7CC, 0x41B81F,
              0x41B87F, 0x41CE7E, 0x420804, 0x42511B, 0x4260D7]
for va in FIRE_SPEED:
    scale_push(va, SPEED, (12.5, 15.0))

# the same speed is the lead-time argument of each craft's aim-assist finder call (0x40C8FC)
FINDER_CALLS = [0x40CDB6, 0x41880A, 0x419A01, 0x41C06D, 0x420CF4, 0x425582, 0x426151]
for call in FINDER_CALLS:
    o = call - D
    for k in range(o - 0x30, o):          # first push before the call = 6th argument (bolt speed)
        if d[k] == 0x68 and struct.unpack_from("<f", d, k + 1)[0] in (10.0, 12.5, 15.0):   # Y-wing turret uses 10
            scale_push(k + D, SPEED, (10.0, 12.5, 15.0))
            break
    else:
        raise SystemExit("no speed push before finder call %X" % call)

# fire intervals in each player craft's setup: mov dword [reg+0x164 / 0x168], imm32
INTERVALS = [0x40BDD5, 0x4168AE, 0x417F48, 0x418F11, 0x41A768, 0x41C998, 0x41FBA1, 0x42466B, 0x425C94,
             0x40BDE2, 0x4168BB, 0x417F55, 0x418F1E, 0x41C9A5, 0x41FBAE, 0x424678, 0x425CA1]
for va in INTERVALS:
    o = va - D
    assert d[o] == 0xC7 and d[o + 2:o + 4] in (b"\x64\x01", b"\x68\x01"), hex(va)
    v = struct.unpack_from("<f", d, o + 6)[0]
    assert 0.04 < v < 0.6, (hex(va), v)
    struct.pack_into("<f", d, o + 6, v / RATE)

# player bolt look pair at 0x601D28 (enemy bolts use 0x601D20 = 0.7, 1.2); stock 2.0, 4.0.
# Referenced only by the laser create handler (0x4C4324). Believed to be width, length.
BOLT_W = float(a[4]) if len(a) > 4 else 2.0
BOLT_L = float(a[5]) if len(a) > 5 else 4.0
o = 0x601D28 - 0x401800
assert struct.unpack_from("<2f", d, o) == (2.0, 4.0)
struct.pack_into("<2f", d, o, BOLT_W, BOLT_L)

# Stretch the player's bolt model (test): scale its forward / second axes after velocity is set.
STR_L = float(a[6]) if len(a) > 6 else 1.0
STR_W = float(a[7]) if len(a) > 7 else 1.0
if STR_L != 1.0 or STR_W != 1.0:
    import subprocess
    BIN = r"G:\msys64\mingw64\bin"
    HERE = os.path.dirname(os.path.abspath(__file__))
    obj, binf = os.path.join(HERE, "bs.o"), os.path.join(HERE, "bs.bin")
    subprocess.run([BIN + r"\as.exe", "--32", "-o", obj, os.path.join(HERE, "caves", "bolt_stretch.s")], check=True)
    subprocess.run([BIN + r"\objcopy.exe", "-O", "binary", "-j", ".text", obj, binf], check=True)
    code = open(binf, "rb").read(); os.remove(obj); os.remove(binf)
    SEC = 0x260A00
    assert d[0x298:0x29D] == b".conv" and len(d) == SEC + 0x1000
    assert len(code) <= 0xF0 and not any(d[SEC + 0x900:SEC + 0xA00]), "cave area 0x7FF900 not free"
    d[SEC + 0x900:SEC + 0x900 + len(code)] = code
    struct.pack_into("<2f", d, SEC + 0x9F0, STR_L, STR_W)
    HOOK = 0x4C43BE
    o = HOOK - D
    assert bytes(d[o:o + 9]) == bytes.fromhex("8b4dac81c19c000000"), "hook bytes differ"
    d[o:o + 9] = b"\xe9" + struct.pack("<i", 0x7FF900 - (HOOK + 5)) + b"\x90" * 4

out = os.path.join(GAME, "Rogue Squadron.%s.EXE" % OUT)
open(out, "wb").write(d)
print("lasers: speed x%g, fire rate x%g, bolt %gx%g, stretch A8 x%g B4 x%g -> %s, md5 %s" % (SPEED, RATE, BOLT_W, BOLT_L, STR_L, STR_W, os.path.basename(out), hashlib.md5(d).hexdigest().upper()))
