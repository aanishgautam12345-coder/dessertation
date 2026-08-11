@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
set "PGROOT=C:\Program Files\PostgreSQL\18"
cd /d "D:\Downloads\jobmatch-scaffold\jobmatch\pgvector-src\pgvector-0.8.0"
nmake /F Makefile.win
if errorlevel 1 (
    echo BUILD FAILED
    exit /b 1
)
nmake /F Makefile.win install
if errorlevel 1 (
    echo INSTALL FAILED
    exit /b 1
)
echo SUCCESS
