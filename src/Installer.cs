// Star Wars: Rogue Squadron 3D (PC v1.2) mod installer.
// Applies any combination of the optional exe patches in PatchData.cs to a
// copy of the untouched exe. The original is always kept as
// "Rogue Squadron.original.EXE", so every option can be changed or removed later.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Windows.Forms;

class Run {
    public readonly int Offset; public readonly byte[] Old, New;
    public Run(int offset, byte[] old, byte[] nw) { Offset = offset; Old = old; New = nw; }
}

class Patch {
    public readonly string Key; public readonly Run[] Runs;
    public Patch(string key, Run[] runs) { Key = key; Runs = runs; }
    public int End { get { return Runs.Max(r => r.Offset + r.New.Length); } }
    public bool IsIn(byte[] exe) {
        foreach (var r in Runs) {
            if (r.Offset + r.New.Length > exe.Length) return false;
            for (int i = 0; i < r.New.Length; i++) if (exe[r.Offset + i] != r.New[i]) return false;
        }
        return true;
    }
}

class Option {
    public string Key, Title, Info;
    public Control Box;
}

class InstallerForm : Form {
    const string ExeName = "Rogue Squadron.EXE";
    const string BackupName = "Rogue Squadron.original.EXE";
#if STEAM
    // Steam build (csc /define:STEAM). The Steam release is the same v1.2 exe wrapped in SteamStub 3.1.
    // Unwrapped with Steamless 3.1.0.5 it differs from the CD exe only in the blanked DOS stub and
    // Steam's 1-byte no-CD patch at 0x4EC47E, which no option touches, so the same patches apply.
    const string SteamPackedMd5 = "63c5c36b04ed2b47a0c84b45d0a43223";
    const string SteamUnpackedMd5 = "6684a72bdb34bb9657815740cbcf52cb";
#elif GOG
    // GOG build (csc /define:GOG). GOG's exe is the CD v1.2 exe with the same 1-byte no-CD patch as
    // Steam's (0x4EC47E), so the same patches apply.
    const string GogMd5 = "2b1658c168e1c379b2298a5acae60daf";
#endif

    static readonly int[][] Resolutions = {
        new[]{1920,1080}, new[]{1280,720}, new[]{1600,900}, new[]{2560,1440}, new[]{3840,2160} };

    readonly TextBox folder = new TextBox();
    readonly Label status = new Label();
    readonly TextBox info = new TextBox();
    readonly ComboBox res = new ComboBox(), rlButton = new ComboBox();
    readonly List<Option> options = new List<Option>();
    readonly Button install = new Button(), restore = new Button();
    byte[] baseExe;

    Option Opt(string key) { return options.First(o => o.Key == key); }
    bool On(string key) {
        var b = Opt(key).Box;
        return ((CheckBox)b).Checked;
    }
    void Set(string key, bool v) {
        var b = Opt(key).Box;
        ((CheckBox)b).Checked = v;
    }

    InstallerForm() {
        Text = "Star Wars: Rogue Squadron 3D - Mod Installer";
#if STEAM
        Text += " (Steam version)";
#elif GOG
        Text += " (GOG version)";
#endif
        Font = new Font("Segoe UI", 9f);
        AutoScaleMode = AutoScaleMode.Dpi;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        AutoSize = true; AutoSizeMode = AutoSizeMode.GrowAndShrink;
        Padding = new Padding(10);

        var root = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false };
        Controls.Add(root);

        // game folder
        var fl = new FlowLayoutPanel { AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false, Margin = new Padding(0) };
        fl.Controls.Add(new Label { Text = "Game folder:", AutoSize = true, Margin = new Padding(0, 7, 4, 0) });
        folder.Width = 470;
        folder.Margin = new Padding(0, 3, 4, 0);
        folder.Leave += (s, e) => LoadFolder();
        fl.Controls.Add(folder);
        var browse = new Button { Text = "Browse...", AutoSize = true };
        browse.Click += (s, e) => {
            using (var d = new FolderBrowserDialog { Description = "Select the Rogue Squadron folder (the one containing \"Rogue Squadron.EXE\")" }) {
                if (Directory.Exists(folder.Text)) d.SelectedPath = folder.Text;
                if (d.ShowDialog(this) == DialogResult.OK) { folder.Text = d.SelectedPath; LoadFolder(); }
            }
        };
        fl.Controls.Add(browse);
        root.Controls.Add(fl);
        status.AutoSize = true; status.MaximumSize = new Size(640, 0); status.Margin = new Padding(0, 4, 0, 6);
        root.Controls.Add(status);

        // option groups
        var g1 = Group(root, "Flight and controls");
        Check(g1, "deadzone", "Remove per-craft stick deadzones",
            "Every craft subtracted its own 10-25% deadzone from the stick on top of the 5% DirectInput one, so " +
            "about 15% of travel around centre did nothing and full stick only gave ~90% input.\r\n\r\n" +
            "Sets all 20 per-craft deadzone values (X-wing, A-wing, Y-wing, airspeeder, V-wing, Falcon, TIE " +
            "Interceptor, Naboo starfighter and others) to 0. The 5% DirectInput and 1.5% shared deadzones stay, " +
            "same as Battle for Naboo.\r\n\r\nStatus: tested.");
        Check(g1, "aimassist", "Remove aim assist (all craft except the Millennium Falcon)",
            "Most craft bend their lasers toward any enemy inside a small cone around the nose: A-wing 15 deg, " +
            "Y-wing ion turret 15 deg, X-wing / TIE Interceptor / Naboo starfighter 7.3 deg, V-wing / airspeeder 9.2 deg.\r\n\r\n" +
            "This sets each cone so nothing can ever match, so shots go where the crosshair points. The Falcon's " +
            "turrets (27 deg) are designed to track and are left alone. The T-16 Skyhopper option below uses the " +
            "X-wing's cone, so it follows this setting.\r\n\r\nStatus: tested.");
        Check(g1, "convergence", "Laser auto-convergence (X-Wing style, replaces aim assist)",
            "Like X-Wing's auto convergence (NOT aim assist): when the game's own targeting picks up an enemy in your " +
            "crosshairs, your lasers converge at its range on the line straight ahead of your nose, instead of bending " +
            "toward the target. They hit what the crosshair is on, and close-range shots no longer spread wide. All " +
            "player craft except the Millennium Falcon, whose turrets keep their tracking.\r\n\r\n" +
            "Adds \"Enable Laser Convergence\" to Options > General Settings in the game (on by default). Switched off " +
            "there, shots fly straight with no aim assist at all. This edits the game's Bundle.002 file, which is backed " +
            "up as \"Bundle.002.original\" first.\r\n\r\n" +
            "Can't be combined with \"Remove aim assist\" (it uses the game's targeting).\r\n\r\nStatus: tested.");
        var rlRow = new FlowLayoutPanel { AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false, Margin = new Padding(0) };
        Check(rlRow, "rlflight", "Rogue Leader style flight + tight-turn button",
            "Turning like Star Wars: Rogue Leader: about 36 deg/s at full stick, rising evenly with the stick, and the " +
            "craft banks with the stick (up to 50 deg) and levels out when you centre it.\r\n\r\n" +
            "Hold the tight-turn joystick button to blend (over 0.3 s) to the game's own flight with its tight turn. " +
            "The game's own flight also takes over in steep climbs and dives, when upside down, and while towing an AT-AT " +
            "with the airspeeder. The button number is the one Windows gives it (Game Controllers > Properties); don't " +
            "also bind it to something in the game's controls.\r\n\r\n" +
            "Needs laser auto-convergence (it shares its code section). If you don't want convergence, switch it off " +
            "in the game's General Settings.\r\n\r\nStatus: tested.");
        rlButton.DropDownStyle = ComboBoxStyle.DropDownList;
        for (int i = 1; i <= 16; i++) rlButton.Items.Add("Button " + i);
        rlButton.SelectedIndex = 8;
        rlButton.Margin = new Padding(12, 2, 0, 0);
        rlButton.Width = 100;
        rlRow.Controls.Add(rlButton);
        Panel(g1).Controls.Add(rlRow);
        Check(g1, "lasers", "Faster lasers",
            "Your craft's laser bolts fly twice as fast, closer to Rogue Leader, so they reach the target sooner and " +
            "need less lead. The targeting's lead is doubled to match. The fire rate is unchanged, and enemy and " +
            "wingman lasers are untouched.\r\n\r\nStatus: tested.");
        Check(g1, "linear", "Linear stick response",
            "The game squares roll/turn and pitch input (50% stick = 25% input), a gamepad-style curve that makes " +
            "the middle of a joystick's travel feel weak and the end sudden.\r\n\r\n" +
            "Skips the squaring, so 50% stick = 50% input on every craft.\r\n\r\nStatus: tested.");
        Check(g1, "smallmoves", "Small stick movement fix",
            "The flight code throws away any turn/pitch/roll rate under 0.1 degrees per frame. At high frame rates " +
            "that ignores stick movements under about 12%, so fine aiming corrections do nothing.\r\n\r\n" +
            "Lowers the cut-off to 0.001 degrees per frame. Small movements now respond from about 3% stick.\r\n\r\n" +
            "Status: tested.");
        Check(g1, "ceiling", "Higher airspeeder ceiling",
            "The airspeeder can only climb 10 units above the ground under it, and its climb fades out over the " +
            "last 2.5 units, which feels like flying into an invisible lid.\r\n\r\n" +
            "Doubles that to 20 units, the same as the V-wing. The mission's own ceiling still applies on top, as it " +
            "does for every craft.\r\n\r\nStatus: tested.");

        var g2 = Group(root, "Widescreen");
        var wsRow = new FlowLayoutPanel { AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false, Margin = new Padding(0) };
        Check(wsRow, "widescreen", "16:9 widescreen (Hor+)",
            "Changes the 3D view from 4:3 to 16:9 by adding width at the sides (Hor+), so nothing is cropped.\r\n\r\n" +
            "Includes:\r\n- terrain generated across the full width (no jagged edges)\r\n- radar map back inside its ring\r\n" +
            "- terrain distance x1.16 so the fog still hides the terrain edge\r\n" +
            "- a terrain-grid overflow fix (stops the white screen / broken terrain when Moff Seerden's shuttle lands)\r\n" +
            "- the chosen 16:9 resolution replaces 1280x1024 in the video menu. Select it in Options > Video.\r\n\r\n" +
            "Known limits: the 2D HUD and menus are still stretched. All menu resolutions use 16:9, so pick the widescreen one.\r\n\r\n" +
            "Status: tested at 1920x1080. Other resolutions are untested.");
        res.DropDownStyle = ComboBoxStyle.DropDownList;
        foreach (var r in Resolutions) res.Items.Add(r[0] + " x " + r[1] + (r[0] == 1920 ? "  (tested)" : "  (untested)"));
        res.SelectedIndex = 0;
        res.Margin = new Padding(12, 2, 0, 0);
        res.Width = 160;
        wsRow.Controls.Add(new Label { Text = "Resolution:", AutoSize = true, Margin = new Padding(16, 6, 0, 0) });
        wsRow.Controls.Add(res);
        Panel(g2).Controls.Add(wsRow);

        var g4 = Group(root, "Miscellaneous improvements");
        Check(g4, "t16", "T-16 Skyhopper as a selectable craft",
            "The T-16 from Beggar's Canyon becomes selectable on every mission that allows the X-wing (not the " +
            "airspeeder-only missions; with the mission 7 option below it's offered there too). It gets its own bay in the hangar, between the V-wing and the Y-wing, with its " +
            "own launch.\r\n\r\n" +
            "In flight: X-wing laser sound and fire rate (10 shots/s), 6 proton torpedoes like the X-wing, and the " +
            "X-wing's target lock. Its lasers and dumbfire torpedoes are aimed 7.5 deg below the nose line so they land " +
            "on the crosshair (the T-16 model is much bigger than the others, so its crosshair sits low).\r\n\r\n" +
            "Also fixes two bugs in the game's own T-16 code that only show up outside Beggar's Canyon " +
            "(memory freed in the wrong order, and a control block too small for the targeting data).\r\n\r\n" +
            "Adds a new code section to the exe. Works with or without the options above.\r\n\r\n" +
            "Status: tested in full missions (hangar launch, combat, end cutscene) together with our tester's " +
            "other flight mods. With the installer's own option sets it is byte-checked but not yet flown.");
        Check(g4, "mission7", "Any craft on Imperial Construction Yards (mission 7)",
            "Mission 7 is airspeeder-only because it has AT-ATs, but you don't have to bring one down to win.\r\n\r\n" +
            "Lets you pick the X-wing there, plus the A-wing, V-wing, Falcon and TIE Interceptor once you've unlocked them, the " +
            "same as a normal X-wing mission, and the T-16 if that option is installed. The airspeeder stays the default " +
            "in the hangar. Corellia, Escape from Fest and the Battle of Hoth stay airspeeder-only.\r\n\r\n" +
            "Status: tested by our tester (the T-16 on this mission is new, not yet flown).");
        Check(g4, "repair", "Every craft repairs itself",
            "In the stock game only the craft with an astromech droid or a crew slowly repair damage: the X-wing, " +
            "Y-wing, Naboo starfighter and Millennium Falcon (full health in 3 minutes).\r\n\r\n" +
            "Gives the same repair to the A-wing, V-wing, airspeeder, TIE Interceptor and T-16. Like the X-wing " +
            "losing its R2 unit, these craft stop repairing for the rest of that life once their health drops below " +
            "a quarter (there's no droid speech, as there's no droid). The Falcon keeps repairing as in the stock game.\r\n\r\n" +
            "Status: repair tested by our tester; the below-a-quarter cut-off is new, not yet flown.");

        // info box
        info.Multiline = true; info.ReadOnly = true; info.ScrollBars = ScrollBars.Vertical;
        info.Size = new Size(640, 150); info.BackColor = SystemColors.Info;
        info.Text = "Point at an option to see what it does.";
        root.Controls.Add(info);

        var bl = new FlowLayoutPanel { AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false, Margin = new Padding(0, 8, 0, 0) };
        install.Text = "Install selected"; install.AutoSize = true;
        install.Click += (s, e) => DoInstall();
        restore.Text = "Restore original exe"; restore.AutoSize = true;
        restore.Click += (s, e) => DoRestore();
        var close = new Button { Text = "Close", AutoSize = true };
        close.Click += (s, e) => Close();
        bl.Controls.AddRange(new Control[] { install, restore, close });
        root.Controls.Add(bl);

        foreach (var key in new[] { "convergence", "rlflight" })
            ((CheckBox)Opt(key).Box).CheckedChanged += (s, e) => UpdateEnabled();
        ((CheckBox)Opt("widescreen").Box).CheckedChanged += (s, e) => UpdateEnabled();

        string here = AppDomain.CurrentDomain.BaseDirectory;
        if (File.Exists(Path.Combine(here, ExeName))) folder.Text = here.TrimEnd('\\');
#if GOG
        else if (File.Exists(Path.Combine(here, "ROGUE", ExeName))) folder.Text = Path.Combine(here, "ROGUE");
#endif
        LoadFolder();
    }

    GroupBox Group(Control parent, string title) {
        var g = new GroupBox { Text = title, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, Width = 640, MinimumSize = new Size(640, 0), Padding = new Padding(8, 4, 8, 6) };
        var p = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false, Location = new Point(8, 20) };
        g.Controls.Add(p);
        parent.Controls.Add(g);
        return g;
    }
    Control Panel(Control g) { return g is GroupBox ? g.Controls[0] : g; }

    void Hook(Option o) {
        o.Box.MouseEnter += (s, e) => info.Text = o.Title + "\r\n\r\n" + o.Info;
        o.Box.GotFocus += (s, e) => info.Text = o.Title + "\r\n\r\n" + o.Info;
        options.Add(o);
    }
    void Check(Control g, string key, string title, string text) {
        var c = new CheckBox { Text = title, AutoSize = true };
        Panel(g).Controls.Add(c);
        Hook(new Option { Key = key, Title = title, Info = text, Box = c });
    }
    void UpdateEnabled() {
        bool ok = baseExe != null;
        // RL flight lives in the convergence section; convergence drives the aim-assist finder
        if (On("rlflight")) Set("convergence", true);
        if (On("convergence")) Set("aimassist", false);
        Opt("convergence").Box.Enabled = ok && !On("rlflight");
        Opt("aimassist").Box.Enabled = ok && !On("convergence");
        rlButton.Enabled = ok && On("rlflight");
        res.Enabled = On("widescreen") && ok;
    }

    // RL flight with any tight-turn button is the same patch: compare with the tested mask (button 9)
    static bool RlIsIn(byte[] exe, out int button) {
        button = 9;
        int o = PatchData.RlButtonOffset;
        if (exe.Length < o + 4) return false;
        uint mask = BitConverter.ToUInt32(exe, o);
        for (int i = 0; i < 32; i++) if (mask == 1u << i) button = i + 1;
        var norm = (byte[])exe.Clone();
        Buffer.BlockCopy(BitConverter.GetBytes(1 << 8), 0, norm, o, 4);
        return PatchFor("rlflight").IsIn(norm);
    }

    static string Md5(byte[] b) {
        using (var m = MD5.Create()) return BitConverter.ToString(m.ComputeHash(b)).Replace("-", "").ToLowerInvariant();
    }
    static Patch PatchFor(string key) { return PatchData.Groups.First(p => p.Key == key); }

    void LoadFolder() {
        baseExe = null;
        string dir = folder.Text.Trim().Trim('"');
#if GOG
        // GOG installs the game in a ROGUE subfolder of the folder you pick in GOG Galaxy / the setup
        if (dir.Length > 0 && !File.Exists(Path.Combine(dir, ExeName)) && File.Exists(Path.Combine(dir, "ROGUE", ExeName)))
            folder.Text = dir = Path.Combine(dir, "ROGUE");
#endif
        string exe = Path.Combine(dir, ExeName), bak = Path.Combine(dir, BackupName);
        install.Enabled = restore.Enabled = false;
        foreach (var o in options) o.Box.Enabled = false;
        res.Enabled = false;
        if (dir.Length == 0 || !File.Exists(exe)) {
            status.ForeColor = Color.DarkRed;
            status.Text = dir.Length == 0 ? "Choose the folder where Rogue Squadron is installed."
                                          : "\"" + ExeName + "\" was not found in that folder.";
            return;
        }
        byte[] cur;
        try { cur = File.ReadAllBytes(exe); }
        catch (Exception ex) { status.ForeColor = Color.DarkRed; status.Text = "Can't read the exe: " + ex.Message; return; }

#if STEAM
        string md5 = Md5(cur);
        if (md5 == SteamUnpackedMd5) {
            baseExe = cur;
            status.ForeColor = Color.DarkGreen;
            status.Text = "Found the Steam exe, unwrapped with Steamless. It will be backed up as \"" + BackupName + "\" before patching.";
        } else if (File.Exists(bak) && Md5(File.ReadAllBytes(bak)) == SteamUnpackedMd5) {
            baseExe = File.ReadAllBytes(bak);
            status.ForeColor = Color.DarkGreen;
            status.Text = "The exe is already modified. The installer will rebuild it from your backup \"" + BackupName + "\". The ticked options show what's installed now.";
        } else if (md5 == SteamPackedMd5) {
            status.ForeColor = Color.DarkRed;
            status.Text = "This is the Steam exe, still wrapped in Steam's DRM. Run Steamless on \"" + ExeName +
                          "\" and replace the exe with the \"" + ExeName + ".unpacked.exe\" it makes (see README), then try again.";
            return;
        } else if (File.Exists(bak) && Md5(File.ReadAllBytes(bak)) == SteamPackedMd5) {
            status.ForeColor = Color.DarkRed;
            status.Text = "The exe is modified, but the backup \"" + BackupName + "\" is Steam's wrapped exe, so there's nothing to rebuild from. " +
                          "Run Steamless on \"" + BackupName + "\" and rename the \".unpacked.exe\" it makes to \"" + BackupName +
                          "\" (replacing it), or use Verify integrity of game files in Steam and start again.";
            return;
        } else {
            status.ForeColor = Color.DarkRed;
            status.Text = "This isn't the Steam exe unwrapped with Steamless (MD5 " + SteamUnpackedMd5.ToUpper() +
                          "), and there's no matching \"" + BackupName + "\". For the CD or GOG version, use that version's installer.";
            return;
        }
#elif GOG
        if (Md5(cur) == GogMd5) {
            baseExe = cur;
            status.ForeColor = Color.DarkGreen;
            status.Text = "Found the GOG exe. It will be backed up as \"" + BackupName + "\" before patching.";
        } else if (File.Exists(bak) && Md5(File.ReadAllBytes(bak)) == GogMd5) {
            baseExe = File.ReadAllBytes(bak);
            status.ForeColor = Color.DarkGreen;
            status.Text = "The exe is already modified. The installer will rebuild it from your backup \"" + BackupName + "\". The ticked options show what's installed now.";
        } else {
            status.ForeColor = Color.DarkRed;
            status.Text = "This isn't the GOG version's exe (MD5 " + GogMd5.ToUpper() + "), and there's no matching \"" + BackupName +
                          "\". For the CD or Steam version, use that version's installer.";
            return;
        }
#else
        if (Md5(cur) == PatchData.OriginalMd5) {
            baseExe = cur;
            status.ForeColor = Color.DarkGreen;
            status.Text = "Found the original Rogue Squadron v1.2 exe. It will be backed up as \"" + BackupName + "\" before patching.";
        } else if (File.Exists(bak) && Md5(File.ReadAllBytes(bak)) == PatchData.OriginalMd5) {
            baseExe = File.ReadAllBytes(bak);
            status.ForeColor = Color.DarkGreen;
            status.Text = "The exe is already modified. The installer will rebuild it from your backup \"" + BackupName + "\". The ticked options show what's installed now.";
        } else {
            status.ForeColor = Color.DarkRed;
            status.Text = "This exe isn't the unmodified Rogue Squadron 3D v1.2 (US) exe (MD5 " + PatchData.OriginalMd5.ToUpper() +
                          "), and there's no matching \"" + BackupName + "\". Install the 1.2 update or restore the original exe, then try again. " +
                          "For the Steam or GOG version, use that version's installer.";
            return;
        }
#endif
        foreach (var o in options) o.Box.Enabled = true;
        install.Enabled = true;
        restore.Enabled = !ReferenceEquals(baseExe, cur);

        // reflect what is installed now (defaults for a clean exe)
        bool clean = ReferenceEquals(baseExe, cur);
        foreach (var k in new[] { "deadzone", "aimassist", "linear", "smallmoves", "widescreen", "ceiling" })
            Set(k, clean || PatchFor(k).IsIn(cur));
        Set("convergence", !clean && PatchFor("convergence").IsIn(cur));
        int button = 9;
        Set("rlflight", !clean && RlIsIn(cur, out button));
        rlButton.SelectedIndex = Math.Min(Math.Max(button, 1), 16) - 1;
        Set("lasers", !clean && PatchFor("lasers").IsIn(cur));
        Set("t16", !clean && (PatchFor("t16").IsIn(cur) || PatchFor("t16x").IsIn(cur)));
        Set("mission7", !clean && PatchFor("mission7").IsIn(cur));
        Set("repair", !clean && PatchFor("repair").IsIn(cur));
        if (!clean && PatchFor("widescreen").IsIn(cur)) {
            int w = BitConverter.ToInt32(cur, PatchData.ResolutionOffset), h = BitConverter.ToInt32(cur, PatchData.ResolutionOffset + 4);
            for (int i = 0; i < Resolutions.Length; i++) if (Resolutions[i][0] == w && Resolutions[i][1] == h) res.SelectedIndex = i;
        }
        UpdateEnabled();
    }

    byte[] Build(List<string> applied) {
        var keys = new List<string>();
        // convergence before rlflight: RL flight's code goes into the section convergence adds
        foreach (var k in new[] { "deadzone", "aimassist", "linear", "widescreen", "ceiling", "smallmoves", "convergence", "rlflight", "lasers", "mission7", "repair" })
            if (On(k)) keys.Add(k);
        if (keys.Contains("rlflight") && !keys.Contains("convergence")) throw new InvalidOperationException("Rogue Leader flight needs laser convergence.");
        if (keys.Contains("convergence")) keys.Remove("aimassist");

        int len = Math.Max(baseExe.Length, keys.Select(k => PatchFor(k).End).DefaultIfEmpty(0).Max());
        var img = new byte[len];
        Buffer.BlockCopy(baseExe, 0, img, 0, baseExe.Length);
        foreach (var k in keys) {
            foreach (var r in PatchFor(k).Runs) {
                for (int i = 0; i < r.Old.Length; i++)
                    if (img[r.Offset + i] != r.Old[i]) throw new InvalidOperationException("Unexpected bytes at 0x" + r.Offset.ToString("X") + " for " + k);
                Buffer.BlockCopy(r.New, 0, img, r.Offset, r.New.Length);
            }
            applied.Add(Opt(k).Title + (k == "rlflight" ? " (tight turn on joystick button " + (rlButton.SelectedIndex + 1) + ")" : ""));
        }
        if (keys.Contains("rlflight"))
            Buffer.BlockCopy(BitConverter.GetBytes(1 << rlButton.SelectedIndex), 0, img, PatchData.RlButtonOffset, 4);
        if (On("t16")) { img = AddT16(img); applied.Add(Opt("t16").Title); }
        if (keys.Contains("widescreen")) {
            var r = Resolutions[res.SelectedIndex];
            Buffer.BlockCopy(BitConverter.GetBytes(r[0]), 0, img, PatchData.ResolutionOffset, 4);
            Buffer.BlockCopy(BitConverter.GetBytes(r[1]), 0, img, PatchData.ResolutionOffset + 4, 4);
            applied.Add("Video menu: 1280 x 1024 replaced by " + r[0] + " x " + r[1]);
        }
        return img;
    }

    // Appends the ".t16" section after the exe's last section (RVA 0x3FF000 on its own, 0x400000
    // after the .conv section of the laser convergence option) and applies the runs built for that RVA.
    static byte[] AddT16(byte[] img) {
        int pe = BitConverter.ToInt32(img, 0x3C);
        int n = BitConverter.ToUInt16(img, pe + 6);
        int tab = pe + 24 + BitConverter.ToUInt16(img, pe + 20);
        int last = tab + (n - 1) * 40;
        int vs = BitConverter.ToInt32(img, last + 8), va = BitConverter.ToInt32(img, last + 12), rs = BitConverter.ToInt32(img, last + 16);
        int rva = (va + Math.Max(vs, rs) + 0xFFF) & ~0xFFF;
        Patch p; byte[] sec;
        if (rva == 0x3FF000) { p = PatchFor("t16"); sec = PatchData.T16Section_3FF000; }
        else if (rva == 0x400000) { p = PatchFor("t16x"); sec = PatchData.T16Section_400000; }
        else throw new InvalidOperationException("Unexpected section layout for the T-16 (next RVA 0x" + rva.ToString("X") + ")");
        int size = PatchData.T16SectionSize, h = tab + n * 40;
        for (int i = 0; i < 40; i++) if (img[h + i] != 0) throw new InvalidOperationException("No free section header for the T-16");
        var outp = new byte[img.Length + size];
        Buffer.BlockCopy(img, 0, outp, 0, img.Length);
        var name = new byte[] { (byte)'.', (byte)'t', (byte)'1', (byte)'6', 0, 0, 0, 0 };
        Buffer.BlockCopy(name, 0, outp, h, 8);
        Buffer.BlockCopy(BitConverter.GetBytes(size), 0, outp, h + 8, 4);          // VirtualSize
        Buffer.BlockCopy(BitConverter.GetBytes(rva), 0, outp, h + 12, 4);          // VirtualAddress
        Buffer.BlockCopy(BitConverter.GetBytes(size), 0, outp, h + 16, 4);         // SizeOfRawData
        Buffer.BlockCopy(BitConverter.GetBytes(img.Length), 0, outp, h + 20, 4);   // PointerToRawData
        Buffer.BlockCopy(BitConverter.GetBytes(unchecked((int)0xE0000020)), 0, outp, h + 36, 4);
        Buffer.BlockCopy(BitConverter.GetBytes((ushort)(n + 1)), 0, outp, pe + 6, 2);
        Buffer.BlockCopy(BitConverter.GetBytes(rva + size), 0, outp, pe + 0x50, 4); // SizeOfImage
        foreach (var r in p.Runs) {
            for (int i = 0; i < r.Old.Length; i++)
                if (outp[r.Offset + i] != r.Old[i]) throw new InvalidOperationException("Unexpected bytes at 0x" + r.Offset.ToString("X") + " for the T-16");
            Buffer.BlockCopy(r.New, 0, outp, r.Offset, r.New.Length);
        }
        Buffer.BlockCopy(sec, 0, outp, img.Length, size);
        return outp;
    }

    const string BundleName = "Bundle.002", BundleBackup = "Bundle.002.original";

    // The convergence option's in-game toggle lives in Bundle.002 (BundleMenu.cs). Adds it when
    // wanted, otherwise puts the backed-up file back. Problems here never stop the exe install:
    // without the toggle convergence simply stays on.
    static string ApplyMenu(string dir, bool want) {
        string b = Path.Combine(dir, BundleName), bb = Path.Combine(dir, BundleBackup);
        try {
            if (!File.Exists(b)) return want ? "\"" + BundleName + "\" wasn't found, so the in-game convergence toggle wasn't added (convergence is always on)." : "";
            byte[] cur = File.ReadAllBytes(b);
            bool patched = BundleMenu.IsPatched(cur);
            if (!want) {
                if (patched && File.Exists(bb) && !BundleMenu.IsPatched(File.ReadAllBytes(bb))) {
                    File.Copy(bb, b, true);
                    return "\"" + BundleName + "\" was restored from \"" + BundleBackup + "\".";
                }
                return "";
            }
            if (patched) return "";
            if (!File.Exists(bb)) File.WriteAllBytes(bb, cur);
            File.WriteAllBytes(b, BundleMenu.Patch(cur));
            return "\"Enable Laser Convergence\" was added to Options > General Settings (\"" + BundleName + "\" backed up as \"" + BundleBackup + "\").";
        } catch (Exception ex) {
            return want ? "The in-game convergence toggle couldn't be added (" + ex.Message + "), so convergence is always on." : "";
        }
    }

    void WriteExe(byte[] img, string done, bool menu) {
        string dir = folder.Text.Trim().Trim('"');
        string exe = Path.Combine(dir, ExeName), bak = Path.Combine(dir, BackupName);
        try {
            // a file already using the backup name that isn't the base exe (e.g. Steam's wrapped exe
            // renamed by hand) is moved aside, never trusted or overwritten
            if (File.Exists(bak) && Md5(File.ReadAllBytes(bak)) != Md5(baseExe)) {
                string old = Path.Combine(dir, "Rogue Squadron.original-old.EXE");
                for (int i = 2; File.Exists(old); i++) old = Path.Combine(dir, "Rogue Squadron.original-old" + i + ".EXE");
                File.Move(bak, old);
                done += "\r\n\r\nThe file that was already called \"" + BackupName + "\" wasn't the original exe, so it was renamed to \"" +
                        Path.GetFileName(old) + "\".";
            }
            if (!File.Exists(bak)) File.WriteAllBytes(bak, baseExe);
            File.WriteAllBytes(exe + ".tmp", img);
            File.Copy(exe + ".tmp", exe, true);
            File.Delete(exe + ".tmp");
        } catch (IOException ex) {
            try { File.Delete(exe + ".tmp"); } catch { }
            MessageBox.Show(this, "Couldn't write the exe. Close Rogue Squadron if it's running and try again.\r\n\r\n" + ex.Message,
                Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        } catch (UnauthorizedAccessException ex) {
            MessageBox.Show(this, "Windows denied access to the game folder. Right-click the installer and choose \"Run as administrator\".\r\n\r\n" + ex.Message,
                Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        string m = ApplyMenu(dir, menu);
        if (m.Length > 0) done += "\r\n\r\n" + m;
        MessageBox.Show(this, done, Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
        LoadFolder();
    }

    void DoInstall() {
        if (baseExe == null) return;
        var applied = new List<string>();
        byte[] img;
        try { img = Build(applied); }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
        string msg = applied.Count == 0 ? "No options were selected, so the exe is now the original."
                                        : "Installed:\r\n  - " + string.Join("\r\n  - ", applied);
        if (On("widescreen")) msg += "\r\n\r\nIn the game, open Options > Video and select the widescreen resolution.";
        msg += "\r\n\r\nYour untouched exe is saved as \"" + BackupName + "\".";
        WriteExe(img, msg, On("convergence"));
    }

    void DoRestore() {
        if (baseExe == null) return;
        if (MessageBox.Show(this, "Put the original, unmodified exe back?", Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        WriteExe(baseExe, "The original exe has been restored. Every mod is removed.", false);
    }

    [STAThread]
    static void Main() {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new InstallerForm());
    }
}
