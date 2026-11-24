@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Prepare este computador seguindo a secao "Antes da apresentacao" do README.md.
    pause
    exit /b 1
)

"%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0classificar_morcegos.py"
if errorlevel 1 (
    echo.
    echo A execucao falhou. Confira a mensagem acima.
    pause
    exit /b 1
)

echo.
echo Arquivos gerados na pasta resultados:
echo   classificacao.csv
echo   indices_morcegos.txt
pause
exit /b 0
