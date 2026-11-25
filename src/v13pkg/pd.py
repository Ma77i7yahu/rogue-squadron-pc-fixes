# Parses PatchData.cs: groups {key: [(offset, old, new)]}, T-16 sections, constants.
import re
SRC=r'G:/Dev/RogueSquadronMods/src/PatchData.cs'
def hb(s): return bytes(int(x,16) for x in re.findall(r'0x([0-9A-Fa-f]{2})',s))
def load(path=SRC):
    t=open(path,encoding='utf-8').read()
    groups={}; order=[]
    for m in re.finditer(r'new Patch\("(\w+)", new Run\[\]\{(.*?)\n        \}\)',t,re.S):
        runs=[]
        for r in re.finditer(r'new Run\(0x([0-9A-Fa-f]+), new byte\[\]\{([^}]*)\}, new byte\[\]\{([^}]*)\}\)',m.group(2)):
            runs.append((int(r.group(1),16),hb(r.group(2)),hb(r.group(3))))
        groups[m.group(1)]=runs; order.append(m.group(1))
    secs={}
    for m in re.finditer(r'T16Section_(\w+) = new byte\[\]\{([^}]*)\}',t): secs[m.group(1)]=hb(m.group(2))
    return groups,order,secs
def isin(img,runs): return all(img[o:o+len(n)]==n for o,_,n in runs)
