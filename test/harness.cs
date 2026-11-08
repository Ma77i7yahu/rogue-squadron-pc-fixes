using System; using System.Reflection; using System.Windows.Forms; using System.Collections;
class H { static void Main(string[] a) {
  var asm = Assembly.LoadFrom(a[0]); var ty = asm.GetType("InstallerForm");
  var f = (Form)Activator.CreateInstance(ty, true);
  var BF = BindingFlags.NonPublic | BindingFlags.Instance;
  ((TextBox)ty.GetField("folder", BF).GetValue(f)).Text = a[1];
  ty.GetMethod("LoadFolder", BF).Invoke(f, null);
  Console.WriteLine(((Label)ty.GetField("status", BF).GetValue(f)).Text);
  foreach (var o in (IEnumerable)ty.GetField("options", BF).GetValue(f)) {
    var ot = o.GetType(); var cb = (CheckBox)ot.GetField("Box").GetValue(o);
    Console.WriteLine("  {0,-62} {1}{2}", ot.GetField("Title").GetValue(o), cb.Checked ? "ON " : "off", cb.Enabled ? "" : " (disabled)"); }
  Console.WriteLine("  RL button: " + ((ComboBox)ty.GetField("rlButton", BF).GetValue(f)).SelectedItem);
} }
