@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: ========================================================
:: [설정] 경로 및 파일명 정의
:: ========================================================
set "DIST_PATH=\\cox_biz\생산-영업\ProductionManager_Update"
set "MAIN_PY=main.py"
set "CONFIG_PY=config.py"
set "VERSION_FILE=version.txt"

:: ========================================================
:: 1. config.py에서 APP_VERSION 읽기
:: ========================================================
echo Reading version from %CONFIG_PY%...
set "APP_VERSION="

:: "APP_VERSION =" 문자열이 포함된 줄을 찾아서 파싱
for /f "tokens=2 delims==" %%A in ('findstr /C:"APP_VERSION =" %CONFIG_PY%') do (
    set "temp_ver=%%A"
    :: 따옴표와 공백 제거
    set "temp_ver=!temp_ver:"=!"
    set "temp_ver=!temp_ver: =!"
    set "APP_VERSION=!temp_ver!"
)

echo Detected Version: !APP_VERSION!

:: ========================================================
:: 2. PyInstaller 실행 (네트워크 경로로 직접 빌드)
:: ========================================================
echo Running PyInstaller...
pyinstaller --onedir --noconsole --noconfirm --icon=logo.ico --distpath "%DIST_PATH%" "%MAIN_PY%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller failed!
    pause
    exit /b %errorlevel%
)

:: ========================================================
:: 3. version.txt 업데이트 및 복사
:: ========================================================
echo Updating version files...

:: 루트 경로의 version.txt 생성
echo !APP_VERSION!> "%DIST_PATH%\%VERSION_FILE%"

:: main 폴더 안으로 복사
copy /y "%DIST_PATH%\%VERSION_FILE%" "%DIST_PATH%\main\%VERSION_FILE%"

echo.
echo ========================================================
echo  Build and Version Update Complete! (Version: !APP_VERSION!)
echo ========================================================
pause
