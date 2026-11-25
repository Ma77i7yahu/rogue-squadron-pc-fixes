# Rebuilds the untouched CD v1.2 exe from an installer-built exe by reverting PatchData runs.
import pd,hashlib,struct,sys
g,order,secs=pd.load()
src,dst,keys=sys.argv[1],sys.argv[2],sys.argv[3].split(',')
img=bytearray(open(src,'rb').read())
pe=struct.unpack_from('<I',img,0x3C)[0]; n=struct.unpack_from('<H',img,pe+6)[0]; tab=pe+24+struct.unpack_from('<H',img,pe+20)[0]
last=tab+(n-1)*40
if img[last:last+4]==b'.t16':
    img[last:last+40]=bytes(40); struct.pack_into('<H',img,pe+6,n-1)
BUILD=["deadzone","aimassist","linear","widescreen","ceiling","smallmoves","convergence","rlflight","lasers","mission7","repair","gunsight","hudnumbers","onelife"]
for k in ['t16x','t16']+BUILD[::-1]:
    if k in keys:
        for o,old,new in g[k][::-1]: img[o:o+len(old)]=old
img=img[:2492928]
m=hashlib.md5(img).hexdigest(); print(m, m=='2d5ee8852eb99f329318325c51742324')
open(dst,'wb').write(img)
