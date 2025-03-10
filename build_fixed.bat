@echo off
echo Construindo o Painel B3 (versao completa)...

rem Criar estrutura de diretorios necessaria
if not exist "cache" mkdir cache
echo # Cache para dados de acoes > cache\README.txt

rem Limpar diretorios anteriores
if exist "dist" rd /s /q dist
if exist "build" rd /s /q build

rem Construir com PyInstaller incluindo TODAS as pastas importantes
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "cache;cache" ^
    --add-data "src\data;src\data" ^
    --add-data "src\dashboard;src\dashboard" ^
    --add-data "src\utils;src\utils" ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import matplotlib ^
    --hidden-import pandas_market_calendars ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import yfinance ^
    --hidden-import tkinter ^
    --hidden-import urllib3 ^
    --hidden-import requests ^
    --exclude-module upx ^
    --name "PainelB3" ^
    src\main.py

echo.
if exist "dist\PainelB3\PainelB3.exe" (
    echo Construcao concluida! Executavel criado em 'dist\PainelB3\PainelB3.exe'
    echo.
    echo IMPORTANTE: Para distribuir, envie a pasta 'dist\PainelB3' completa.
) else (
    echo ERRO: A construcao falhou. Verifique as mensagens acima.
)
echo.
pause