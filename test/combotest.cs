// 2026-11-25: random option sets on the CD, Steam and GOG installers (reflection, nothing written by the
// installers). Checks: every set builds; Steam/GOG output == CD output apart from their known bytes;
// the CD output read back by LoadFolder ticks exactly the options that were built.
// Usage: combotest <cd inst> <cd dir> <steam inst> <steam dir> <gog inst> <gog dir> <scratch dir> [count]
using System; using System.IO; using System.Reflection; using System.Windows.Forms; using System.Collections.Generic; using System.Linq;
class T {
  static BindingFlags BF = BindingFlags.NonPublic | BindingFlags.Instance;
  static Form Load(string asmPath, string dir, out Type ty) {
    ty = Assembly.LoadFrom(asmPath).GetType("InstallerForm");
    var f = (Form)Activator.CreateInstance(ty, true);
    ((TextBox)ty.GetField("folder", BF).GetValue(f)).Text = dir;
    ty.GetMethod("LoadFolder", BF).Invoke(f, null);
    Console.WriteLine(((Label)ty.GetField("status", BF).GetValue(f)).Text);
    return f;
  }
  static bool Get(Form f, Type ty, string k) { return (bool)ty.GetMethod("On", BF).Invoke(f, new object[] { k }); }
  static byte[] Build(Form f, Type ty, Dictionary<string, bool> set, int rl) {
    foreach (var kv in set) ty.GetMethod("Set", BF).Invoke(f, new object[] { kv.Key, kv.Value });
    ty.GetMethod("UpdateEnabled", BF).Invoke(f, null);
    ((ComboBox)ty.GetField("rlButton", BF).GetValue(f)).SelectedIndex = rl;
    return (byte[])ty.GetMethod("Build", BF).Invoke(f, new object[] { new List<string>() });
  }
  static void Main(string[] a) {
    Type tc, ts, tg;
    var fc = Load(a[0], a[1], out tc); var fs = Load(a[2], a[3], out ts); var fg = Load(a[4], a[5], out tg);
    string scratch = a[6]; int count = a.Length > 7 ? int.Parse(a[7]) : 300;
    byte[] orig = File.ReadAllBytes(Path.Combine(a[1], "Rogue Squadron.EXE"));
    Directory.CreateDirectory(scratch);
    File.WriteAllBytes(Path.Combine(scratch, "Rogue Squadron.original.EXE"), orig);
    string[] keys = { "deadzone", "aimassist", "convergence", "rlflight", "lasers", "linear", "smallmoves", "ceiling", "widescreen",
                      "t16", "anycraft", "kessel", "nonah", "bios", "failselect", "repair", "gunsight", "hudnumbers", "onelife", "falconaim" };
    var rnd = new Random(7);
    int bad = 0, n = 0;
    for (int c = 0; c < count; c++) {
      var set = keys.ToDictionary(k => k, k => c == 0 ? true : c == 1 ? false : rnd.Next(2) == 1);
      int rl = rnd.Next(16);
      byte[] x, y, z;
      try { x = Build(fc, tc, set, rl); y = Build(fs, ts, set, rl); z = Build(fg, tg, set, rl); }
      catch (Exception ex) { bad++; Console.WriteLine("combo " + c + " build failed: " + (ex.InnerException ?? ex).Message); continue; }
      n++;
      // what the CD form actually built (UpdateEnabled may have changed the set)
      var eff = keys.ToDictionary(k => k, k => Get(fc, tc, k));
      if (eff["convergence"]) eff["aimassist"] = false;
      foreach (var pair in new[] { Tuple.Create("Steam", y, true), Tuple.Create("GOG", z, false) }) {
        var o = pair.Item2;
        if (o.Length != x.Length) { bad++; Console.WriteLine("combo " + c + " " + pair.Item1 + ": length differs"); continue; }
        var d = Enumerable.Range(0, x.Length).Where(i => x[i] != o[i]).ToList();
        bool ok = d.All(i => i == 0xEB87E || (pair.Item3 && i >= 0x40 && i < 0xD0)) && d.Contains(0xEB87E);
        if (!ok) { bad++; Console.WriteLine("combo " + c + " " + pair.Item1 + ": " + d.Count + " unexpected diffs, first 0x" + d.First(i => i != 0xEB87E).ToString("X")); }
      }
      // read back
      File.WriteAllBytes(Path.Combine(scratch, "Rogue Squadron.EXE"), x);
      Type tr; var fr = Load2(a[0], scratch, out tr);
      var wrong = keys.Where(k => Get(fr, tr, k) != eff[k]).ToList();
      int rb = ((ComboBox)tr.GetField("rlButton", BF).GetValue(fr)).SelectedIndex;
      if (wrong.Count > 0 || (eff["rlflight"] && rb != rl)) { bad++; Console.WriteLine("combo " + c + " readback wrong: " + string.Join(",", wrong.Select(k => k + "=" + Get(fr, tr, k))) + (eff["rlflight"] && rb != rl ? " rlbutton" : "")); }
      fr.Dispose();
    }
    Console.WriteLine(n + " combos built, " + bad + " problems");
  }
  static Assembly cdAsm;
  static Form Load2(string asmPath, string dir, out Type ty) {
    if (cdAsm == null) cdAsm = Assembly.LoadFrom(asmPath);
    ty = cdAsm.GetType("InstallerForm");
    var f = (Form)Activator.CreateInstance(ty, true);
    ((TextBox)ty.GetField("folder", BF).GetValue(f)).Text = dir;
    ty.GetMethod("LoadFolder", BF).Invoke(f, null);
    return f;
  }
}
