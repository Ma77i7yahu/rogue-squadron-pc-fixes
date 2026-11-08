"""Builds the patch tables for the Rogue Squadron mod installer.

Every patch is taken from the hand-patched exe variants in the game folder
(diffed against the untouched v1.2 exe), so the installer reproduces exactly
the bytes that were tested in game.  Outputs:
  PatchData.cs   - embedded tables for Installer.cs
  ../dist/PATCHES.txt - full byte listing + disassembly of every change
"""
import hashlib, os, struct, sys

GAME = sys.argv[1] if len(sys.argv) > 1 else r"G:\Game Files\LucasArts\Star Wars Rogue Squadron"
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG_MD5 = "2d5ee8852eb99f329318325c51742324"

def rd(n): return open(os.path.join(GAME, "Rogue Squadron.%s.EXE" % n), "rb").read()

orig = rd("original")
assert hashlib.md5(orig).hexdigest() == ORIG_MD5
v4x3, vws, vsm = rd("4x3"), rd("before-convergence"), rd("smallmoves")
# convergence v5 (build_conv.py), Rogue Leader flight on it (build_rlflight.py, default args),
# faster lasers on that (build_lasers.py, default args). convergence-v3 is only kept because
# the T-16's 0x800000 build (t16-on-conv3) was made on it.
vconv, vrl, vlas = rd("convergence"), rd("rlflight"), rd("rllasers")
vconv3 = rd("convergence-v3")

def runs(a, b, gap=8):
    spans, i, n = [], 0, max(len(a), len(b))
    while i < n:
        if i >= len(a) or i >= len(b) or a[i] != b[i]:
            j = i
            while j < n and (j >= len(a) or j >= len(b) or a[j] != b[j]): j += 1
            if spans and i - spans[-1][1] <= gap and (i < len(a)) == (spans[-1][0] < len(a)):
                spans[-1][1] = j
            else:
                spans.append([i, j])
            i = j
        else: i += 1
    return [(s, b[s:e], a[s:e]) for s, e in spans]  # (offset, new, old)

# --- PE section map for offset -> VA --------------------------------------
pe = struct.unpack_from("<I", vconv, 0x3C)[0]
nsec = struct.unpack_from("<H", vconv, pe + 6)[0]
opt = struct.unpack_from("<H", vconv, pe + 20)[0]
base = struct.unpack_from("<I", vconv, pe + 52)[0]
secs = []
for k in range(nsec):
    o = pe + 24 + opt + k * 40
    name = vconv[o:o + 8].rstrip(b"\0").decode()
    vs, va, rs, ro = struct.unpack_from("<IIII", vconv, o + 8)
    secs.append((name, va, rs, ro))
def va_of(off):
    for name, va, rs, ro in secs:
        if ro <= off < ro + rs: return base + va + off - ro, name
    return None, "header"

# --- groups ---------------------------------------------------------------
AIM = {0x00C19A: "A-wing", 0x025535: "Y-wing ion turret", 0x024964: "X-wing",
       0x017BEB: "TIE Interceptor", 0x018DE3: "Naboo starfighter",
       0x01B448: "Snowspeeder", 0x0200D5: "V-wing"}
LINEAR = {0x00E351}
RES = 0x201D80

flight = runs(orig, v4x3)
deadzone = [r for r in flight if r[0] not in AIM and r[0] not in LINEAR]
aim = [r for r in flight if r[0] in AIM]
linear = [r for r in flight if r[0] in LINEAR]
assert len(deadzone) == 20 and len(aim) == 7 and len(linear) == 1
ws_all = runs(v4x3, vws)
widescreen = [r for r in ws_all if r[0] != RES]
assert len(widescreen) == len(ws_all) - 1 and orig[RES:RES + 8] == bytes.fromhex("0005000000040000")
small = runs(vws, vsm)
# snowspeeder init 41A617: mov [rec+0x108], 10.0 = its ceiling above the terrain (V-wing 20.0);
# flight input fn 4113B5 caps types 3/4 at ground + [rec+0x108], never above the mission ceiling
SPEEDER_CEIL = 0x019A1D
ceiling = [(SPEEDER_CEIL, struct.pack("<f", 20.0), struct.pack("<f", 10.0))]
# convergence v5 was built on the smallmoves exe with the aim-assist cones put back (it drives
# the game's own target finder), so diff against that; the installer never combines it with
# the aim-assist group. Its in-game toggle (Bundle.002 menu) is done by the installer itself.
vsm_cones = bytearray(vsm)
for o in AIM: vsm_cones[o:o + 4] = orig[o:o + 4]
# The .conv section is diffed against zeros (not as one block) so convergence and RL flight each
# own only their own bytes in it; a final 4-byte zero run makes the image reach the section end.
def runs_pad(a, b): return runs(a + bytes(len(b) - len(a)), b)
SEC_CONV, SEC_CONV_END = 0x260A00, 0x261A00
assert len(vconv) == len(vrl) == len(vlas) == SEC_CONV_END and vconv[0x298:0x29D] == b".conv"
conv = runs_pad(bytes(vsm_cones), vconv)
assert not any(o in AIM for o, _, _ in conv) and not any(vconv[SEC_CONV_END - 4:])
conv.append((SEC_CONV_END - 4, bytes(4), bytes(4)))
rlflight = runs(vconv, vrl)
# tight-turn joystick button mask (1 << (button - 1)), .conv data +0x68; the installer writes it
RL_BUTTON = SEC_CONV + 0xF00 + 0x68
assert struct.unpack_from("<I", vrl, RL_BUTTON)[0] == 1 << 8
assert any(o <= RL_BUTTON + 1 < o + len(n) for o, n, _ in rlflight)   # only byte +1 is non-zero
lasers = runs(vrl, vlas)

# --- any craft on Imperial Construction Yards (level 6) ---------------------------------------
# Allowed-craft mask fn 43CEC8 (hangar) and full-unlock mask fn 43D04A (menus) both start with
# 1 << default craft [5F8498 + level*4] and cut levels 3/6/0xB/0x12 to the snowspeeder only.
# The prologue is rewritten to also set the X-wing bit for level 6 (so the progress unlocks
# for X/A/V apply), and level 6 is dropped from the speeder-only list (cmp 6 -> cmp -1).
def off_of(va):
    for name, sva, rs, ro in secs:
        if base + sva <= va < base + sva + rs: return va - base - sva + ro
M7_OLD = bytes.fromhex("51 8B4508 BA01000000 8B0C8598845F00 D3E2 8955FC")
M7_NEW = bytes.fromhex("8B4508 8B0C8598845F00 31D2 3C06 0F94C2 0FABCA 52")
mission7 = [(off_of(0x43CECB), M7_NEW, M7_OLD), (off_of(0x43D01A), b"\xFF", b"\x06"),
            (off_of(0x43D04D), M7_NEW, M7_OLD), (off_of(0x43D12B), b"\xFF", b"\x06")]
M7_CODE = {off_of(0x43CECB), off_of(0x43D04D)}

# --- every craft repairs itself ---------------------------------------------------------------
# Repair fn 40EBE8(rec, dt) (called by the shared craft update 40ECCE, so every craft) adds
# max health/180 per second ([rec+0xC0] up to [rec+0xC4]), only for X, Y, Falcon and Naboo.
# The whole fn (and its tables, up to 40ECCE) is replaced by caves/repair_all.s: every craft
# repairs, and the craft without droid or crew lose it below 25% health like a lost R2.
sys.path.insert(0, HERE)  # build.cmd runs python -I
import build_repair
REPAIR_OFF, REPAIR_END = off_of(build_repair.VA), off_of(build_repair.END)
repair_code = build_repair.assemble()
repair_code += b"\xCC" * (REPAIR_END - REPAIR_OFF - len(repair_code))
repair = [(REPAIR_OFF, repair_code, orig[REPAIR_OFF:REPAIR_END])]

# --- T-16 Skyhopper (build_t16.py) ------------------------------------------------------------
# Its own section ".t16" goes after the exe's last section, so the cave is built for two VAs:
# 0x7FF000 (no other new section) and 0x800000 (after .conv). The installer appends the
# section header + data itself (T16Section below) and applies the matching .text/.data runs.
T16_SIZE = 0x1000
vt_plain, vt_conv = rd("t16-plain"), rd("t16-on-conv3")
def body_runs(a, b):
    """runs inside the original image, excluding the PE header (written by the installer)"""
    return [r for r in runs(a[:len(orig)], b[:len(orig)]) if r[0] >= 0x400]
t16lo = body_runs(orig, vt_plain)
t16hi = body_runs(vconv3, vt_conv)
t16lo_sec, t16hi_sec = vt_plain[len(orig):], vt_conv[len(vconv3):]
# the T-16 in the tester's exe was built on rllasers (convergence v5 + RL flight + lasers): same runs and data
vt_las = rd("t16")
assert body_runs(vlas, vt_las) == t16hi and vt_las[len(vlas):] == t16hi_sec
assert len(t16lo_sec) == len(t16hi_sec) == T16_SIZE

# mask_end (section +0) skipped levels whose default craft is the snowspeeder. Those are exactly
# the speeder-only levels, which never have the X-wing bit, except Imperial Construction Yards
# with the mission 7 option. NOP the "je" (+0x17) so the T-16 is offered wherever the X-wing is.
T16_SPEEDER_JE = 0x17
def t16_on_m7(sec):
    assert sec[T16_SPEEDER_JE - 8:T16_SPEEDER_JE + 2] == bytes.fromhex("833C8D98845F0004 7402")
    return sec[:T16_SPEEDER_JE] + b"\x90\x90" + sec[T16_SPEEDER_JE + 2:]
vt_plain = vt_plain[:len(orig)] + t16_on_m7(t16lo_sec)
vt_conv = vt_conv[:len(vconv3)] + t16_on_m7(t16hi_sec)
vt_las = vt_las[:len(vlas)] + t16_on_m7(t16hi_sec)
t16lo_sec, t16hi_sec = vt_plain[len(orig):], vt_conv[len(vconv3):]

def add_t16(img, variants):
    """Same steps as Installer.cs AddT16: new section header, then the runs + section data."""
    img = bytearray(img)
    pe = struct.unpack_from("<I", img, 0x3C)[0]
    n = struct.unpack_from("<H", img, pe + 6)[0]
    tab = pe + 24 + struct.unpack_from("<H", img, pe + 20)[0]
    vs, va, rs, ro = struct.unpack_from("<IIII", img, tab + (n - 1) * 40 + 8)
    nva = (va + max(vs, rs) + 0xFFF) & ~0xFFF
    struct.pack_into("<8sIIIIIIHHI", img, tab + n * 40, b".t16", T16_SIZE, nva, T16_SIZE, len(img), 0, 0, 0, 0, 0xE0000020)
    struct.pack_into("<H", img, pe + 6, n + 1)
    struct.pack_into("<I", img, pe + 0x50, nva + T16_SIZE)
    rr, sec = variants[nva]
    for off, new, old in rr:
        assert img[off:off + len(old)] == old
        img[off:off + len(new)] = new
    return bytes(img + sec)
VARIANTS = {0x3FF000: (t16lo, t16lo_sec), 0x400000: (t16hi, t16hi_sec)}
for base_img, built in ((orig, vt_plain), (vconv3, vt_conv), (vlas, vt_las)):
    assert add_t16(base_img, VARIANTS) == built, "installer simulation differs from build_t16.py"

GROUPS = [
    ("deadzone", "Remove per-craft stick deadzones", deadzone),
    ("aimassist", "Remove aim assist (all craft except the Falcon)", aim),
    ("linear", "Linear stick response (no squaring)", linear),
    ("widescreen", "16:9 widescreen (Hor+) with terrain, radar and draw-distance fixes", widescreen),
    ("smallmoves", "Small stick movement fix", small),
    ("ceiling", "Airspeeder ceiling 10 -> 20 above the ground", ceiling),
    ("mission7", "Any craft on Imperial Construction Yards (mission 7)", mission7),
    ("repair", "Every craft repairs itself like the X-wing", repair),
    ("convergence", "Laser auto-convergence (in-game toggle; replaces aim assist)", conv),
    ("rlflight", "Rogue Leader style flight + tight-turn button (code in .conv)", rlflight),
    ("lasers", "Faster lasers (player bolt speed x2)", lasers),
    ("t16", "T-16 Skyhopper as a selectable craft (.t16 section at VA 007FF000)", t16lo),
    ("t16x", "T-16 Skyhopper as a selectable craft (.t16 section at VA 00800000, after .conv)", t16hi),
]

# sanity: every group's old bytes match the original exe, and the four
# base groups never overlap each other
def span(g): return set(i for off, new, old in g for i in range(off, off + len(new)))
orig_pad = orig + bytes(SEC_CONV_END - len(orig))   # new-section bytes start out as zeros
for key, _, g in GROUPS:
    for off, new, old in g:
        assert orig_pad[off:off + len(old)] == old, (key, hex(off))
basekeys = ["deadzone", "aimassist", "linear", "widescreen", "smallmoves"]
for i, a in enumerate(GROUPS):
    for b in GROUPS[i + 1:]:
        ov = span(a[2]) & span(b[2])
        if ov and {a[0], b[0]} != {"t16", "t16x"}:
            raise SystemExit("unexpected overlap %s/%s" % (a[0], b[0]))

# --- C# -------------------------------------------------------------------
def cs_bytes(b): return "new byte[]{" + ",".join("0x%02X" % x for x in b) + "}"
lines = ["// Generated by gen.py - do not edit.", "static class PatchData {",
         '    public const string OriginalMd5 = "%s";' % ORIG_MD5,
         "    public const int OriginalLength = %d;" % len(orig),
         "    public const int ResolutionOffset = 0x%X;" % RES,
         "    public const int RlButtonOffset = 0x%X;   // u32 joystick button mask, 1 << (button - 1)" % RL_BUTTON,
         "    public static readonly Patch[] Groups = {"]
for key, title, g in GROUPS:
    lines.append('        new Patch("%s", new Run[]{' % key)
    for off, new, old in g:
        lines.append("            new Run(0x%06X, %s, %s)," % (off, cs_bytes(old), cs_bytes(new)))
    lines.append("        }),")
lines.append("    };")
lines.append("    // T-16 section data, keyed by the section's RVA (0x3FF000 = VA 007FF000, 0x400000 = VA 00800000)")
lines.append("    public const int T16SectionSize = 0x%X;" % T16_SIZE)
for rva, (_, sec) in sorted(VARIANTS.items()):
    lines.append("    public static readonly byte[] T16Section_%X = %s;" % (rva, cs_bytes(sec)))
lines.append("}")
open(os.path.join(HERE, "PatchData.cs"), "w").write("\n".join(lines) + "\n")

# --- PATCHES.txt ----------------------------------------------------------
import capstone
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(code, va):
    res = []
    for i in cs.disasm(code, va):
        if i.mnemonic == "nop" and res and res[-1].endswith("nop"):
            res[-1] = res[-1][:-3] + "nop (x2)" if not res[-1].endswith(")") else res[-1]
            continue
        if i.mnemonic == "nop" and res and "nop (x" in res[-1]:
            n = int(res[-1].rsplit("x", 1)[1][:-1]); res[-1] = res[-1].rsplit("(x", 1)[0] + "(x%d)" % (n + 1); continue
        res.append(("        %08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)).rstrip())
    return res
def floats(b):
    return " ".join("%g" % struct.unpack_from("<f", b, k)[0] for k in range(0, len(b) - 3, 4))

import math
def f32(b, o=0): return struct.unpack_from("<f", b, o)[0]

# instruction starts for runs that begin mid-instruction
INSN_START = {0xF947: 0xF945, 0xF948: 0xF945, 0xF978: 0xF976, 0xF979: 0xF976, 0xF9A9: 0xF9A7, 0xF9AA: 0xF9A7}
CODE = {0x00E351, 0x0D4A62, 0x0D4B23, 0x00BD1F, 0x0DC299, 0x0DC3EE, 0x00E930, 0x00EF7D, 0x00F92E} | set(INSN_START) | M7_CODE | {REPAIR_OFF}
FLOAT_NOTES = {0x079D44: "radar map sideways scale", 0x079D5B: "radar map sideways position",
               0x16E042: "renderer aspect ratio (4/3 -> 16/9, Hor+)",
               0x1C0944: "terrain view-pyramid corner x (-4 -> -16/3)"}
NOTES = {
    0x0001D8: ".text VirtualSize 0x1BDF99 -> 0x1BE000 so the code caves at 5BEFA0.. are mapped",
    0x0D4A62: "terrain distance: call cave that multiplies it by 1.16",
    0x0D4B23: "terrain grid: call cave that clamps the 4 frustum corners to camera +-30.5 cells (stops the 64x64 grid overflowing, e.g. Moff Seerden's shuttle scene)",
    0x1BE3A0: "code caves in .text padding (+ constants at 5BEFF0: 30.5, 1e30, 30.5, 1e30)",
    0x00E351: "skip the X*|X| stick squaring (jmp over it)",
    0x0000DE: "NumberOfSections 5 -> 6", 0x000129: "SizeOfImage", 0x000298: "new section header",
    0x0002BC: "section characteristics RWX code",
    0x00BD1F: "target finder wrapper 40C8FC end: jmp to convergence cave (moves the aim point onto the nose line)",
    0x0DC299: "settings store Get: GENERAL option 5 (Laser Convergence) -> cave",
    0x0DC3EE: "settings store Set: GENERAL option 5 (Laser Convergence) -> cave",
    0x00E930: "flight fn 40F530: jmp to Rogue Leader turn cave (yaw)",
    0x00EF7D: "flight fn 40FB7D: jmp to Rogue Leader cave (auto tight-turn pull)",
    0x00F92E: "flight fn 41052E: jmp to Rogue Leader cave (final roll rate)",
}
for va in (0x4DD14B, 0x4DD15F, 0x4DD179, 0x4DD1A5):
    NOTES[off_of(va)] = "settings help-text table 6056E8 -> copy in .conv with the convergence line"
for va in (0x5BF674, 0x5BF6AC, 0x5BF6B0, 0x5BF72C, 0x5BF800, 0x5BF804, 0x5BF808, 0x5BF8E0, 0x5BF8E4):
    FLOAT_NOTES[off_of(va)] = "fraction of the turn toward the aim point a bolt makes"
NOTES[off_of(0x43CECB)] = "hangar craft mask fn 43CEC8: mask = 1 << default craft, plus the X-wing bit when level == 6"
NOTES[off_of(0x43D04D)] = "full-unlock mask fn 43D04A (menus): same prologue change"
NOTES[off_of(0x43D01A)] = NOTES[off_of(0x43D12B)] = "speeder-only level list: cmp [ebp+8], 6 -> -1 (Imperial Construction Yards no longer listed)"
INSN_START[off_of(0x43D01A)], INSN_START[off_of(0x43D12B)] = off_of(0x43D017), off_of(0x43D128)
CODE |= {off_of(0x43D01A), off_of(0x43D12B)}
for o in (0xF948, 0xF979, 0xF9AA):
    NOTES[o] = "rate cut-off fcomp: 0.1 deg/frame -> existing 0.001 constant at 5C04C8"
SECNAME = {"convergence": ".conv", "rlflight": ".conv"}
CAVESRC = {"convergence": "laser_convergence.s (+ build_conv.py)", "rlflight": "rl_flight.s (+ build_rlflight.py)"}

out = ["Star Wars: Rogue Squadron 3D (PC v1.2) - complete patch listing",
       "Base exe: Rogue Squadron.EXE, %d bytes, MD5 %s" % (len(orig), ORIG_MD5.upper()),
       "off = file offset; VA = virtual address in the loaded exe (image base 0x400000).",
       "Every 'old' value below has been checked against the original exe.", ""]
for key, title, g in GROUPS:
    img = bytearray(orig) + bytearray(max(0, max(o + len(n) for o, n, _ in g) - len(orig)))
    for off, new, old in g: img[off:off + len(new)] = new
    out.append("=" * 78)
    out.append("[%s] %s  (%d changes)" % (key, title, len(g)))
    out.append("=" * 78)
    for off, new, old in g:
        va, sec = va_of(off)
        if off >= len(orig):
            out.append("  off %06X  (VA %08X %s)  NEW SECTION data, %d bytes." % (off, 0x7FF000 + off - SEC_CONV, SECNAME[key], len(new)))
            out.append("        Assembly source: src/caves/%s" % CAVESRC[key])
            hx = new.rstrip(b"\0").hex()
            out += ["        " + hx[k:k + 64] for k in range(0, len(hx), 64)]
            continue
        where = ("VA %08X %s" % (va, sec)) if va else "PE header"
        note = NOTES.get(off, "")
        if key == "aimassist":
            c = f32(old); note = "%s: target cone cos %.4f (%.1f deg) -> 2.0 (never matches)" % (AIM[off], c, math.degrees(math.acos(c)))
        elif key == "deadzone":
            note = "float %.2f -> 0" % (f32(old) if len(old) == 4 else 0.25)
        elif key == "ceiling":
            note = "airspeeder init (mov [rec+0x108], imm): ceiling above the terrain %g -> %g" % (f32(old), f32(new))
        elif key == "repair":
            note = ("repair fn 40EBE8 rewritten in place (src/caves/repair_all.s): every craft repairs; A, V, speeder, "
                    "TIE and T-16 clear the R2 flag 5E9384 (= stop repairing) below 25% health")
        elif off in FLOAT_NOTES:
            note = "%s: %.4f -> %.4f" % (FLOAT_NOTES[off], f32(orig, off), f32(img, off))
        sh = lambda b: b.hex() if len(b) <= 24 else b[:24].hex() + "...(%d bytes)" % len(b)
        out.append("  off %06X  (%s)  %s -> %s" % (off, where, sh(old), sh(new)))
        if note: out.append("        ; " + note)
        if va and off == 0x1BE3A0:
            out += dis(bytes(img[0x1BE3A0:0x1BE3AD]), 0x5BEFA0)
            out.append("        005BEFB0  %-20s dd %g" % (img[0x1BE3B0:0x1BE3B4].hex(), f32(img, 0x1BE3B0)))
            out += dis(bytes(img[0x1BE3B4:0x1BE3ED]), 0x5BEFB4)
            out.append("        005BEFF0  %-20s dd %s" % (img[0x1BE3F0:0x1BE400].hex(), ", ".join("%g" % f32(img, 0x1BE3F0 + 4 * k) for k in range(4))))
        elif va and off in CODE:
            s = INSN_START.get(off, off)
            out += dis(bytes(img[s:max(off + len(new), s + 6)]), va - (off - s))
    out.append("")
out += ["=" * 78, "[t16 / t16x] new section",
        "  The installer adds a section header \".t16\" (VirtualSize/SizeOfRawData 0x1000, RWX 0xE0000020)",
        "  after the exe's last section, appends 0x1000 bytes of data at the end of the file, raises",
        "  NumberOfSections by 1 and SizeOfImage by 0x1000. Its VA is 007FF000 on its own and 00800000",
        "  when the laser convergence option (which adds a section) is also installed;",
        "  the [t16] or [t16x] runs above match that VA. Source: src/caves/t16_craft.s + src/build_t16.py.",
        "  On top of the build_t16.py output, the \"je\" at section +0x17 (skip levels whose default craft is",
        "  the snowspeeder) is NOPed, so the T-16 is also offered on mission 7 with that option.", ""]
for rva, (_, sec) in sorted(VARIANTS.items()):
    hx = sec.rstrip(b"\0").hex()
    out.append("  .t16 data for VA %08X (%d bytes, trailing zeros omitted):" % (0x400000 + rva, T16_SIZE))
    out += ["        " + hx[k:k + 64] for k in range(0, len(hx), 64)]
    out.append("")
out += ["=" * 78, "[resolution] menu entry 1280x1024 (table at VA 603520, entry 8) replaced",
        "  off 201D80  (VA 00603580 .data)  width dword 0x500, off 201D84 height dword 0x400",
        "  The installer writes the chosen 16:9 size here (default 1920x1080 = 80 07 00 00 / 38 04 00 00).", ""]
open(os.path.join(HERE, "..", "dist", "PATCHES.txt"), "w", newline="\r\n").write("\n".join(out) + "\n")
print("ok", [(k, len(g)) for k, _, g in GROUPS])
