@echo off
chcp 65001 >nul
title 智慧农业管理系统 - 后端 (FastAPI :8001)
cd /d %~dp0server
echo ============================================
echo  智慧农业管理系统 v2 - 后端启动
echo  API 地址: http://127.0.0.1:8001/api
echo  管理 Token: server\auth_token.txt
echo ============================================
python -m uvicorn main:app --host 127.0.0.1 --port 8001
pause