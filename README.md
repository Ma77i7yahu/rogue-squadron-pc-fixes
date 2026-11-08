# Star Wars: Rogue Squadron 3D (PC) – Widescreen and Flight Mods

Optional fixes and improvements for the PC version of **Star Wars: Rogue Squadron 3D**: 16:9 widescreen, stick deadzone and response fixes, aim assist removal or laser auto-convergence, a playable T-16 Skyhopper, and more. Each mod can be turned on or off on its own, and the installer keeps a backup so you can change options or undo everything at any time.

**This is a patch only.** No game files are included. You need your own copy of the game.

## Download

Get the latest version from the [**Releases**](https://github.com/Ma77i7yahu/rogue-squadron-pc-fixes/releases/latest) page. Pick the one that matches your copy of the game:

| Your copy | Download | Instructions |
|---|---|---|
| CD, with the official v1.2 update | `RogueSquadronMods-CD-v1.0.zip` | [README-CD](docs/README-CD.md) |
| Steam | `RogueSquadronMods-Steam-v1.0.zip` | [README-Steam](docs/README-Steam.md) (unwrap the exe with Steamless first) |
| GOG | `RogueSquadronMods-GOG-v1.0.zip` | [README-GOG](docs/README-GOG.md) (read the joystick note before creating a pilot) |

Each zip holds the installer, its README and `PATCHES.txt`. The installer checks your exe's MD5 and won't touch a version it doesn't recognise. `SHA256SUMS.txt` on the release page lets you check your download.

## The mods

| Mod | Default | Status |
|---|---|---|
| Remove per-craft stick deadzones | On | Tested |
| Remove aim assist (all craft except the Falcon) | On | Tested |
| Laser auto-convergence (replaces aim assist) | Off | Tested |
| Rogue Leader style flight + tight-turn button | Off | Tested |
| Faster lasers | Off | Tested |
| Linear stick response | On | Tested |
| Small stick movement fix | On | Tested |
| Higher airspeeder ceiling | On | Tested |
| 16:9 widescreen (Hor+) | On | Tested at 1920 x 1080 |
| T-16 Skyhopper as a selectable craft | Off | Tested in full missions |
| Any craft on Imperial Construction Yards (mission 7) | Off | Tested (T-16 there not yet flown) |
| Every craft repairs itself | Off | Repair tested; 25% cut-off not yet flown |

What each one changes, and how, is explained in the README for your version.

## What's in this repo

- `docs/`: the README for each version (the same files as in the zips).
- `PATCHES.txt`: every changed byte with its file offset, virtual address, old and new value, and disassembly. Use it to apply the mods by hand or to port them.
- `src/`: the installer's C# source, the patch generator and the assembly source of the code caves. See [BUILDING.md](BUILDING.md).
- `test/`: the test tools used to check the installer's output.

## Licence

The code, patches and documentation here are under the [MIT licence](LICENSE): reuse or port them freely, with credit. The game itself isn't covered.

## Disclaimer

Unofficial fan-made mods, not affiliated with or endorsed by Lucasfilm, LucasArts, Disney, Factor 5, Steam or GOG. Star Wars and Rogue Squadron are trademarks of their owners. No game files are distributed here. Use at your own risk, and keep the backups the installer makes.
