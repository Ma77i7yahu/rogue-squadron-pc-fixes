// Detects the options in <folder>\Rogue Squadron.EXE with the given installer (reflection, nothing
// written), forces "t16" on, builds, and lists every byte that differs from <compare exe>.
// Usage: livediff <installer> <folder> <compare exe>
using System; using System.IO; using System.Reflection; using System.Windows.Forms; using System.Collections; using System.Collections.Generic; using System.Linq;
class L { static void Main(string[] a) {
  var BF = BindingFlags.NonPublic | BindingFlags.Instance;
  var ty = Assembly.LoadFrom(a[0]).GetType("InstallerForm");
  var f = (Form)Activator.CreateInstance(ty, true);
  ((TextBox)ty.GetField("folder", BF).GetValue(f)).Text = a[1];
  ty.GetMethod("LoadFolder", BF).Invoke(f, null);
  Console.WriteLine(((Label)ty.GetField("status", BF).GetValue(f)).Text);
  ty.GetMethod("Set", BF).Invoke(f, new object[] { "t16", true });
  if (a.Length > 3) foreach (var kv in a.Skip(3)) { var p = kv.Split('='); ty.GetMethod("Set", BF).Invoke(f, new object[] { p[0], p[1] == "1" }); }
  ty.GetMethod("UpdateEnabled", BF).Invoke(f, null);
  foreach (var o in (IEnumerable)ty.GetField("options", BF).GetValue(f)) {
    var ot = o.GetType(); var cb = (CheckBox)ot.GetField("Box").GetValue(o);
    Console.WriteLine("  {0,-14} {1}", ot.GetField("Key").GetValue(o), cb.Checked ? "ON" : "off"); }
  Console.WriteLine("  RL button: " + ((ComboBox)ty.GetField("rlButton", BF).GetValue(f)).SelectedItem);
  var x = (byte[])ty.GetMethod("Build", BF).Invoke(f, new object[] { new List<string>() });
  var y = File.ReadAllBytes(a[2]);
  Console.WriteLine("built " + x.Length + " vs " + y.Length);
  int n = Math.Min(x.Length, y.Length), cnt = 0;
  for (int i = 0; i < n; i++) if (x[i] != y[i]) {
    int j = i; while (j < n && x[j] != y[j]) j++;
    // merge runs closer than 4 bytes
    while (j < n) { int k = j; while (k < n && k < j + 4 && x[k] == y[k]) k++; if (k < n && k < j + 4) { j = k; while (j < n && x[j] != y[j]) j++; } else break; }
    Console.WriteLine("0x{0:X6} len {1,3}: inst {2} | live {3}", i, j - i, BitConverter.ToString(x, i, Math.Min(j - i, 24)), BitConverter.ToString(y, i, Math.Min(j - i, 24)));
    cnt++; i = j;
  }
  Console.WriteLine(cnt + " runs");
} }
