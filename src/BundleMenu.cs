// Adds the "Enable Laser Convergence" checkbox to the General Settings screen (C# port of
// build_menu.py). GENERAL_P.SLB inside Bundle.002 is a plain-text Sweet view (objects + C-like
// script); the checkbox reads/writes GENERAL option 5 of the settings store, which the
// convergence exe patch adds. Every edit must match exactly once, otherwise nothing is changed.
using System;
using System.Collections.Generic;
using System.Text;

static class BundleMenu {
    const int HD = 0x10, ENT = 0x10032, ESZ = 0xFC, N = 10;
    static readonly Encoding Latin1 = Encoding.GetEncoding(28591);
    const string Marker = "Enable Laser Convergence";

    static int BE(byte[] b, int o) { return b[o] << 24 | b[o + 1] << 16 | b[o + 2] << 8 | b[o + 3]; }
    static void PutBE(byte[] b, int o, int v) { b[o] = (byte)(v >> 24); b[o + 1] = (byte)(v >> 16); b[o + 2] = (byte)(v >> 8); b[o + 3] = (byte)v; }

    // finds GENERAL_P.SLB: entry index, data start (BNDT payload), size, offset
    static void Locate(byte[] b, out int k, out int dt, out int sz, out int off) {
        if (b.Length < ENT + N * ESZ || Latin1.GetString(b, 0, 4) != "BUND" || Latin1.GetString(b, 8, 4) != "BNHD")
            throw new FormatException("not a BUND file");
        int tag = HD + BE(b, 12);
        if (Latin1.GetString(b, tag, 4) != "BNDT") throw new FormatException("no BNDT block");
        dt = tag + 8;
        for (k = 0; k < N; k++) {
            int e = ENT + k * ESZ, n = 0;
            while (n < 0xC8 && b[e + n] != 0) n++;
            var raw = new byte[n];
            for (int i = 0; i < n; i++) raw[i] = (byte)(b[e + i] ^ 0xAA);
            if (Latin1.GetString(raw).Contains("\\GENERAL_P.SLB")) {
                sz = BitConverter.ToInt32(b, e + 0xC8); off = BitConverter.ToInt32(b, e + 0xCC);
                return;
            }
        }
        throw new FormatException("GENERAL_P.SLB not found");
    }

    public static bool IsPatched(byte[] b) {
        int k, dt, sz, off;
        Locate(b, out k, out dt, out sz, out off);
        return Latin1.GetString(b, dt + off, sz).Contains(Marker);
    }

    public static byte[] Patch(byte[] b) {
        int K, DT, sz, off;
        Locate(b, out K, out DT, out sz, out off);
        string t = Latin1.GetString(b, DT + off, sz);
        if (t.Contains(Marker)) throw new InvalidOperationException("already patched");

        Func<string, string> block = start => {
            int i = t.IndexOf("\t\tOBJECT " + start + "\r\n", StringComparison.Ordinal);
            if (i < 0) throw new FormatException("object " + start + " not found");
            int j = t.IndexOf("\t\tOBJECT ", i + 10, StringComparison.Ordinal);
            return t.Substring(i, j - i);
        };
        Action<string, string> rep = (o, n) => {
            int c = 0;
            for (int i = t.IndexOf(o, StringComparison.Ordinal); i >= 0; i = t.IndexOf(o, i + o.Length, StringComparison.Ordinal)) c++;
            if (c != 1) throw new FormatException("expected text found " + c + " times: " + o.Trim());
            t = t.Replace(o, n);
        };

        // four new objects, cloned from the Crosshairs row (y 279 -> 309)
        var rows = new StringBuilder();
        foreach (var p in new[] { new[] { "x5", "x8" }, new[] { "5", "8" }, new[] { "x5-x", "x8-x" }, new[] { "generalbox_5", "generalbox_8" } }) {
            string nm = p[0], blk = block(nm);
            string head = "\t\tOBJECT " + nm + "\r\n";
            blk = "\t\tOBJECT " + p[1] + "\r\n" + blk.Substring(head.Length);
            var lines = blk.Split(new[] { "\r\n" }, StringSplitOptions.None);
            var f = lines[2].Split((char[])null, StringSplitOptions.RemoveEmptyEntries);   // x y w h
            if (f[1] != "279") throw new FormatException("unexpected position of " + nm);
            f[1] = "309";
            if (nm == "5") f[2] = "180";             // wider label for the longer text
            if (nm == "generalbox_5") f[2] = "210";  // clickable area covers it
            lines[2] = lines[2].Substring(0, lines[2].Length - lines[2].TrimStart().Length) + string.Join(" ", f);
            blk = string.Join("\r\n", lines);
            if (nm == "5") blk = blk.Replace("Enable Crosshairs", Marker);
            if (nm == "generalbox_5") blk = blk.Replace("flip_check_box(\"x5\",IMMORTAL_CROSSHAIR);", "flip_convergence();");
            rows.Append(blk);
        }
        const string anchor = "\t\tOBJECT x6-x\r\n";
        rep(anchor, rows + anchor);
        rep("OBJLIST 63\r\n", "OBJLIST 67\r\n");

        // script
        rep("long entering_passcode = FALSE;\r\n",
            "long entering_passcode = FALSE;\r\n" +
            "long conv_setting = 1;  // Laser Convergence (GENERAL option 5, added by mod)\r\n");
        rep("long NUM_NAV_BUTTONS = 20;", "long NUM_NAV_BUTTONS = 21;");
        rep("      \"generalbox_5\"\r\n   };", "      \"generalbox_5\",\r\n      \"generalbox_8\"\r\n   };");
        rep("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,0};",
            "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,0};");
        rep("long nav_move_1[4] = {19,2,10,0};", "long nav_move_1[4] = {20,2,10,0};");
        rep("long nav_move_2[4] = {19,3,15,1};", "long nav_move_2[4] = {20,3,15,1};");
        rep("long nav_move_3[4] = {19,4,15,2};", "long nav_move_3[4] = {20,4,15,2};");
        rep("long nav_move_9[4] = {8,14,4,19};", "long nav_move_9[4] = {8,14,4,20};");
        rep("long nav_move_19[4] = {18,9,2,14};// crosshairs\r\n",
            "long nav_move_19[4] = {18,9,20,14};// crosshairs\r\n" +
            "long nav_move_20[4] = {19,9,2,14};// laser convergence\r\n");
        rep("nav_move_15,nav_move_16,nav_move_17,nav_move_18,nav_move_19\r\n",
            "nav_move_15,nav_move_16,nav_move_17,nav_move_18,nav_move_19,\r\n      nav_move_20\r\n");
        rep("   set_check_box(\"x7\", generalData[OVERLAYS_ENABLED]);\r\n   \r\n   display_passcodes(0);",
            "   set_check_box(\"x7\", generalData[OVERLAYS_ENABLED]);\r\n" +
            "   GetGameData(GENERAL,5,0,0,&conv_setting);\r\n" +
            "   set_check_box(\"x8\", conv_setting);\r\n   \r\n   display_passcodes(0);");
        rep("      set_check_box(\"x7\", generalData[OVERLAYS_ENABLED]);\r\n   }else",
            "      set_check_box(\"x7\", generalData[OVERLAYS_ENABLED]);\r\n" +
            "      set_check_box(\"x8\", conv_setting);\r\n   }else");
        rep("   GetGameData(GET_DEFAULT,GENERAL,PASSCODE,0,0x0);\r\n   displayData();",
            "   GetGameData(GET_DEFAULT,GENERAL,PASSCODE,0,0x0);\r\n" +
            "   SetGameData(GENERAL,5,0,0,1);\r\n   displayData();");
        rep("// Toggles the state of a check box.\r\n",
            "// Toggles Laser Convergence (stored straight away in GENERAL option 5).\r\n" +
            "long flip_convergence()\r\n{\r\n" +
            "   conv_setting = !conv_setting;\r\n" +
            "   SetGameData(GENERAL,5,0,0,conv_setting);\r\n" +
            "   set_check_box(\"x8\",conv_setting);\r\n}\r\n\r\n" +
            "// Toggles the state of a check box.\r\n");

        // repack: replace the file's data, shift the entries after it, fix the block sizes
        byte[] nw = Latin1.GetBytes(t);
        int delta = nw.Length - sz, dataLen = b.Length - DT;
        var outp = new byte[b.Length + delta];
        Buffer.BlockCopy(b, 0, outp, 0, DT + off);
        Buffer.BlockCopy(nw, 0, outp, DT + off, nw.Length);
        Buffer.BlockCopy(b, DT + off + sz, outp, DT + off + nw.Length, b.Length - (DT + off + sz));
        for (int k = 0; k < N; k++) {
            int e = ENT + k * ESZ;
            int s = BitConverter.ToInt32(b, e + 0xC8), o = BitConverter.ToInt32(b, e + 0xCC);
            if (k == K) s = nw.Length; else if (o > off) o += delta;
            Buffer.BlockCopy(BitConverter.GetBytes(s), 0, outp, e + 0xC8, 4);
            Buffer.BlockCopy(BitConverter.GetBytes(o), 0, outp, e + 0xCC, 4);
        }
        PutBE(outp, DT - 4, dataLen + delta);
        PutBE(outp, 4, outp.Length - 8);
        return outp;
    }
}
