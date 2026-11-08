@echo off
rem Rebuilds PatchData.cs + ..\dist\PATCHES.txt from the tested exes, then the installer.
rem Usage: build.cmd ["path to Rogue Squadron folder holding the .original/.4x3/... exes"]
cd /d "%~dp0"
G:\msys64\mingw64\bin\python.exe -I gen.py %1 || exit /b 1
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize /out:..\dist\RogueSquadronModInstaller.exe /r:System.Windows.Forms.dll /r:System.Drawing.dll Installer.cs PatchData.cs BundleMenu.cs || exit /b 1
rem Steam build: same patches, accepts only the Steamless-unwrapped Steam exe. Its README is kept by hand.
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize /define:STEAM /out:..\dist\Steam\RogueSquadronModInstaller-Steam.exe /r:System.Windows.Forms.dll /r:System.Drawing.dll Installer.cs PatchData.cs BundleMenu.cs || exit /b 1
copy /y ..\dist\PATCHES.txt ..\dist\Steam\PATCHES.txt >nul
rem GOG build: same patches, accepts only GOG's exe, and turns off GOG's XP compatibility mode. Its README is kept by hand.
if not exist ..\dist\GOG mkdir ..\dist\GOG
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize /define:GOG /out:..\dist\GOG\RogueSquadronModInstaller-GOG.exe /r:System.Windows.Forms.dll /r:System.Drawing.dll Installer.cs PatchData.cs BundleMenu.cs || exit /b 1
copy /y ..\dist\PATCHES.txt ..\dist\GOG\PATCHES.txt >nul
