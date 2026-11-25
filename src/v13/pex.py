import struct, sys, capstone
class PE:
    def __init__(s, path):
        s.d = bytearray(open(path,'rb').read()); d=s.d
        pe=struct.unpack_from('<I',d,0x3C)[0]; n=struct.unpack_from('<H',d,pe+6)[0]; opt=struct.unpack_from('<H',d,pe+20)[0]
        s.base=struct.unpack_from('<I',d,pe+52)[0]; s.secs=[]
        for k in range(n):
            o=pe+24+opt+k*40; nm=d[o:o+8].rstrip(b'\0').decode(errors='replace')
            vs,va,rs,ro=struct.unpack_from('<IIII',d,o+8); s.secs.append((nm,va,vs,rs,ro))
        s.md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    def off(s,va):
        for nm,v,vs,rs,ro in s.secs:
            if s.base+v<=va<s.base+v+max(vs,rs): return ro+va-s.base-v
    def va(s,off):
        for nm,v,vs,rs,ro in s.secs:
            if ro<=off<ro+rs: return s.base+v+off-ro
    def rd(s,va,n): o=s.off(va); return bytes(s.d[o:o+n])
    def u32(s,va): return struct.unpack('<I',s.rd(va,4))[0]
    def dis(s,va,n=40,stop_ret=False):
        out=[]
        for i in s.md.disasm(s.rd(va,n*8),va):
            out.append('%08X  %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
            n-=1
            if n<=0 or (stop_ret and i.mnemonic=='ret'): break
        return '\n'.join(out)
if __name__=='__main__':
    p=PE(sys.argv[1]); print(p.dis(int(sys.argv[2],16),int(sys.argv[3]) if len(sys.argv)>3 else 60))
