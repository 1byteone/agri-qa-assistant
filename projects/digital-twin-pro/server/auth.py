# -*- coding: utf-8 -*-
"""简易 Token 鉴权（MVP，适配本机部署）。

Token 优先级：
1. 环境变量 AGRI_ADMIN_TOKEN（存在则优先使用，不再读写文件）
2. 文件 server/auth_token.txt（首次启动自动生成随机 token 并持久化）

比较用 hmac.compare_digest 常量时间比较，防止时序攻击。
"""

import hashlib
import hmac
import os
import secrets
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "auth_token.txt"

# 认证方案（用于 Swagger 文档展示 Authorize 按钮）
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="管理端写接口令牌（server/auth_token.txt 或环境变量 AGRI_ADMIN_TOKEN）",
)


def _generate_token() -> str:
    """生成 32 字节 URL 安全随机 token（约 43 字符）。"""
    return secrets.token_urlsafe(32)


def load_or_create_token() -> str:
    """读取环境变量或本地文件中的 token；都不存在则生成并写入文件。"""
    env_token = os.environ.get("AGRI_ADMIN_TOKEN", "").strip()
    if env_token:
        return env_token
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = _generate_token()
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    return token


# 模块加载时初始化（服务器启动时执行一次）
ADMIN_TOKEN = load_or_create_token()


def verify_token(token: str) -> bool:
    """常量时间比较：token 是否与服务器令牌一致。"""
    if not token:
        return False
    return hmac.compare_digest(
        token.encode("utf-8"), ADMIN_TOKEN.encode("utf-8")
    )


def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """FastAPI 依赖：写接口必须携带有效 Bearer Token，否则返回 401。"""
    if credentials is None or not verify_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或缺失的管理令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# ---------------------------------------------------------------
# 账号密码哈希（sha256 加盐，无第三方依赖；供 /api/auth/login 使用）
# ---------------------------------------------------------------

def hash_password(password: str, salt: str | None = None) -> str:
    """生成加盐哈希，格式：sha256:<salt>:<hexdigest>。"""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256:{salt}:{digest}"


def verify_password(password: str, stored: str) -> bool:
    """常量时间比较校验密码。"""
    try:
        algo, salt, digest = (stored or "").split(":")
        if algo != "sha256":
            return False
        calc = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(calc, digest)
    except Exception:
        return False