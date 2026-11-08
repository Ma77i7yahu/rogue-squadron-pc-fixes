"""Rogue Squadron: hide the big (near) gunsight ring and make the crosshair orange.

Same change as Battle for Naboo's gunsight.py (same target.c HUD code):
  - gunsight draw 0x422Bxx..0x4234xx projects a near ring (ov_target, sprite +0x28 /
    +0x1A8 in the torpedo branch) and a far ring (sprite +0x58 / +0x1D8).  The big ring
    is hidden by skipping its draw-list insert; its maths still runs (the torpedo
    branch's small ring copies its alpha from the big ring, +0x1D7 -> +0x207).
  - colour fn 0x423A32 writes R,G,B = 00 FF 00 (green) in three paths -> COLOUR.

usage: python build_gunsight.py on|off [exe]
  on  : backs up to "Rogue Squadron.before-gunsight.EXE" (once) and patches
  off : restores the patched bytes from that backup
"""
import os, shutil, struct, sys

GAME = r"G:\Game Files\LucasArts\Star Wars Rogue Squadron\ROGUE"
COLOUR = (0xFF, 0x80, 0x00)          # same orange as the BfN crosshair

def sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 52)[0]
    out = []
    for i in range(n):
        o = pe + 24 + opt + i * 40
        vs, va, rs, ra = struct.unpack_from("<IIII", data, o + 8)
        out.append((va + base, max(vs, rs), ra))
    return out

def v2f(data, va):
    for sva, size, ra in sections(data):
        if sva <= va < sva + size:
            return va - sva + ra
    raise ValueError(hex(va))

def patches():
    r, g, b = COLOUR
    p = [
        # big ring, normal branch: skip insert 0x422F29..0x422F68 -> jmp 0x422F69
        (0x422F29, "8b4d0c8b118b45b0", "eb3e"),
        # big ring, torpedo branch: skip insert 0x4233A9..0x4233F7 -> jmp 0x4233F8
        (0x4233A9, "8b450c8b088b55b0", "eb4d"),
    ]
    # colour immediates (mov byte [reg+n], imm8): R, G, B in each of the 3 paths
    for ra, ga, ba in ((0x423A5A, 0x423A61, 0x423A68),
                       (0x423AA9, 0x423AB0, 0x423AB7),
                       (0x423AEA, 0x423AF1, 0x423AF8)):
        p += [(ra, "00", "%02x" % r), (ga, "ff", "%02x" % g), (ba, "00", "%02x" % b)]
    # opacity: RS tops out at 100/255, BfN at 200/255 -> match BfN.
    # 0x5BF898 = 100.0 (only used by the two fading paths of 0x423A32), path 3 imm 0x64
    p += [(0x5BF898, "0000c842", "00004843"),       # 100.0 -> 200.0
          (0x423AFF, "64", "c8")]
    return [(va, bytes.fromhex(old), bytes.fromhex(new)) for va, old, new in p]

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "on"
    exe = sys.argv[2] if len(sys.argv) > 2 else os.path.join(GAME, "Rogue Squadron.EXE")
    backup = os.path.join(os.path.dirname(exe), "Rogue Squadron.before-gunsight.EXE")
    data = bytearray(open(exe, "rb").read())
    if mode == "on":
        if not os.path.exists(backup):
            shutil.copy2(exe, backup)
        for va, old, new in patches():
            f = v2f(data, va)
            cur = bytes(data[f:f + len(new)])
            if cur == new:
                continue
            assert bytes(data[f:f + len(old)]).startswith(cur) and cur == old[:len(new)], \
                f"unexpected bytes at {va:#x}: {bytes(data[f:f+len(old)]).hex()}"
            data[f:f + len(new)] = new
    elif mode == "off":
        ref = open(backup, "rb").read()
        for va, old, new in patches():
            f = v2f(data, va)
            data[f:f + len(new)] = ref[f:f + len(new)]
    else:
        sys.exit(__doc__)
    open(exe, "wb").write(data)
    print(mode, "->", exe)

if __name__ == "__main__":
    main()
