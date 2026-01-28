@echo off
:: Título da Janela
title JVC Turismo - Sistema

:: Cor da tela (Fundo Preto, Letra Verde - estilo Hacker)
color 0A

echo ==========================================
echo      INICIANDO O SISTEMA JVC TURISMO
echo ==========================================
echo.

:: 1. Entra na pasta do projeto (O comando %~dp0 garante que ele rode onde o arquivo está)
cd /d "%~dp0"

:: 2. Ativa o ambiente virtual (ajuste 'venv' se sua pasta tiver outro nome, ex: .venv)
call venv\Scripts\activate

:: 3. Abre o navegador automaticamente após 3 segundos
timeout /t 3 >nul
start http://127.0.0.1:8000/dashboard/nova-reserva/

:: 4. Roda o servidor
echo Servidor rodando... Pressione CTRL+C para parar.
python manage.py runserver

pause