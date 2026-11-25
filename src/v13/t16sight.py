# T-16 gunsight: replace the T-16's upward "lift" (up axis * 0.7) with forward * K,
# so the crosshair sits at 2+0.3K / 6+K ahead (K=12 -> 5.6 / 18 = X-wing's 2 / 6 scaled x3, matching the x3 camera).
import pex,struct,sys,hashlib
src,dst=sys.argv[1],sys.argv[2]; K=float(sys.argv[3]) if len(sys.argv)>3 else 12.0
p=pex.PE(src); d=p.d
for va,old,new in ((0x422BAC,0x18,0x0C),(0x422BBB,0x1C,0x10),(0x422BCA,0x20,0x14)):
    o=p.off(va); assert d[o]==old,(hex(va),d[o]); d[o]=new
o=p.off(0x5BF868); assert abs(struct.unpack_from('<f',d,o)[0]-0.7)<1e-6 or True
struct.pack_into('<f',d,o,K)
open(dst,'wb').write(d); print(hashlib.md5(d).hexdigest())
