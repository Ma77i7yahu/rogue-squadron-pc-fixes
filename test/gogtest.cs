// Builds option sets with the CD and GOG installers (via reflection, nothing written to disk)
// and checks the GOG output equals the CD output apart from GOG's no-CD byte at file 0xEB87E.
// Usage: gogtest <cd installer> <cd folder> <gog installer> <gog folder>
using System; using System.Reflection; using System.Windows.Forms; using System.Collections.Generic; using System.Linq;
class T {
  static BindingFlags BF = BindingFlags.NonPublic | BindingFlags.Instance;
  static Form Load(string asmPath, string dir, out Type ty) {
    ty = Assembly.LoadFrom(asmPath).GetType("InstallerForm");
    var f = (Form)Activator.CreateInstance(ty, true);
    ((TextBox)ty.GetField("folder", BF).GetValue(f)).Text = dir;
    ty.GetMethod("LoadFolder", BF).Invoke(f, null);
    Console.WriteLine("[" + ((TextBox)ty.GetField("folder", BF).GetValue(f)).Text + "] " + ((Label)ty.GetField("status", BF).GetValue(f)).Text);
    return f;
  }
  static byte[] Build(Form f, Type ty, Dictionary<string, bool> set, int rl) {
    foreach (var kv in set) ty.GetMethod("Set", BF).Invoke(f, new object[] { kv.Key, kv.Value });
    ty.GetMethod("UpdateEnabled", BF).Invoke(f, null);
    ((ComboBox)ty.GetField("rlButton", BF).GetValue(f)).SelectedIndex = rl;
    return (byte[])ty.GetMethod("Build", BF).Invoke(f, new object[] { new List<string>() });
  }
  static void Main(string[] a) {
    Type tc, tg;
    var fc = Load(a[0], a[1], out tc);
    var fg = Load(a[2], a[3], out tg);
    string[] keys = { "deadzone", "aimassist", "convergence", "rlflight", "lasers", "linear", "smallmoves", "ceiling", "widescreen", "t16", "mission7", "repair" };
    var rnd = new Random(1);
    int bad = 0, n = 0;
    for (int c = 0; c < 200; c++) {
      var set = keys.ToDictionary(k => k, k => c == 0 ? true : c == 1 ? false : rnd.Next(2) == 1);
      int rl = rnd.Next(16);
      byte[] x = Build(fc, tc, set, rl), y = Build(fg, tg, set, rl);
      n++;
      if (y.Length != x.Length) { bad++; Console.WriteLine("combo " + c + ": length differs"); continue; }
      var diffs = Enumerable.Range(0, x.Length).Where(i => x[i] != y[i]).ToList();
      if (!(diffs.Count == 1 && diffs[0] == 0xEB87E && x[0xEB87E] == 0xA0 && y[0xEB87E] == 0xA2)) {
        bad++; Console.WriteLine("combo " + c + ": " + diffs.Count + " diffs, first 0x" + (diffs.Count > 0 ? diffs[0].ToString("X") : "-"));
      }
    }
    Console.WriteLine(n + " combos, " + bad + " bad");
    foreach (var o in (System.Collections.IEnumerable)tg.GetField("options", BF).GetValue(fg)) {
      var ot = o.GetType(); var cb = (CheckBox)ot.GetField("Box").GetValue(o);
      if ((string)ot.GetField("Key").GetValue(o) == "noxp") Console.WriteLine("noxp box: " + (cb.Checked ? "ON" : "off") + (cb.Enabled ? "" : " (disabled)"));
    }
  }
}
