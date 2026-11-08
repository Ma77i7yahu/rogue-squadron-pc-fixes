Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text;
public static class W32 {
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr h);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, int m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern IntPtr FindWindow(string c, string t);
  public delegate bool EP(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, EP f, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
}
"@
$AE=[System.Windows.Automation.AutomationElement]; $TS=[System.Windows.Automation.TreeScope]
function Win($title){ for($i=0;$i -lt 40;$i++){ $w=$AE::RootElement.FindFirst($TS::Children,(New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty,$title))); if($w){return $w}; Start-Sleep -Milliseconds 250 }; throw "no window $title" }
function HandleOf($w,$name){ $e=$w.FindFirst($TS::Descendants,(New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty,$name))); if(-not $e){ throw "no element $name" }; [IntPtr]$e.Current.NativeWindowHandle }
function State($w,$name){ $h=HandleOf $w $name; $c=[int][W32]::SendMessage($h,0xF0,[IntPtr]::Zero,[IntPtr]::Zero); $(if($c -eq 1){'On'}else{'Off'}) + $(if([W32]::IsWindowEnabled($h)){''}else{' (disabled)'}) }
function SetBox($w,$name,$on){ $h=HandleOf $w $name; $c=[int][W32]::SendMessage($h,0xF0,[IntPtr]::Zero,[IntPtr]::Zero); if(($c -eq 1) -ne $on){ [W32]::SendMessage($h,0xF5,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null } }
function Click($w,$name){ $h=HandleOf $w $name; [W32]::PostMessage($h,0xF5,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null }
function Dialog($title){
  for($i=0;$i -lt 40;$i++){ $d=[W32]::FindWindow('#32770',$title); if($d -ne [IntPtr]::Zero){ break }; Start-Sleep -Milliseconds 250 }
  if($d -eq [IntPtr]::Zero){ return 'NO DIALOG' }
  $script:txt=@(); $script:ok=[IntPtr]::Zero
  [W32]::EnumChildWindows($d,{ param($h,$l) $sb=New-Object Text.StringBuilder 4096; [W32]::GetWindowText($h,$sb,4096)|Out-Null; $cb=New-Object Text.StringBuilder 64; [W32]::GetClassName($h,$cb,64)|Out-Null; if($cb.ToString() -eq 'Button' -and $sb.ToString() -eq 'OK'){ $script:ok=$h } elseif($sb.Length){ $script:txt+=$sb.ToString() }; $true },[IntPtr]::Zero) | Out-Null
  [W32]::SendMessage($script:ok,0xF5,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null
  ($script:txt -join ' | ') -replace "`r`n",' / '
}
