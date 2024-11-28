$taskName = "Daily Wallpaper Update"
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

# Create the principal (run in current user context)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

# Create the settings
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

# Unregister existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Force
