Option Explicit

If WScript.Arguments.Count < 1 Then
    WScript.Echo "usage: wscript run_powershell_hidden.vbs <script.ps1>"
    WScript.Quit 2
End If

Dim shell, scriptPath, command
scriptPath = WScript.Arguments(0)
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & scriptPath & """"

Set shell = CreateObject("WScript.Shell")
shell.Run command, 0, False

