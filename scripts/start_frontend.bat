@echo off
chcp 65001 >nul
title 智慧农业管理系统 - 前端 (Vite :5173)
cd /d %~dp0frontend
echo ============================================
echo  智慧农业管理系统 v2 - 前端启动
echo  访问地址: http://127.0.0.1:5173
echo  (首次运行需 npm install)
echo ============================================
if not exist node_modules (
  echo 未检测到 node_modules，开始安装依赖...
  call npm install --cache .\.npm-cache --prefer-online
)
npm run dev
pause