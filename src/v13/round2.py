"""2026-11-23 round 2: Nonah lifters 20000 HP, ion cannon ammo number hidden for every craft,
T-16 ion cannon aimed by the T-16 aim correction (same cave as its torpedoes)."""
import pex, sys
p = pex.PE(sys.argv[1])
def patch(va, old, new):
    old, new = bytes.fromhex(old), bytes.fromhex(new)
    o = p.off(va); cur = bytes(p.d[o:o+len(old)])
    assert len(old) == len(new) and cur == old, (hex(va), cur.hex())
    p.d[o:o+len(new)] = new
# Nonah heavy lifters: HP >= 65536 -> 20000 (was 2000)
patch(0x4A92C8, 'c7406cd0070000', 'c7406c10270000')   # 10000 (user 2026-11-24; was 20000)
# HUD 0x47B4EE: number hidden when "craft == X-wing && weapon == 1" -> "weapon == 1"
patch(0x47B4F8, '750d', '9090')
# ion cannon fire 0x4241BF: after the "scnd" matrix call, run t16_torp (0x8008EA, .t16 at 0x800000)
# like the torpedo case does at 0x423F24; it replays add esp,0x18 + mov edx,[0x704DFC]
assert p.rd(0x423F24, 5) == bytes.fromhex('e8c1c93d00')
rel = (0x8008EA - (0x4241DB + 5)) & 0xffffffff
patch(0x4241DB, '83c418' '8b15fc4d7000', 'e8' + rel.to_bytes(4, 'little').hex() + '90' * 4)
open(sys.argv[2], 'wb').write(p.d)
