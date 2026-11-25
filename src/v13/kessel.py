"""Rescue on Kessel (level 8): more craft + ion cannon for all of them."""
import pex, sys
src, dst = sys.argv[1], sys.argv[2]
p = pex.PE(src)
def patch(va, old, new):
    old, new = bytes.fromhex(old), bytes.fromhex(new)
    assert len(old) == len(new), hex(va)
    o = p.off(va); cur = bytes(p.d[o:o+len(old)])
    assert cur == old, (hex(va), cur.hex())
    p.d[o:o+len(new)] = new
# 1) craft masks (hangar fn 0x43CEC8, menu fn 0x43D04A): level 8 "mask &= 3" ->
#    "mask |= 2 (Y-wing); mask &= ~0x10 (no speeder)"
patch(0x43D008, '8b4dfc83e103894dfc', '834dfc028365fcef90')
patch(0x43D119, '8b45fc83e0038945fc', '834dfc028365fcef90')
# 2) secondary weapon fn 0x43D1BD: level 8 -> weapon 1 (ion cannon) for every craft
patch(0x43D22E, '7504', '9090')
# 3) ammo fn 0x43BE72(craft, weapon): weapon 1 -> 0xFF (unlimited) for every craft
patch(0x43BE78, 'c645fc008b450825ff0000008945f8',
                '0fb64508807d0c0174278945f89090')   # movzx eax,[ebp+8]; cmp byte[ebp+c],1; je 43BEA9; mov [ebp-8],eax
patch(0x43BE8B, '7750', '7746')                     # out-of-range craft -> case that sets 6 (was: uninitialised)
open(dst, 'wb').write(p.d)
