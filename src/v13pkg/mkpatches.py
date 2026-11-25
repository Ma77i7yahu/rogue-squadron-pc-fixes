# Appends the 2026-11-25 groups to dist\PATCHES.txt (gen.py doesn't know them).
import sys; sys.path.insert(0,r'G:/Dev/RogueSquadronMods/src/v13')
import pd,pex,struct
g,order,secs=pd.load()
live=pex.PE(r'G:/Game Files/LucasArts/Star Wars Rogue Squadron/Rogue Squadron.EXE')
orig=pex.PE(r'orig.exe')
def secname(va):
    for nm,v,vs,rs,ro in live.secs:
        if live.base+v<=va<live.base+v+max(vs,rs): return nm
CODE={0x3B278:5,0x3C408:2,0x3C519:2,0x3C62E:1,0x7A8F8:1,0x3C2CB:7,0x3C44D:7,0xA86C1:(0x4A92BF,4),0x3C6EE:1,0x6C5A8:2,0x1C561:1,0x235DB:2}
NOTE={'t16b':'.t16 at VA 007FF000 (T-16 without laser convergence)','t16xb':'.t16 at VA 00800000 (after .conv)',
      't16ion':'.t16 at VA 007FF000','t16xion':'.t16 at VA 00800000'}
TITLE={'kessel':'Any craft on Rescue on Kessel, all with the ion cannon','anycraft':'Any craft on the airspeeder missions (replaces [mission7]; the installer no longer applies [mission7], it only reads it as this option)',
 'nonah':'Killable Imperial landing craft (The Search for the Nonah)','bios':"Kasan Moor's biography always reachable",'failselect':'Game over returns to mission select',
 't16b':'T-16 update 1.3: X-wing turn values, crosshair, chase camera, hit boxes','t16xb':'T-16 update 1.3 (same, .t16 after .conv)',
 't16ion':'T-16 ion cannon aim (with the Kessel option)','t16xion':'T-16 ion cannon aim (with the Kessel option, .t16 after .conv)'}
src=open(r'mkdata.py',encoding='utf-8').read()
import re
comments={}
for m in re.finditer(r"R\((0x[0-9A-F]+),\d+[^)]*?c='([^']*)'",src): comments[int(m.group(1),16)]=m.group(2)
out=['','='*78,'2026-11-25 additions (version 1.3). Hand-written groups; see src'+chr(92)+'v13pkg'+chr(92)+'mkdata.py.','='*78]
for k in ['kessel','anycraft','nonah','bios','failselect','t16b','t16xb','t16ion','t16xion']:
    runs=g[k]
    out+=['','='*78,'[%s] %s  (%d changes)%s'%(k,TITLE[k],len(runs),('  - '+NOTE[k]) if k in NOTE else ''),'='*78]
    for o,old,new in runs:
        va=orig.va(o)
        out.append('  off %06X  (VA %08X %s)  %s -> %s'%(o,va,secname(va),old.hex(),new.hex()))
        if o in comments: out.append('        ; '+comments[o])
        if o in CODE and k not in ('t16b','t16ion'):
            c=CODE[o]; start,n=(c if isinstance(c,tuple) else (va,c))
            for line in live.dis(start,n).splitlines(): out.append('        '+line)
out+=['','='*78,'[.t16 section data] T-16 update 1.3 (both T16Section arrays)','='*78,
 '  .t16+0x64C  TANDOWN (tan of the aim-down angle) 0.1317 (7.5 deg) -> -0.025 (about 1.4 deg up; the crosshair and camera moved)',
 '  .t16+0xA00  hit-box hook cave, called from 0x41D161 (T-16 create):',
 '              mov ecx,[ebp-8] / mov [ecx],eax (replayed); if model && model data: [[model]+0x58] = .t16+0xA40; ret',
 '  .t16+0xA40  collision list: 13 boxes of 0x1C bytes (u8 kind 0, u8 node 0, u16 0, min xyz, max xyz floats, model units)',
 '              body, 4 stepped fin boxes, 4 stepped boxes per wing; ends with node 0xFF (src'+chr(92)+'v13'+chr(92)+'t16hitbox.py, margin 1.5)']
for line in live.dis(0x800A00,10,True).splitlines(): out.append('        '+line)
lst=live.rd(0x800A40,14*0x1C)
for i in range(14):
    kind,node,_=struct.unpack_from('<BBH',lst,i*0x1C); f=struct.unpack_from('<6f',lst,i*0x1C+4)
    out.append('        box %2d  kind %d node %02X  min (%7.2f %7.2f %7.2f)  max (%7.2f %7.2f %7.2f)'%(i,kind,node,*f))
p=r'G:/Dev/RogueSquadronMods/dist/PATCHES.txt'
t=open(p,'rb').read().decode('ascii')
assert '[kessel]' not in t
t=t.rstrip('\r\n')+'\r\n'+'\r\n'.join(out)+'\r\n'
open(p,'wb').write(t.encode('ascii'))
print(len(out),'lines')
