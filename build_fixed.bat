@echo off
echo Construindo o executável do Painel B3 com configurações otimizadas...

rem Limpar diretórios anteriores
if exist "dist" rd /s /q dist
if exist "build" rd /s /q build

rem Construir com PyInstaller usando configurações especiais
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "data;data" ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import matplotlib ^
    --hidden-import pandas_market_calendars ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import tkinter ^
    --collect-submodules pandas ^
    --collect-submodules numpy ^
    --collect-submodules matplotlib ^
    --upx-exclude vcruntime140.dll ^
    --upx-exclude vcruntime140_1.dll ^
    --name "PainelB3" ^
    src\main.py

echo.
echo Construção concluída! O executável está na pasta 'dist\PainelB3'.
echo.
pause