"""Nonah heavy lifters killable + any craft on every airspeeder-only mission."""
import pex, sys
src, dst = sys.argv[1], sys.argv[2]
p = pex.PE(src)
def patch(va, old, new):
    old, new = bytes.fromhex(old), bytes.fromhex(new)
    assert len(old) == len(new), hex(va)
    o = p.off(va); cur = bytes(p.d[o:o+len(old)])
    assert cur == old, (hex(va), cur.hex())
    p.d[o:o+len(new)] = new
# --- Search for the Nonah: Shuttle.c HP callback 0x4A9295 passes rec+0x6C (HP) to 0x401000.
# The three Spline_HeavyLifter landing craft (kind 0x2C) have 1,000,000 HP; every other
# shuttle-type object has < 65536. If HP >= 65536 -> 2000 (as the Rebel shuttles there).
patch(0x4A92BF,
      '8b45f8' '8b4834' '894dfc' '8b55fc' '52' '8b45fc' '83c06c' '50' '8b4df8' '8b5138' '52',
      '8b45fc' '80786e00' '7407' 'c7406cd0070000' '50' '83c06c' '50' '8b4df8' 'ff7138')
# --- Airspeeder-only missions (levels 3, 6, 0xB, 0x12): mask prologue adds the X-wing bit when
# the level's default craft is the speeder (generalises the mission 7 patch: was "level == 6"),
# so X/A/V progress unlocks and the T-16 apply; the speeder-only list is emptied.
M7  = '8b4508' '8b0c8598845f00' '31d2' '3c06' '0f94c2' '0fabca' '52'
ANY = '8b4508' '8b048598845f00' '31d2' '3c04' '0f94c2' '0fabc2' '52'
for pro, lst in ((0x43CECB, 0x43D011), (0x43D04D, 0x43D122)):
    patch(pro, M7, ANY)
    patch(lst + 3, '03', 'ff')      # cmp [ebp+8],3
    patch(lst + 0xF, '0b', 'ff')    # cmp [ebp+8],0xb
    patch(lst + 0x15, '12', 'ff')   # cmp [ebp+8],0x12
open(dst, 'wb').write(p.d)
