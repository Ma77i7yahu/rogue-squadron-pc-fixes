"""Adds a "Laser Convergence" checkbox to the General Settings screen.

Edits GENERAL_P.SLB (a plain-text Sweet view: objects + C-like script) inside
Bundle.002 and repacks the bundle. The checkbox reads/writes GENERAL option 5
of the game's settings store, which the convergence exe patch adds.
usage: build_menu.py <original Bundle.002> <output Bundle.002>
"""
import struct, sys

src, dst = sys.argv[1], sys.argv[2]
b = bytearray(open(src, "rb").read())
assert b[0:4] == b"BUND" and b[8:12] == b"BNHD"
HD = 0x10
nh = struct.unpack(">I", b[12:16])[0]
DT_TAG = HD + nh
assert b[DT_TAG:DT_TAG + 4] == b"BNDT"
DT = DT_TAG + 8
ENT, ESZ, N = 0x10032, 0xFC, 10

def name(k):
    raw = b[ENT + k * ESZ:ENT + k * ESZ + 0xC8].split(b"\0")[0]
    return bytes(c ^ 0xAA for c in raw).decode("latin1")
def size_off(k):
    return struct.unpack_from("<II", b, ENT + k * ESZ + 0xC8)

K = [k for k in range(N) if "\\GENERAL_P.SLB" in name(k)][0]
sz, off = size_off(K)
t = b[DT + off:DT + off + sz].decode("latin1")
assert "Laser Convergence" not in t, "already patched"

def rep(old, new, count=1):
    global t
    assert t.count(old) == count, (old, t.count(old))
    t = t.replace(old, new)

def block(start):
    """Text of one OBJECT block (from its OBJECT line up to the next OBJECT/FCODE View)."""
    i = t.index("\t\tOBJECT %s\r\n" % start)
    j = t.index("\t\tOBJECT ", i + 10)
    return t[i:j]

# --- four new objects, cloned from the Crosshairs row (y 279 -> 309) ---------
rows = []
for nm, new in (("x5", "x8"), ("5", "8"), ("x5-x", "x8-x"), ("generalbox_5", "generalbox_8")):
    blk = block(nm)
    blk = blk.replace("\t\tOBJECT %s\r\n" % nm, "\t\tOBJECT %s\r\n" % new, 1)
    lines = blk.split("\r\n")
    f = lines[2].split()                    # x y w h
    assert f[1] == "279", (nm, lines[2])
    f[1] = "309"
    if nm == "5": f[2] = "180"              # wider label for the longer text
    if nm == "generalbox_5": f[2] = "210"   # clickable area covers it
    lines[2] = lines[2][:len(lines[2]) - len(lines[2].lstrip())] + " ".join(f)
    blk = "\r\n".join(lines)
    if nm == "5":
        blk = blk.replace("Enable Crosshairs", "Enable Laser Convergence")
    if nm == "generalbox_5":
        blk = blk.replace('flip_check_box("x5",IMMORTAL_CROSSHAIR);', "flip_convergence();")
    rows.append(blk)
anchor = "\t\tOBJECT x6-x\r\n"
rep(anchor, "".join(rows) + anchor)
rep("OBJLIST 63\r\n", "OBJLIST 67\r\n")

# --- script --------------------------------------------------------------
rep("long entering_passcode = FALSE;\r\n",
    "long entering_passcode = FALSE;\r\n"
    "long conv_setting = 1;  // Laser Convergence (GENERAL option 5, added by mod)\r\n")
rep("long NUM_NAV_BUTTONS = 20;", "long NUM_NAV_BUTTONS = 21;")
rep('      "generalbox_5"\r\n   };', '      "generalbox_5",\r\n      "generalbox_8"\r\n   };')
rep("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,0};",
    "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,0};")
rep("long nav_move_1[4] = {19,2,10,0};", "long nav_move_1[4] = {20,2,10,0};")
rep("long nav_move_2[4] = {19,3,15,1};", "long nav_move_2[4] = {20,3,15,1};")
rep("long nav_move_3[4] = {19,4,15,2};", "long nav_move_3[4] = {20,4,15,2};")
rep("long nav_move_9[4] = {8,14,4,19};", "long nav_move_9[4] = {8,14,4,20};")
rep("long nav_move_19[4] = {18,9,2,14};// crosshairs\r\n",
    "long nav_move_19[4] = {18,9,20,14};// crosshairs\r\n"
    "long nav_move_20[4] = {19,9,2,14};// laser convergence\r\n")
rep("nav_move_15,nav_move_16,nav_move_17,nav_move_18,nav_move_19\r\n",
    "nav_move_15,nav_move_16,nav_move_17,nav_move_18,nav_move_19,\r\n      nav_move_20\r\n")
rep('   set_check_box("x7", generalData[OVERLAYS_ENABLED]);\r\n   \r\n   display_passcodes(0);',
    '   set_check_box("x7", generalData[OVERLAYS_ENABLED]);\r\n'
    '   GetGameData(GENERAL,5,0,0,&conv_setting);\r\n'
    '   set_check_box("x8", conv_setting);\r\n   \r\n   display_passcodes(0);')
rep('      set_check_box("x7", generalData[OVERLAYS_ENABLED]);\r\n   }else',
    '      set_check_box("x7", generalData[OVERLAYS_ENABLED]);\r\n'
    '      set_check_box("x8", conv_setting);\r\n   }else')
rep("   GetGameData(GET_DEFAULT,GENERAL,PASSCODE,0,0x0);\r\n   displayData();",
    "   GetGameData(GET_DEFAULT,GENERAL,PASSCODE,0,0x0);\r\n"
    "   SetGameData(GENERAL,5,0,0,1);\r\n   displayData();")
rep("// Toggles the state of a check box.\r\n",
    "// Toggles Laser Convergence (stored straight away in GENERAL option 5).\r\n"
    "long flip_convergence()\r\n{\r\n"
    "   conv_setting = !conv_setting;\r\n"
    "   SetGameData(GENERAL,5,0,0,conv_setting);\r\n"
    '   set_check_box("x8",conv_setting);\r\n}\r\n\r\n'
    "// Toggles the state of a check box.\r\n")

new = t.encode("latin1")
delta = len(new) - sz

# --- repack -----------------------------------------------------------------
out = bytearray(b[:DT])
data = bytearray(b[DT:])
data[off:off + sz] = new
out += data
for k in range(N):
    s, o = size_off(k)
    if k == K:
        s = len(new)
    elif o > off:
        o += delta
    struct.pack_into("<II", out, ENT + k * ESZ + 0xC8, s, o)
struct.pack_into(">I", out, DT_TAG + 4, len(data))
struct.pack_into(">I", out, 4, len(out) - 8)
open(dst, "wb").write(out)
print("GENERAL_P.SLB %d -> %d bytes, bundle %d -> %d" % (sz, len(new), len(b), len(out)))
