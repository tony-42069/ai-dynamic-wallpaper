$taskName = "Daily Wallpaper Update"
$taskPath = "\Wallpaper App\"
$scriptPath = "C:\Users\dsade\OneDrive\Desktop\Business\AI\Wallpaper App\update_wallpaper.bat"

# Create the task action
$action = New-ScheduledTaskAction -Execute $scriptPath

# Create triggers
# 1. At login
$triggerLogin = New-ScheduledTaskTrigger -AtLogOn

# 2. Daily at 9 AM (you can change this time)
$triggerDaily = New-ScheduledTaskTrigger -Daily -At 9am

# Combine triggers
$triggers = @($triggerLogin, $triggerDaily)

# Create the principal (run whether user is logged in or not)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Password -RunLevel Highest

# Create the settings
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

# Register the task
Register-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Force
