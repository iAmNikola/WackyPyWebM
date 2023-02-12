@echo off

:: Print Ascii Art (ugly because batch requires escaping of "|" and "<" with `^`, instead of with `\`.)


echo __          __        _          _____    __          __  _               
echo \ \        / /       ^| ^|        ^|  __ \   \ \        / / ^| ^|              
echo  \ \  /\  / /_ _  ___^| ^| ___   _^| ^|__) ^|   \ \  /\  / /__^| ^|__  _ __ ___  
echo   \ \/  \/ / _` ^|/ __| ^|/ / ^| ^| ^|  ___/ ^| ^| \ \/  \/ / _ \ '_ \^| '_ ` _ \ 
echo    \  /\  / (_^| ^| (__^|   ^<^| ^|_^| ^| ^|   ^| ^|_^| ^|\  /\  /  __/ ^|_) ^| ^| ^| ^| ^| ^|
echo     \/  \/ \__,_^|\___^|_^|\_\\__, ^|_^|    \__, ^| \/  \/ \___^|_.__/^|_^| ^|_^| ^|_^|
echo                             __/ ^|       __/ ^|                             
echo                            ^|___/       ^|___/                              

echo.

:: test for dependencies.
echo Testing for FFmpeg, FFprobe, Node and npm...

where /q ffmpeg || echo FFmpeg could not be found && exit /B
where /q ffprobe || echo FFprobe could not be found && exit /B
where /q py || echo Python could not found && exit /B

call pip install -r requirements.txt >NUL

set "lang=en_us"
set /p "lang=Enter the language [en_us]: "

echo Starting UI
py terminal_ui.py --lang %lang%
