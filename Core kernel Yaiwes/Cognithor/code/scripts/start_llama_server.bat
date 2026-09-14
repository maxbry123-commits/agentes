@echo off
REM ============================================================
REM  llama-server Starter fuer Cognithor
REM  Startet llama.cpp Server mit optimierten KV-Cache Settings
REM ============================================================

set LLAMA_SERVER=C:\Users\ArtiCall\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe
set MODEL=C:\Users\ArtiCall\.ollama\models\blobs\sha256-d4b8b4f4c350f5d322dc8235175eeae02d32c6f3fd70bdb9ea481e3abb7d7fc4

REM KV-Cache Einstellungen:
REM   -ctk q8_0    = KV-Cache Key Quantisierung (spart ~50%% VRAM vs F16)
REM   -ctv q8_0    = KV-Cache Value Quantisierung
REM   -c 258048    = 252K Kontextfenster (statt Ollama's 64K Limit)
REM   -ngl 99      = Alle Layer auf GPU (99 = alle verfuegbaren)
REM   --port 8080  = Standard llama.cpp Port
REM   -fa           = Flash Attention (schneller, weniger VRAM)

echo ============================================================
echo  Cognithor llama.cpp Server
echo  Modell: qwen3.5:27b-Q4_K_M
echo  Kontext: 252K (KV-Cache Q8_0)
echo  GPU: Vulkan, alle Layer
echo ============================================================
echo.

"%LLAMA_SERVER%" ^
    -m "%MODEL%" ^
    -c 258048 ^
    -ctk q8_0 ^
    -ctv q8_0 ^
    -ngl 99 ^
    -fa ^
    --port 8080 ^
    --host 0.0.0.0 ^
    -t 8

pause
