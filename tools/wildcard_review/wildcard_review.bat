@echo off
rem Wildcard review: page through the wildcard lists, Keep / Dump / Same as. Opens http://127.0.0.1:8766
cd /d "A:\Comfy25\ComfyUI_windows_portable\ComfyUI\custom_nodes\video_prompter"
A:\Comfy25\ComfyUI_windows_portable\python_embeded\python.exe -X utf8 tools\wildcard_review\server.py %*
pause

