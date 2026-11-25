# Adds the 2026-11-22..25 changes to PatchData.cs (hand-written groups + T-16 section updates).
import pd,struct,re
orig=open('orig.exe','rb').read()
live=open(r'G:/Game Files/LucasArts/Star Wars Rogue Squadron/Rogue Squadron.EXE','rb').read()
LSEC=0x261A00
def R(o,l,new=None,c=''):
    nw=new if new is not None else live[o:o+l]
    return (o,orig[o:o+l],nw,c)
def rel(frm,to): return struct.pack('<i',to-(frm+5))
G={}
G['kessel']=[R(0x3B278,15,c='ammo fn 0x43BE72: weapon 1 (ion cannon) -> 0xFF (unlimited) for every craft'),
  R(0x3B28C,1),
  R(0x3C408,9,c='Kessel (level 8) hangar mask: |= 2 (Y-wing always), &= ~0x10'),
  R(0x3C519,9,c='same in the menu mask fn'),
  R(0x3C62E,2,c='secondary weapon fn: ion cannon for every craft, not only craft 0'),
  R(0x7A8F8,2,c='HUD: no ammo number for any craft carrying the ion cannon')]
G['anycraft']=[R(0x3C2CB,21,c='hangar mask prologue: X-wing bit added when the level default craft is the airspeeder'),
  R(0x3C414,1,c='speeder-only level list (3,6,0xB,0x12) cmps -> -1'),R(0x3C41A,1),R(0x3C420,1),R(0x3C426,1),
  R(0x3C44D,21,c='menu mask prologue, same'),R(0x3C525,1),R(0x3C52B,1),R(0x3C531,1),R(0x3C537,1)]
G['nonah']=[R(0xA86C1,25,c='Shuttle HP callback 0x4A92BF: HP >= 65536 (lifters, 1,000,000) -> 10000')]
G['bios']=[R(0x3C6EE,2,c='bio page count 0x43D2E0: jl NOPped, Kasan Moor page always reachable')]
G['failselect']=[R(0x6C5A8,7,c='game-over block 0x46D1A8: call 0x43AE82 (reset lives, game stays in progress)'),
  R(0x6C5D7,1,c='0x704962 high-score flag 1 -> 0: back to mission select')]
common=[R(0x1BC40,3,c='T-16 init 0x41C780: X-wing turn values (F8 1.6, FC 1.75, P114 -30, P118 40)'),R(0x1BC4F,2),R(0x1BC9D,2),R(0x1BCAA,2),
  R(0x21FAC,1,c='gunsight 0x422B50 T-16 branch: near/far points along fwd (+0xC/+0x10/+0x14)'),R(0x21FBB,1),R(0x21FCA,1),
  R(0x1BEC68,4,c='T-16 sight distance constant 0.7 -> 12.0'),
  R(0x1F4DD2,1,c='T-16 chase camera (mode 2) = X-wing mode 2 x3'),R(0x1F4DF2,6),R(0x1F4DFE,5)]
for k,base in (('t16b',0x7FF000),('t16xb',0x800000)):
    G[k]=common+[R(0x1C561,5,b'\xe8'+rel(0x41D161,base+0xA00),c='T-16 create: hit-box list hook -> .t16+0xA00')]
for k,base in (('t16ion',0x7FF000),('t16xion',0x800000)):
    G[k]=[R(0x235DB,9,b'\xe8'+rel(0x4241DB,base+0x8EA)+b'\x90'*4,c='ion cannon case: T-16 aim (.t16+0x8EA), with the Kessel option')]
for k,v in G.items():
    for o,old,new,c in v: assert len(old)==len(new),(k,hex(o))
# sanity: Old must equal the original, New must equal live (except variant-specific)
assert live[0x1C561:0x1C566]==G['t16xb'][-1][2], live[0x1C561:0x1C566].hex()
assert live[0x235DB:0x235E4]==G['t16xion'][0][2]
def cs(b): return ','.join('0x%02X'%x for x in b)
lines=['        // 2026-11-25 additions (hand-written by src\\v13pkg\\mkdata.py from the tested exes; gen.py does not know them)']
for k,v in G.items():
    lines.append('        new Patch("%s", new Run[]{'%k)
    for o,old,new,c in v:
        lines.append('            new Run(0x%06X, new byte[]{%s}, new byte[]{%s}),%s'%(o,cs(old),cs(new),('   // '+c) if c else ''))
    lines.append('        }),')
t=open(r'..\PatchData.cs',encoding='utf-8').read()
assert 'new Patch("kessel"' not in t
i=t.index('    };\n    // T-16 section data')
t=t[:i]+'\n'.join(lines)+'\n'+t[i:]
# T-16 sections: aim + hit box
cave=bytearray(live[LSEC+0xA00:LSEC+0xBAE])
ref=struct.pack('<I',0x800A40); assert cave.count(ref)==1
for key,base in (('3FF000',0x7FF000),('400000',0x800000)):
    m=re.search(r'(T16Section_%s = new byte\[\]\{)([^}]*)(\})'%key,t)
    sec=bytearray(pd.hb(m.group(2))); assert len(sec)==0x1000
    assert sec[0x64C:0x650]==bytes.fromhex('eacf063e') and not any(sec[0xA00:0xBAE])
    sec[0x64C:0x650]=live[LSEC+0x64C:LSEC+0x650]
    cv=bytearray(cave); j=cv.index(ref); cv[j:j+4]=struct.pack('<I',base+0xA40)
    sec[0xA00:0xBAE]=cv
    if key=='400000': assert bytes(sec)==live[LSEC:LSEC+0x1000]
    t=t[:m.start(2)]+cs(sec)+t[m.end(2):]
t=t.replace('// 2026-11-08: "gunsight" group appended by hand','// 2026-11-25: kessel/anycraft/nonah/bios/failselect/t16b/t16xb/t16ion/t16xion + T-16 section aim/hit box added by\n// src\\v13pkg\\mkdata.py. 2026-11-08: "gunsight" group appended by hand',1)
open(r'..\PatchData.cs','w',encoding='utf-8',newline='\n').write(t)
print('ok', {k:len(v) for k,v in G.items()})
