param([string]$act="shot",[int]$x=0,[int]$y=0,[string]$keys="",[int]$wait=900,[string]$crop="")
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
Add-Type @"
using System;using System.Runtime.InteropServices;
public class M{[DllImport("user32.dll")]public static extern bool SetCursorPos(int x,int y);
[DllImport("user32.dll")]public static extern void mouse_event(uint f,uint dx,uint dy,uint d,UIntPtr e);
[DllImport("user32.dll")]public static extern bool SetProcessDPIAware();}
"@
[M]::SetProcessDPIAware()|Out-Null
if($act -eq "click" -or $act -eq "dbl" -or $act -eq "move"){[M]::SetCursorPos($x,$y)|Out-Null;Start-Sleep -Milliseconds 150
 if($act -ne "move"){[M]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[M]::mouse_event(4,0,0,0,[UIntPtr]::Zero)}
 if($act -eq "dbl"){Start-Sleep -Milliseconds 80;[M]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[M]::mouse_event(4,0,0,0,[UIntPtr]::Zero)}}
if($act -eq "wheel"){[M]::SetCursorPos($x,$y)|Out-Null;[M]::mouse_event(1,0,1,0,[UIntPtr]::Zero);1..40|%{[M]::mouse_event(0x800,0,0,[uint32]4294966576,[UIntPtr]::Zero);Start-Sleep -Milliseconds 40}}
if($act -eq "hover"){[M]::SetCursorPos($x,$y)|Out-Null;1..60|%{[M]::mouse_event(1,0,1,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 50;[M]::mouse_event(1,0,[uint32]4294967295,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 50}}
if($act -eq "rclick"){[M]::SetCursorPos($x,$y)|Out-Null;Start-Sleep -Milliseconds 150;[M]::mouse_event(8,0,0,0,[UIntPtr]::Zero);[M]::mouse_event(16,0,0,0,[UIntPtr]::Zero)}
if($act -eq "keys"){[System.Windows.Forms.SendKeys]::SendWait($keys)}
Start-Sleep -Milliseconds $wait
$b=[System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;$g=[System.Drawing.Graphics]::FromImage($bmp);$g.CopyFromScreen($b.Left,$b.Top,0,0,$bmp.Size)
$out=Join-Path $PSScriptRoot "s.png"
if($crop){$c=$crop.Split(",")|%{[int]$_};$r=New-Object System.Drawing.Rectangle $c[0],$c[1],$c[2],$c[3];$bmp=$bmp.Clone($r,$bmp.PixelFormat)}
$bmp.Save($out);"$($b.Width)x$($b.Height)"
