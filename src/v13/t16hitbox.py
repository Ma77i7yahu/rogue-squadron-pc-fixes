# T-16 hit box: replace the model's single collision box (whole bounding box of a Y-shaped craft)
# with a body box + 4 stepped fin boxes + 4 stepped boxes per wing, built from the t16 model's
# vertices (DATA.DAT, model units, y down). Hook in the T-16 create 0x41D161 (mov ecx,[ebp-8] /
# mov [ecx],eax) -> CAVE: same two instructions, then [[model]+0x58] = LIST.
# Collision entry (0x1C): u8 kind (0 = box in node space), u8 node, u16 0, min xyz, max xyz;
# a list ends with node byte 0xFF. Tested by 0x464AE4 (any box hit = hit).
import pex,struct,sys,hashlib
src,dst=sys.argv[1],sys.argv[2]; M=float(sys.argv[3]) if len(sys.argv)>3 else 1.5
CAVE,LIST,HOOK=0x800A00,0x800A40,0x41D161
boxes=[]
boxes.append(((-8.5,-12.5,-9.3-M),(8.5,12.5,24.9+M)))           # body
def fin_front(y): return 13.6+(-3.16-13.6)*(abs(y)-11.25)/32.63
for y0,y1 in ((-20,-12),(-28,-20),(-36,-28),(-44-M,-36)):        # fin, stepped taper
    boxes.append(((-0.4-M,y0,-9.3-M),(0.4+M,y1,fin_front(y1)+M)))
def wing_y(x): return 0.584*(x-6.3)
def wing_front(x): return 4.71+(-0.91-4.71)*(x-6.3)/30.3
for x0,x1 in ((8,16),(16,24),(24,32),(32,36.8+M)):                # wings, stepped diagonal
    xe=min(x1,36.8)
    for s in (1,-1):
        lo,hi=sorted((s*x0,s*x1))
        boxes.append(((lo,wing_y(x0)-M,-5.41-M),(hi,max(wing_y(xe),17.95)+M if x1>36 else wing_y(xe)+M,wing_front(x0)+M)))
lst=b''
for mn,mx in boxes: lst+=struct.pack('<BBH6f',0,0,0,*mn,*mx)
lst+=struct.pack('<BBH6f',0,0xFF,0,*([0.0]*6))
code=bytes.fromhex('8b4df8'+'8901'+'85c0'+'740d'+'8b10'+'85d2'+'7407'+'c74258')+struct.pack('<I',LIST)+bytes.fromhex('c3')
p=pex.PE(src); d=p.d
o=p.off(HOOK); assert bytes(d[o:o+5])==bytes.fromhex('8b4df88901'),bytes(d[o:o+5]).hex()
rel=CAVE-(HOOK+5); d[o:o+5]=b'\xe8'+struct.pack('<i',rel)
oc=p.off(CAVE); assert not any(d[oc:oc+0x40+len(lst)])
d[oc:oc+len(code)]=code; ol=p.off(LIST); d[ol:ol+len(lst)]=lst
open(dst,'wb').write(d); print(len(boxes),'boxes', hashlib.md5(d).hexdigest())
for b in boxes: print(' min (%6.2f %6.2f %6.2f) max (%6.2f %6.2f %6.2f)'%(*b[0],*b[1]))
