@echo off
setlocal

set VENV_PYTHON=.venv_verify\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    echo Using virtual environment: %VENV_PYTHON%
    "%VENV_PYTHON%" run_tests.py
) else (
    echo Using system python...
    python run_tests.py
)

if %ERRORLEVEL% equ 0 (
    echo.
    echo All tests passed!
) else (
    echo.
    echo Some tests failed.
    exit /b 1
)
