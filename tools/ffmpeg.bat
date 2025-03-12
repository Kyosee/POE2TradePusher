@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: ������ԱȨ��
NET FILE >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo �������ԱȨ��...
    powershell -Command "Start-Process cmd -ArgumentList '/c %0' -Verb RunAs"
    exit /b
)

:: ����Ƿ��Ѱ�װFFmpeg
where ffmpeg >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo FFmpeg �Ѱ�װ
    pause
    exit /b
)

:: ���ð�װ����
set "install_path=C:\ffmpeg"
set "bin_path=%install_path%\bin"
set "local_zip=%~dp0ffmpeg.zip"

:: ��֤����ѹ����
if not exist "%local_zip%" (
    echo ���󣺵�ǰĿ¼δ�ҵ�ffmpeg.zip
    echo �뽫FFmpegѹ����������Ϊffmpeg.zip�����ڴ�Ŀ¼
    pause
    exit /b 1
)

:: ������װĿ¼
if exist "%install_path%" (
    rd /s /q "%install_path%"
)
mkdir "%install_path%"

:: ��ѹ�ļ���֧��ZIP/7Z��ʽ��
echo ���ڽ�ѹ...
powershell -Command "Expand-Archive -Path '%local_zip%' -DestinationPath '%install_path%' -Force"
if %ERRORLEVEL% neq 0 (
    echo ��ѹʧ�ܣ�����ѹ����������
    pause
    exit /b 1
)

:: ����Ŀ¼�ṹ���Զ�����binĿ¼��
for /d %%i in ("%install_path%\*") do (
    if exist "%%i\bin\ffmpeg.exe" (
        move "%%i\*" "%install_path%\" >nul
        rd "%%i"
    )
)

:: ��ӻ�������
setx PATH "%bin_path%;%PATH%" /m >nul
if %ERRORLEVEL% neq 0 (
    echo ������������ʧ��
    pause
    exit /b 1
)

echo ��װ��ɣ�FFmpeg�Ѱ�װ�� %install_path%
echo �����󻷾�������Ч�����ֶ�ˢ�»�������
echo ��֤��װ������CMD����ִ�� ffmpeg -version
pause