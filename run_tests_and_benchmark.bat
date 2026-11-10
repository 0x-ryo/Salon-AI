@echo off
title Run Tests & Benchmark - Salon AI
echo ===============================================================
echo   🧪 Running Pytest System Test Suite & Benchmark 🧪
echo ===============================================================
echo.
echo 1. Executing Pytest Unit & System Tests...
"C:\Users\suman\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests\test_ai_system.py -v
echo.
echo 2. Executing Comparative Benchmark (Approach 1 vs Approach 2)...
"C:\Users\suman\AppData\Local\Programs\Python\Python312\python.exe" -m benchmark.evaluate
echo.
echo Done!
pause
