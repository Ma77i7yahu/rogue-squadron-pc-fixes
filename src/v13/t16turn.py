# T-16 turn handling = X-wing's: init 0x41C780 immediates F8 (+0xF8) 1.8->1.6, FC (+0xFC) 2->1.75,
# P114 (+0x114) -35->-30, P118 (+0x118) 40 (was 30). Speed/accel (+0xF0/+0xF4/+0x104/+0x108) untouched.
import pex,struct,sys,hashlib
src,dst=sys.argv[1],sys.argv[2]
p=pex.PE(src); d=p.d
want={0xF8:1.6,0xFC:1.75,0x114:-30.0,0x118:40.0}
for i in p.md.disasm(p.rd(0x41C780,0x200),0x41C780):
    if i.mnemonic=='mov' and '+ 0x' in i.op_str and i.op_str.startswith('dword ptr ['):
        off=int(i.op_str.split('+ ')[1].split(']')[0],16)
        if off in want:
            o=p.off(i.address)+i.size-4
            print(hex(i.address),hex(off),struct.unpack_from('<f',d,o)[0],'->',want[off])
            struct.pack_into('<f',d,o,want.pop(off))
assert not want,want
open(dst,'wb').write(d); print(hashlib.md5(d).hexdigest())
