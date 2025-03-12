@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: 检查管理员权限
NET FILE >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo 请求管理员权限...
    powershell -Command "Start-Process cmd -ArgumentList '/c %0' -Verb RunAs"
    exit /b
)

:: 检查是否已安装FFmpeg
where ffmpeg >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo FFmpeg 已安装
    pause
    exit /b
)

:: 设置安装参数
set "install_path=C:\ffmpeg"
set "bin_path=%install_path%\bin"
set "local_zip=%~dp0ffmpeg.zip"

:: 验证本地压缩包
if not exist "%local_zip%" (
    echo 错误：当前目录未找到ffmpeg.zip
    echo 请将FFmpeg压缩包重命名为ffmpeg.zip并放在此目录
    pause
    exit /b 1
)

:: 创建安装目录
if exist "%install_path%" (
    rd /s /q "%install_path%"
)
mkdir "%install_path%"

:: 解压文件（支持ZIP/7Z格式）
echo 正在解压...
powershell -Command "Expand-Archive -Path '%local_zip%' -DestinationPath '%install_path%' -Force"
if %ERRORLEVEL% neq 0 (
    echo 解压失败，请检查压缩包完整性
    pause
    exit /b 1
)

:: 整理目录结构（自动搜索bin目录）
for /d %%i in ("%install_path%\*") do (
    if exist "%%i\bin\ffmpeg.exe" (
        move "%%i\*" "%install_path%\" >nul
        rd "%%i"
    )
)

:: 添加环境变量
setx PATH "%bin_path%;%PATH%" /m >nul
if %ERRORLEVEL% neq 0 (
    echo 环境变量配置失败
    pause
    exit /b 1
)

echo 安装完成！FFmpeg已安装到 %install_path%
echo 重启后环境变量生效，或手动刷新环境变量
echo 验证安装：打开新CMD窗口执行 ffmpeg -version
pause