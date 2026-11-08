# Building

You don't need any of this to install the mods. It's for anyone who wants to rebuild the installer or port the patches.

## Installer only

`src/PatchData.cs` already holds every patch, so the installer builds with the C# compiler that ships with Windows (.NET Framework 4):

```
cd src
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize /out:RogueSquadronModInstaller.exe /r:System.Windows.Forms.dll /r:System.Drawing.dll Installer.cs PatchData.cs BundleMenu.cs
```

Add `/define:STEAM` or `/define:GOG` for the Steam or GOG build.

## Regenerating the patches

`src/build.cmd` runs `gen.py` first, which rebuilds `PatchData.cs` and `PATCHES.txt` by comparing a set of tested variant exes against the original v1.2 exe. Those exes are modified copies of the game's exe, so they aren't in this repo. The `build_*.py` scripts produce them from the original exe and the assembly in `src/caves/`.

The scripts were written for one machine, so check the paths at the top of each before running them:

- `GAME`: the Rogue Squadron folder holding the exes.
- `BIN`: a MinGW-w64 toolchain (`as`, `objcopy`, Python), for example from MSYS2.

## Tests

`test/harness.cs` and `test/gogtest.cs` load the installer by reflection and compare its output exes against known-good builds. `test/uia.ps1` holds small helpers for driving the installer's window.
