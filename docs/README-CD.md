# Star Wars: Rogue Squadron 3D (PC) – Widescreen and Flight Mods

Optional fixes for the PC version of **Star Wars: Rogue Squadron 3D** (v1.2 update, US exe). Each one can be turned on or off on its own. All of them are changes to `Rogue Squadron.EXE`, except the in-game toggle for laser convergence, which edits `Bundle.002` (backed up first).
## Installing

1. Install Rogue Squadron 3D and the official **1.2 update**.
2. Run `RogueSquadronModInstaller.exe`. If it's inside the game folder it finds the game on its own. Otherwise, click **Browse…** and pick the folder that holds `Rogue Squadron.EXE`.
3. Tick the options you want. Point at any option to see what it does.
4. Click **Install selected**.
5. If you chose widescreen, start the game, open **Options → Video** and select the widescreen resolution. It replaces 1280 x 1024 in the list.

On first use the installer saves your untouched exe as `Rogue Squadron.original.EXE` (and `Bundle.002` as `Bundle.002.original` when you choose laser convergence). Every later install rebuilds the exe from that backup, so you can run the installer again at any time to change options. It shows the options that are installed now. **Restore original exe** removes everything.

The installer only accepts the unmodified v1.2 exe (2,492,928 bytes, MD5 `2D5EE8852EB99F329318325C51742324`) or a folder holding that backup. Close the game before installing.

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
| Single solid orange crosshair | On | Tested |

Laser auto-convergence uses the game's own targeting, so it replaces "Remove aim assist" (the installer won't let you tick both). Rogue Leader style flight shares convergence's code section, so it switches convergence on with it; you can still turn convergence off in the game. Everything else can be combined freely. Laser auto-convergence and the T-16 each add their own code section to the exe.

### Remove per-craft stick deadzones
Rogue Squadron applies three deadzones to the stick:

| Stage | Size |
|---|---|
| DirectInput | 5.12% |
| Shared game input code | 1.5% |
| Each craft's flight setup | 10–25% |

The per-craft one is subtracted on top of the others and never scaled back up. As a result, about 15% of travel around centre did nothing and full stick gave only about 90% input. You feel this as a numb centre, then a sudden turn, and slow turn reversals.

This mod sets all 20 per-craft values to 0, covering both axes on 10 craft setups:

| Craft | Roll/turn | Pitch |
|---|---|---|
| X-wing, A-wing, Falcon, TIE Interceptor, Naboo starfighter and others | 10% | 10% |
| Y-wing | 10% | 15% |
| Airspeeder | 20% | 15% |
| V-wing | 25% | 25% |

The DirectInput and shared deadzones stay. Battle for Naboo uses the same two.

### Remove aim assist (all craft except the Falcon)
Most craft bend their shots toward any enemy inside a cone around the nose. On the A-wing, the wingtip guns swivel to track the target at about 21°/s.

| Craft | Cone |
|---|---|
| A-wing | 15° |
| Y-wing ion turret | 15.2° |
| X-wing, TIE Interceptor, Naboo starfighter | 7.3° |
| V-wing, airspeeder | 9.2° |

The mod sets each cone's cosine to 2.0, which no angle can match, so shots always go where the crosshair points. The Millennium Falcon (27°) has turrets that are meant to track, so it's left alone. The T-16 Skyhopper option uses the X-wing's cone, so it follows this setting.

### Laser auto-convergence (replaces aim assist)
This works like X-Wing's auto convergence and is **not** aim assist. The game's own targeting still picks the enemy in your crosshairs, but instead of bending your shots toward it, the mod moves the aim point onto the line straight ahead of your nose, at the target's range. Each craft also turned its bolts only part of the way toward the aim point (40–80%), so that's set to the full turn. The result: your lasers converge where the crosshair is, at the right range, so close-range shots no longer spread wide. All player craft except the Millennium Falcon, whose turrets keep tracking.

It adds **Enable Laser Convergence** to **Options → General Settings** in the game, on by default, with its own help line. Switched off there, shots fly straight with no aim assist at all. The setting is saved per pilot. The toggle is an edit to the settings screen inside `Bundle.002`, which the installer backs up as `Bundle.002.original` and puts back if you remove the option.

It works through a hook at the end of the game's target finder and a new `.conv` section.

### Rogue Leader style flight + tight-turn button
This changes turning to feel like Star Wars: Rogue Leader:
- **Turn:** about 36°/s at full stick, rising evenly with the stick.
- **Bank:** the craft banks with the stick (up to 50°) and levels out when you centre it.
- **Tight-turn button:** hold it to blend (over 0.3 s) to the game's own flight, with its tight turn. Choose the button in the installer (default 9). The number is the one Windows gives it (Control Panel → Game Controllers → Properties). Don't also bind that button to something in the game's controls.
- **Stock flight where it works better:** the game's own flight also takes over in steep climbs and dives (blending between 35° and 55°), when you roll far over (blending between about 66° and 84° of roll), and while towing an AT-AT with the airspeeder's tow cable.

The code lives in the `.conv` section, so this option needs laser auto-convergence and ticks it for you. If you don't want convergence, turn it off in the game's General Settings.

### Faster lasers
Your craft's laser bolts fly twice as fast (closer to Rogue Leader), so they reach the target sooner and need less lead. The same speed is the lead the targeting uses, so that's doubled too. The fire rate is unchanged, and enemy and wingman lasers are untouched. 20 single values change: the bolt speed in each player craft's fire call and the matching lead value in each craft's targeting call.

### Linear stick response
The game squares the roll/turn and pitch input (`X*|X|`). This curve suits a gamepad: 50% stick gives 25% input. On a joystick it makes the middle of the travel weak and the end sudden. The mod jumps over the squaring, so 50% stick gives 50% input on every craft.

### Small stick movement fix
The flight code zeroes any turn, pitch or roll rate under 0.1° per frame. At modern frame rates, that ignores stick movements under about 12%. The mod points the three compares at an existing 0.001 constant in the exe. Small movements now respond from about 3% stick, at roughly 1°/s per 1% of stick.

### Higher airspeeder ceiling
The airspeeder and V-wing have a ceiling that follows the terrain: the ground height under the craft plus a per-craft value, and never above the mission's own ceiling. Over the last 2.5 units the craft's climb fades out. The airspeeder's value is 10 and the V-wing's is 20. This mod raises the airspeeder's value to 20 (one float in its init code). Every other craft only has the mission ceiling, which is unchanged.

### 16:9 widescreen (Hor+)
- **Aspect ratio:** the renderer's fixed 4/3 is changed to 16/9. The vertical view is unchanged and the extra width is added at the sides, so nothing is cropped.
- **Resolution:** the chosen 16:9 resolution replaces the 1280 x 1024 entry in the video menu. 1920 x 1080 is tested. 1280 x 720, 1600 x 900, 2560 x 1440 and 3840 x 2160 are offered but untested.
- **Terrain edges:** the terrain view pyramid is widened from a corner of −4 to −16/3, so land is generated across the whole screen with no jagged edges.
- **Radar:** the radar map's sideways position and scale are multiplied by 4/3 (0.55 → 0.733 and 0.13 → 0.173), which puts it back inside its ring.
- **Draw distance:** the wider pyramid pulled the far terrain edge about 10–15% closer straight ahead. A small code cave multiplies the terrain distance by 1.16 so the fog hides the edge again.
- **Terrain grid overflow:** the terrain builder fills a fixed 64x64 grid with no bounds checks. The wider view could overflow it, which corrupted the terrain scale and the fog. The visible symptom was a white screen and broken terrain when Moff Seerden's shuttle lands in *Moff Seerden's Revenge*. A second code cave clamps the four frustum corners to ±30.5 cells around the camera.

Known limits:
- The 2D HUD and menus are still stretched.
- Every menu resolution uses 16:9, so pick the widescreen one.

### T-16 Skyhopper as a selectable craft
The T-16 from Beggar's Canyon is complete in the game (model, cockpit, flight code), but you can only fly it in that bonus level. This option makes it selectable on every mission that allows the X-wing, except the airspeeder-only missions. With the mission 7 option it's offered on Imperial Construction Yards too.

- **Hangar:** it gets its own bay between the V-wing and the Y-wing, with its own launch. The airspeeder keeps its bay.
- **Lasers:** the X-wing's laser sound and fire rate (10 shots/s; the T-16's own was 3.3/s), and the X-wing's target lock.
- **Torpedoes:** 6 proton torpedoes like the X-wing (the game gave it no secondary weapon).
- **Aim:** the T-16 model is far larger than the others, so its crosshair sits below its line of fire. Its lasers and dumbfire torpedoes are aimed 7.5° below the nose line so they land on the crosshair.
- **Game bug fixes:** two bugs in the original T-16 code only show up outside Beggar's Canyon. It freed its control block before the weapon cleanup that still uses it, and that block was too small for the targeting data.

It adds a new code section, `.t16`, after the exe's last section, so it works with or without the other options. It has been flown in full missions (hangar launch, combat, end cutscene) with our tester's own set of flight mods. With the installer's option sets it is byte-checked but not yet flown.

### Any craft on Imperial Construction Yards (mission 7)
The game makes four levels airspeeder-only because they have AT-ATs: Defection at Corellia, Imperial Construction Yards, Escape from Fest and the Battle of Hoth. In Imperial Construction Yards you don't have to bring down an AT-AT to win, so this option lifts the restriction there only.

A level's craft list starts from its default craft, and the X-wing, A-wing and V-wing unlocks only apply when that default is one of those three. Mission 7's default is the airspeeder, so taking it off the speeder-only list would still leave only the airspeeder. The patch therefore rewrites the start of both craft-list functions (the hangar's and the one the menus use) so that mission 7 also gets the X-wing. Your normal unlocks then apply on top: A-wing, V-wing, Millennium Falcon and TIE Interceptor, plus the T-16 if that option is installed. The airspeeder stays the hangar default. AT-ATs can still only be brought down with the airspeeder's tow cable.

### Every craft repairs itself
In the stock game, the craft with an astromech droid or a crew slowly repair damage, at 1/180 of full health per second (full repair in 3 minutes). These are the X-wing, Y-wing, Naboo starfighter and Millennium Falcon. The A-wing, V-wing, airspeeder, TIE Interceptor and T-16 don't repair at all. This mod rewrites the repair function in place (same size, `src/caves/repair_all.s`) so every craft repairs at that rate.

In the stock game the X-wing, Y-wing and Naboo starfighter lose their droid when their health drops below a quarter (you hear R2 get hit), and then stop repairing for the rest of that life. The mod gives the A-wing, V-wing, airspeeder, TIE Interceptor and T-16 the same cut-off, without the droid speech. It uses the same "droid lost" flag, which on these craft does nothing else. The Millennium Falcon has a crew rather than a droid, so it keeps repairing at any health, as in the stock game. Repair stays off where the game turns it off for everyone.

### Single solid orange crosshair
The crosshair is two green rings: a big one drawn close to the craft and a small one further out. The lasers meet the small one; the big one sits well below it from the chase camera and only confuses where the shots go. The pale, half see-through green is also hard to see against the terrain.

This removes the big ring, in normal flight and in the torpedo targeting view, so the crosshair is the small ring only. It's drawn in orange at twice the stock opacity (200/255 instead of 100/255), matching the Battle for Naboo mod. The big ring's position and fade are still worked out, because the torpedo view's small ring takes its fade from it; it just isn't drawn. Aiming is unchanged, and missile and torpedo lock markers keep their colours. 13 bytes (`src/build_gunsight.py`).

## Not included
- **DxWrapper, dinput.dll camera fix, rsLauncher, wingman.dll:** these are third-party files some setups use. They're not part of these mods and the installer doesn't touch them.
- **Roll sensitivity boost (1024 → 800 divisor):** tried, then reverted. The problem it targeted turned out to be worn joystick hardware.

## Files
- `RogueSquadronModInstaller.exe`: the installer. It's a .NET Framework 4 app, which is built into Windows 10 and 11.
- `PATCHES.txt`: every changed byte with its file offset, virtual address, old and new value, and disassembly. Use it to apply the mods by hand or to port them.
- Source code (not needed to install): the installer's C# source, the patch generator, and the assembly source of the laser convergence, Rogue Leader flight, repair and T-16 code. It's in the `src` folder of the GitHub repo: https://github.com/Ma77i7yahu/rogue-squadron-pc-fixes
