@echo off
echo Creating startup shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WallpaperUpdater.lnk'); $Shortcut.TargetPath = '%~dp0update_wallpaper.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"
echo Done! The wallpaper updater will now run automatically when you start your computer.
