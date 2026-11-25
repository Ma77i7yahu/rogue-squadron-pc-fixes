"""Kasan Moor biography always available: bio page count fn 0x43D2E0(progress) returns 5 always."""
import pex, sys
p = pex.PE(sys.argv[1]); o = p.off(0x43D2EE)
assert bytes(p.d[o:o+2]) == bytes.fromhex('7c04')
p.d[o:o+2] = b'\x90\x90'
open(sys.argv[2], 'wb').write(p.d)
