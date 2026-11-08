"""T-16 Skyhopper selectable on every mission that allows the X-wing (not snowspeeder missions),
with its own hangar bay between the V-wing and the Y-wing. Cave source: caves\t16_craft.s.
Adds a new 0x1000-byte section ".t16" after the exe's last section (VA 0x7FF000 on the plain exe,
0x800000 after the .conv / .bfnf section of the other mods); the cave is assembled for that VA.
usage: build_t16.py [base rllasers] [out t16] [x -24.9] [z -14.9] [yaw 70] [cam1 0.06] [cam2 0.073]
                    [aimdown 7.5] [aimdist 25]
"""
import hashlib, os, re, struct, subprocess, sys

GAME = r"G:\Game Files\LucasArts\Star Wars Rogue Squadron"
a = sys.argv[1:]
BASE_EXE = a[0] if len(a) > 0 else "rllasers"
OUT = a[1] if len(a) > 1 else "t16"
X = float(a[2]) if len(a) > 2 else -24.9           # T-16 bay position (hangar floor, y = 28.44)
Z = float(a[3]) if len(a) > 3 else -14.9
YAW = float(a[4]) if len(a) > 4 else 70.0
CAM1 = float(a[5]) if len(a) > 5 else 0.06          # camera route parameter for the bay
CAM2 = float(a[6]) if len(a) > 6 else 0.073         # look-at route parameter for the bay
AIMDOWN = float(a[7]) if len(a) > 7 else 7.5        # T-16 shots aimed this many degrees below the nose line
AIMDIST = float(a[8]) if len(a) > 8 else 25.0       # no-target shots meet that line this far ahead
d = bytearray(open(os.path.join(GAME, "Rogue Squadron.%s.EXE" % BASE_EXE), "rb").read())
D = 0x400C00                      # .text VA - file offset
T16OBJ = 47

# --- new section ".t16" ------------------------------------------------------------------------
def add_section(d, name=b".t16", size=0x1000):
    """Append a RWX section after the last one; returns its VA. Same layout the installer writes."""
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    tab = pe + 24 + opt
    vs, va, rs, ro = struct.unpack_from("<IIII", d, tab + (n - 1) * 40 + 8)
    assert name not in [bytes(d[tab + k * 40:tab + k * 40 + 8]).rstrip(b"\0") for k in range(n)], "already has .t16"
    new_va = (va + max(vs, rs) + 0xFFF) & ~0xFFF
    assert len(d) % 0x200 == 0 and len(d) == ro + rs, "section data must end the file"
    h = tab + n * 40
    assert h + 40 <= struct.unpack_from("<I", d, pe + 0x54)[0] and not any(d[h:h + 40]), "no room for a section header"
    struct.pack_into("<8sIIIIIIHHI", d, h, name, size, new_va, size, len(d), 0, 0, 0, 0, 0xE0000020)
    struct.pack_into("<H", d, pe + 6, n + 1)
    struct.pack_into("<I", d, pe + 0x50, new_va + size)          # SizeOfImage
    return 0x400000 + new_va

BASE = add_section(d)
C = len(d)                                         # file offset of BASE
d += bytes(0x1000)

# --- assemble ----------------------------------------------------------------------------------
BIN = r"G:\msys64\mingw64\bin"
HERE = os.path.dirname(os.path.abspath(__file__))
obj, binf = os.path.join(HERE, "t16.o"), os.path.join(HERE, "t16.bin")
subprocess.run([BIN + r"\as.exe", "--32", "--defsym", "BASE=0x%X" % BASE, "-o", obj,
                os.path.join(HERE, "caves", "t16_craft.s")], check=True)
syms = {}
for line in subprocess.run([BIN + r"\nm.exe", obj], capture_output=True, text=True, check=True).stdout.splitlines():
    f = line.split()
    if len(f) == 3 and f[1] in "tT":
        syms[f[2]] = BASE + int(f[0], 16)
subprocess.run([BIN + r"\objcopy.exe", "-O", "binary", "-j", ".text", obj, binf], check=True)
code = open(binf, "rb").read(); os.remove(obj); os.remove(binf)
assert len(code) <= 0xA00 and not any(code[0x400:0x700]), "cave code overlaps the data at +0x400..+0x700"
d[C:C + len(code)] = code

# --- data --------------------------------------------------------------------------------------
DD = 0x401800                     # .data VA - file offset
def rd(va, n): return bytes(d[va - DD:va - DD + n])
def put(off, data): d[C + off:C + off + len(data)] = data

objtype = bytearray(49); objtype[0:9] = rd(0x5F1A58, 9); objtype[T16OBJ] = 7
assert bytes(objtype[0:9]) == bytes.fromhex("000400020103050608")
put(0x400, objtype)                                              # OBJTYPE
posobj = rd(0x5F1A68, 8) + bytes([T16OBJ]); posty = rd(0x5F1A70, 8) + bytes([7])
assert posobj[:8] == bytes.fromhex("0208050406010307") and posty[:8] == bytes.fromhex("0008030105040206")
put(0x480, posobj); put(0x490, posty)                            # POSOBJ, POSTYPE
# bay order: X-wing 0 > Naboo 1 > V-wing 2 > T-16 8 > Y-wing 3 > Falcon 4 > speeder 5 > A-wing 6 (TIE 7 is special)
NEXT = [1, 2, 8, 4, 5, 6, 0, 0, 3]
PREV = [6, 0, 1, 8, 3, 4, 5, 6, 2]
put(0x4A0, bytes(NEXT)); put(0x4B0, bytes(PREV))
put(0x4C0, rd(0x5F1A78, 32) + struct.pack("<f", CAM1))          # CAM1
put(0x4F0, rd(0x5F1A98, 32) + struct.pack("<f", CAM2))          # CAM2
put(0x520, b"+t16#\0"); put(0x530, b"pl_crafts/t16\0")

DAT = open(os.path.join(GAME, "DATA", "OUT", "DATA.DAT"), "rb").read()
# placement: copy the V-wing's hangar record (name follows its data) and move it
vw = 0x199B47C
assert struct.unpack_from("<4I", DAT, vw) == (6, 3, 0x6C, 0x64) and DAT[vw + 0x64:vw + 0x69] == b"vwing"
rec = bytearray(DAT[vw:vw + 0x40])
struct.pack_into("<3f", rec, 0x10, X, 28.44, Z)
struct.pack_into("<3f", rec, 0x1C, 0.0, YAW, 0.0)
put(0x560, rec)
# launch route: the V-wing's route header, own points (start, start, mid, exit, exit)
m = DAT.index(b"awing_route\0", 0x199D000)             # record after this name = V-wing route
h = m + 12
assert struct.unpack_from("<HH", DAT, h) == (8, 3) and struct.unpack_from("<II", DAT, h + 0x1C) == (5, 0x48)
hdr = bytearray(DAT[h:h + 0x48])
Y = 28.40
pts = [(X, Z), (X, Z), (-10.0, -3.5), (0.01, 7.62), (0.01, 7.62)]
length = sum(((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5 for i in range(4))
struct.pack_into("<3f", hdr, 0x10, 0.0, Y, 0.0)          # origin (points are absolute x/z)
struct.pack_into("<IIf", hdr, 0x1C, 5, BASE + 0x5A0 + 0x48, length)
put(0x5A0, hdr)
put(0x5E8, b"".join(struct.pack("<3f", px, 0.0, pz) for px, pz in pts))
put(0x5E8 + 60, struct.pack("<3f", 0.0, 0.5, 1.0))
put(0x640, struct.pack("<2f", 1.0, 0.0001))                     # ONE, EPS
import math
put(0x648, struct.pack("<2f", AIMDIST, math.tan(math.radians(AIMDOWN))))   # DEFDIST, TANDOWN

# --- patches -----------------------------------------------------------------------------------
def patch(va, old, new):
    o = va - D
    assert bytes(d[o:o + len(old)]) == old, "bytes differ at %X: %s" % (va, d[o:o + len(old)].hex())
    d[o:o + len(new)] = new
def rel(va, target): return struct.pack("<i", target - (va + 5))
def callpatch(va, target, total):
    o = va - D
    return b"\xe8" + rel(va, target) + b"\x90" * (total - 5)

# relocate bay / object tables: every reference in .text, counts checked
TEXT = (0x400, 0x400 + 0x1BE000)
for old, new, count in ((0x5F1A58, BASE + 0x400, 11), (0x6484F7, BASE + 0x440, 3), (0x6484F8, BASE + 0x441, 1),
                        (0x5F1A68, BASE + 0x480, 6), (0x5F1A6E, BASE + 0x486, 1), (0x5F1A70, BASE + 0x490, 8),
                        (0x5F1A78, BASE + 0x4C0, 15), (0x5F1A98, BASE + 0x4F0, 15)):
    pat = struct.pack("<I", old)
    hits = [m.start() for m in re.finditer(re.escape(pat), bytes(d[TEXT[0]:TEXT[1]]))]
    assert len(hits) == count, (hex(old), len(hits))
    for h in hits:
        d[TEXT[0] + h:TEXT[0] + h + 4] = struct.pack("<I", new)

S = syms
patch(0x43D043, bytes.fromhex("8b45fc8be55dc3"), b"\xe9" + rel(0x43D043, S["mask_end"]) + b"\x90\x90")
patch(0x4413DF, bytes.fromhex("a148427000"), b"\xe9" + rel(0x4413DF, S["hangar_init"]))
for va in (0x442977, 0x442DFA):
    patch(va, bytes.fromhex("83bd6cffffff08"), callpatch(va, S["ship_loop"], 7))
patch(0x442E9C, bytes.fromhex("8b856cffffff c704850c84640000000000".replace(" ", "")), callpatch(0x442E9C, S["ship_clear"], 17))
patch(0x4454E7, bytes.fromhex("d80c8db41a5f00"), callpatch(0x4454E7, S["obj_fmul"], 7))
patch(0x447076, bytes.fromhex("8b0c85641b5f00"), callpatch(0x447076, S["obj_speech"], 7))
patch(0x441C51, b"\xe8" + rel(0x441C51, 0x443015), b"\xe8" + rel(0x441C51, S["register"]))
patch(0x441D63, b"\xe8" + rel(0x441D63, 0x46FA6C), b"\xe8" + rel(0x441D63, S["load_models"]))
patch(0x442030, b"\xe8" + rel(0x442030, 0x4CBA60), b"\xe8" + rel(0x442030, S["placement"]))
patch(0x44226C, b"\xe8" + rel(0x44226C, 0x4CBB36), b"\xe8" + rel(0x44226C, S["route"]))
# object count 48 -> 49 (the level environment object is now 48)
patch(0x44186B, bytes.fromhex("66c705dc8464003000"), bytes.fromhex("66c705dc8464003100"))
for va, op in ((0x441C84, "83f8"), (0x44265B, "83f9"), (0x443201, "83f8")):
    patch(va, bytes.fromhex(op + "30"), bytes.fromhex(op + "31"))
# bay navigation right / left: next/prev bay from a table instead of +-1 with wrap at 6
def nav(va, end, tbl, slot, old):
    body = (b"\x0f\xb6\x0d" + struct.pack("<I", 0x6481D8) +              # movzx ecx, byte [0x6481d8]
            b"\x0f\xb6\x89" + struct.pack("<I", tbl) +                   # movzx ecx, byte [ecx+tbl]
            b"\x89\x8d" + struct.pack("<i", slot))                        # mov [ebp+slot], ecx
    body += b"\xe9" + struct.pack("<i", end - (va + len(body) + 5))
    o = va - D
    assert bytes(d[o:o + len(old) // 2]) == bytes.fromhex(old), (hex(va), d[o:o + 12].hex())
    d[o:end - D] = body + b"\x90" * (end - va - len(body))
nav(0x4448F0, 0x44491A, BASE + 0x4A0, -0x11C, "33c98a0dd881640083f906")   # pos == 6 ? 0 : pos+1
nav(0x444999, 0x4449C1, BASE + 0x4B0, -0x120, "33c0a0d881640085c0")       # pos == 0 ? 6 : pos-1

# --- T-16 weapons ------------------------------------------------------------------------------
# lasers aim like the X-wing's: finder at the end of the T-16 update, bolt turned onto the aim point
patch(0x41D09C, b"\xe8" + rel(0x41D09C, 0x41EF0D), b"\xe8" + rel(0x41D09C, S["t16_find"]))
patch(0x41CE71, bytes.fromhex("83c4188b45cc"), callpatch(0x41CE71, S["t16_aim"], 6))
# laser sound: T16_SHOT (0x31, 100, 50) -> XW_SHOT single shot (2, 90, 40) like the X-wing
patch(0x41CED9, bytes.fromhex("6a326a646a31"), bytes.fromhex("6a286a5a6a02"))
# secondary weapon id for craft type 7: none (0xFF) -> 5 = the X-wing's proton torpedoes
patch(0x43D20C, bytes.fromhex("c645fcff"), bytes.fromhex("c645fc05"))
# secondary ammo for craft type 7 (0x43BE72 table): 0xFF (infinite, shows 99) -> 6 like the X-wing
patch(0x43BED3, bytes.fromhex("c645fcff"), bytes.fromhex("c645fc06"))
# hangar: the T-16 always skips the launch fly-out (it crashed at the end of it)
# (off again: that crash was the 8-byte info block overflow, fixed below; set SKIP_FLYOUT to restore)
SKIP_FLYOUT = False
if SKIP_FLYOUT:
    patch(0x444F19, bytes.fromhex("2500900000" "85c0"), callpatch(0x444F19, S["t16_skip"], 7))
# dumbfire torpedoes from the T-16 aim like its lasers (shared torpedo code, player + T-16 only)
patch(0x423F24, bytes.fromhex("83c418" "8b15fc4d7000"), callpatch(0x423F24, S["t16_torp"], 9))
# cutscenes show an X-wing for the T-16 (the end cutscene crashed with the T-16 model)
# (removed: showing an X-wing in cutscenes crashed mid-mission - its model is not loaded)
# patch(0x42A178, bytes.fromhex("8a1521427000"), callpatch(0x42A178, S["cut_craft"], 6))
# T-16 fire rate: 0.3 s between shots (3.3/s, slowest of all craft) -> 0.1 s like the X-wing's
# single fire. +0x164 = interval, +0x174 = same value (T-16 init 0x41C780)
for va in (0x41C998, 0x41C9BF):
    o = va - D
    assert d[o] == 0xC7 and abs(struct.unpack_from("<f", d, o + 6)[0] - 0.3) < 1e-6, hex(va)
    struct.pack_into("<f", d, o + 6, 0.1)
# T-16 create (handler 0x41D0A8): its player info block was only 8 bytes, but the finder data the
# X-wing keeps there (target +0x1A, aim point +0x1C..+0x27) needs the X-wing's 0x28 -> t16_find
# wrote past the block every frame (heap corruption: crashes at fly-out / mid-mission / end cutscene)
patch(0x41D10C, bytes.fromhex("6a08"), bytes.fromhex("6a28"))
# T-16 destroy (handler 0x41D0A8): it freed its info block (rec+0xBC) BEFORE the weapon / target
# cleanup 0x423B20 + 0x41EE5A(0), which reads through a pointer into that block and frees two
# buffers -> use-after-free / double free (crash in free 0x584980 at mission end). Same calls in the
# X-wing's order (0x4258BA): cleanups first, then free(info), then 0x4710E0(model).
va = 0x41D39B
old = (bytes.fromhex("8b4df8" "8b91bc000000" "52") + b"\xe8" + rel(va + 10, 0x584960) +
       bytes.fromhex("8b45f8" "8b08" "51") + b"\xe8" + rel(va + 21, 0x4710E0) + bytes.fromhex("83c404") +
       b"\xe8" + rel(va + 29, 0x423B20) + bytes.fromhex("6a00") + b"\xe8" + rel(va + 36, 0x41EE5A) + bytes.fromhex("83c404"))
new = (b"\xe8" + rel(va, 0x423B20) + bytes.fromhex("6a00") + b"\xe8" + rel(va + 7, 0x41EE5A) + bytes.fromhex("83c404") +
       bytes.fromhex("8b4df8" "8b91bc000000" "52") + b"\xe8" + rel(va + 25, 0x584960) +
       bytes.fromhex("8b45f8" "8b08" "51") + b"\xe8" + rel(va + 36, 0x4710E0) + bytes.fromhex("83c404"))
assert len(old) == len(new) == 0x2C
patch(va, old, new)

out = os.path.join(GAME, "Rogue Squadron.%s.EXE" % OUT)
open(out, "wb").write(d)
print("T-16 bay: %d bytes of cave, pos (%g, %g) yaw %g, cam %g/%g -> %s, md5 %s"
      % (len(code), X, Z, YAW, CAM1, CAM2, os.path.basename(out), hashlib.md5(d).hexdigest().upper()))
