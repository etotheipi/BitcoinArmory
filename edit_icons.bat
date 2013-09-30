@CLS
@SET CURRENT_DIR="%CD%"
@SET BATH_DIR="%~dp0"
@CD %BATH_DIR% || EXIT 100
@CD .. || EXIT 100
@CD .. || EXIT 100
@SET PATH=%PATH%;%CD%
@CD %BATH_DIR% || EXIT 100

rtc.exe /L:"%~dp0\log.txt" /F:edit_icons.rts

@CD %CURRENT_DIR% || EXIT 100
