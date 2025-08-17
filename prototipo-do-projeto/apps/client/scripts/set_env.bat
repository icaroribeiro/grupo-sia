   @echo off
   for /f "tokens=1* delims==" %%a in ('.env') do (
       set "%%a=%%b"
   )
   echo Environment variables set from .env file.