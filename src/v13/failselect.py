# Game over (lives used up, or result code 3) -> back to MISSION SELECT instead of high scores + main menu.
# Outer loop 0x46CC75, game-over block 0x46D1A8:
#   0x46D1A8  mov byte [0x704961],0   (game no longer in progress)  -> call 0x43AE82 (reset lives) + 2 nops
#   0x46D1D1  mov byte [0x704962],1   (front end shows high scores) -> 0
# The end-of-mission screen (flow 4, mode 3) still plays; with 0x704961 kept at 1 the loop enters
# flow state 1 = mission select, exactly like a death with lives left.
import pex,struct,sys,hashlib
src,dst=sys.argv[1],sys.argv[2]
p=pex.PE(src); d=p.d
o=p.off(0x46D1A8); assert bytes(d[o:o+7])==bytes.fromhex('c6056149700000'),bytes(d[o:o+7]).hex()
d[o:o+7]=b'\xe8'+struct.pack('<i',0x43AE82-(0x46D1A8+5))+b'\x90\x90'
o=p.off(0x46D1D1); assert bytes(d[o:o+7])==bytes.fromhex('c6056249700001'),bytes(d[o:o+7]).hex()
d[o+6]=0
open(dst,'wb').write(d); print(hashlib.md5(d).hexdigest())
