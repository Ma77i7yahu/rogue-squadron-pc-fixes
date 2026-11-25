"""T-16 chase camera (mode 2 of its camera set 0x5F6550, entry 0x5F65C8, 0x3C bytes) = the X-wing's
mode 2 (0x5F6988) with its offsets x SCALE (the game's own T-16 side/rear views sit ~3x further out
than the X-wing's), and the T-16 aim-down correction (TANDOWN, .t16 data 0x80064C) set to 0, so its
shots fly along the nose line like every other craft.  usage: t16cam.py in out [scale 3] [tandown 0]"""
import pex, struct, sys
p = pex.PE(sys.argv[1]); out = sys.argv[2]
S = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
TD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
X, T = 0x5F6988, 0x5F65C8
assert p.rd(T, 0xc) == bytes.fromhex('0100030000000000') + struct.pack('<f', 4.5)
x = bytearray(p.rd(X, 0x3c))
v = list(struct.unpack_from('<12f', x, 0xc))
v[6:12] = [c * S for c in v[6:12]]            # camera position + look-at point
struct.pack_into('<12f', x, 0xc, *v)
o = p.off(T); p.d[o:o + 0x3c] = x
o = p.off(0x80064C)
assert abs(struct.unpack_from('<f', p.d, o)[0] - 0.13165) < 1e-3
struct.pack_into('<f', p.d, o, TD)
open(out, 'wb').write(p.d)
print('T-16 mode 2:', ' '.join('%.3g' % c for c in v), 'f8', struct.unpack_from('<f', x, 8)[0], 'tandown', TD)
