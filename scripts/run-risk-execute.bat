@echo off
setlocal EnableExtensions

for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"

REM Run from repository root regardless of where Task Scheduler starts.
cd /d "%~dp0.."

set "ACTION=%~1"
if "%ACTION%"=="" goto :usage

if "%SCHEDULE_AUDIT_LOG%"=="" (
	set "LOG_FILE=logs\scheduler-audit.log"
) else (
	set "LOG_FILE=%SCHEDULE_AUDIT_LOG%"
)

if not exist "logs" mkdir "logs"

>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo ==================================================
>> "%LOG_FILE%" echo [%date% %time%] START action=%ACTION%

call :log 36 "Starting Jira agent scheduled run..."

REM Optional: override log verbosity for scheduler runs.
if "%AGENT_LOG_LEVEL%"=="" set "AGENT_LOG_LEVEL=info"

call :log 36 "Step 1/3: Testing LLM connection..."
>> "%LOG_FILE%" echo [%date% %time%] CMD npm run agent -- test-llm
call npm run agent -- test-llm >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail_llm

call :log 36 "Step 2/3: Testing MCP connection..."
>> "%LOG_FILE%" echo [%date% %time%] CMD npm run agent -- test-mcp
call npm run agent -- test-mcp >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail_mcp

call :log 36 "Step 3/3: Executing %ACTION% action updates..."
>> "%LOG_FILE%" echo [%date% %time%] CMD npm run agent -- run --action %ACTION% --execute
call npm run agent -- run --action %ACTION% --execute >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail_run

call :log 32 "SUCCESS: Scheduled run completed."
>> "%LOG_FILE%" echo [%date% %time%] END status=SUCCESS
exit /b 0

:fail_llm
call :log 31 "FAILED: test-llm failed."
>> "%LOG_FILE%" echo [%date% %time%] END status=FAILED step=test-llm
exit /b 1

:fail_mcp
call :log 31 "FAILED: test-mcp failed."
>> "%LOG_FILE%" echo [%date% %time%] END status=FAILED step=test-mcp
exit /b 2

:fail_run
call :log 31 "FAILED: run --action %ACTION% --execute failed."
>> "%LOG_FILE%" echo [%date% %time%] END status=FAILED step=execute action=%ACTION%
exit /b 3

:usage
call :log 33 "Usage: %~nx0 <action-name>"
call :log 33 "Example: %~nx0 risk"
exit /b 64

:log
set "COLOR=%~1"
set "MSG=%~2"
if defined LOG_FILE >> "%LOG_FILE%" echo [%date% %time%] %MSG%
echo %ESC%[%COLOR%m[%date% %time%] %MSG%%ESC%[0m
exit /b 0
