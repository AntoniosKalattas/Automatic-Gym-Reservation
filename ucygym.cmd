@echo off
rem Runs the UCY Gym bot, building it first if the jar is missing. Usage: ucygym <command>
setlocal
cd /d "%~dp0"
if not exist target\ucygym.jar (
  echo Building the bot...
  call mvn -q package || exit /b 1
)
java -jar target\ucygym.jar %*
