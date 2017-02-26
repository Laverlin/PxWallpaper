rem ------ loosen permissions on a single folder in the path where the cached images are kept
takeown /F C:\ProgramData\Microsoft\Windows\SystemData 
icacls C:\ProgramData\Microsoft\Windows\SystemData /grant:r %UserName%:F
icacls C:\ProgramData\Microsoft\Windows\SystemData /grant:r Administrators:F
icacls C:\ProgramData\Microsoft\Windows\SystemData /setowner Administrators
pause

rem ------ loosen permissions on the sub-folders where the cached images are kept
takeown /F C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18 /R /D Y
rem icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18 /grant:r %UserName%:(OI)(CI)F
rem icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18 /grant:r Administrators:(OI)(CI)F
rem icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18 /grant:r SYSTEM:(OI)(CI)F
icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18\* /inheritance:e /T
icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18 /setowner Administrators /T
pause

takeown /F C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-21-1690007262-1860438432-1133890597-1001 /R /D Y
icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-21-1690007262-1860438432-1133890597-1001\* /inheritance:e /T
icacls C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-21-1690007262-1860438432-1133890597-1001 /setowner Administrators /T


rem rd /Q /S C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18\ReadOnly\LockScreen* 
rem rd /Q /S C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-21-1690007262-1860438432-1133890597-1001\ReadOnly\LockScreen*

rem for /f %%i in ('dir /a:d /s /b C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18\ReadOnly\LockScreen*') do rd /s /q  %%i 
rem for /f %%i in ('dir /a:d /s /b C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-21-1690007262-1860438432-1133890597-1001\ReadOnly\LockScreen*') do rd /s /q %%i
