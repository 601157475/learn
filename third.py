from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from datetime import datetime
import re
import uuid
import logging
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI()

# Token管理器
class TokenManager:
    def __init__(self):
        self.blacklisted_tokens = set()
    
    def is_blacklisted(self, token: str) -> bool:
        return token in self.blacklisted_tokens
    
    def add_to_blacklist(self, token: str):
        self.blacklisted_tokens.add(token)
    
    def remove_from_blacklist(self, token: str):
        self.blacklisted_tokens.discard(token)

# 创建Token管理器实例
token_manager = TokenManager()

# 安全日志记录器
class SecurityLogger:
    @staticmethod
    def log_security_event(message: str, request: Request, reason: str = None):
        log_data = {
            "level": "SECURITY",
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "request": {
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            },
            "reason": reason
        }
        logger.error(str(log_data))

# AI平台认证中间件
async def ai_platform_auth_middleware(request: Request, call_next):
    # 只对AI平台相关路径进行拦截
    if not request.url.path.startswith("/api/ai/"):
        return await call_next(request)

    # 获取Token
    token = request.headers.get("x-age-verified-token")
    
    # Token验证
    if not token:
        SecurityLogger.log_security_event(
            "AI平台请求拦截：Token缺失",
            request,
            "MISSING_TOKEN"
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": "Authentication token is required",
                "code": "MISSING_TOKEN",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Token格式验证（UUID格式）
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    if not uuid_pattern.match(token):
        SecurityLogger.log_security_event(
            "AI平台请求拦截：Token格式错误",
            request,
            "INVALID_TOKEN_FORMAT"
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": "Invalid token format",
                "code": "INVALID_TOKEN_FORMAT",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Token黑名单检查
    if token_manager.is_blacklisted(token):
        SecurityLogger.log_security_event(
            "AI平台请求拦截：Token已被撤销",
            request,
            "TOKEN_BLACKLISTED"
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": "Token has been revoked",
                "code": "TOKEN_BLACKLISTED",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Token过期验证
    try:
        # 这里假设token中包含时间戳信息
        token_time = datetime.fromisoformat(token.split('-')[-1])
        if (datetime.utcnow() - token_time).days > 1:
            SecurityLogger.log_security_event(
                "AI平台请求拦截：Token已过期",
                request,
                "TOKEN_EXPIRED"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Token has expired",
                    "code": "TOKEN_EXPIRED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except (ValueError, IndexError):
        SecurityLogger.log_security_event(
            "AI平台请求拦截：Token解析错误",
            request,
            "TOKEN_PARSE_ERROR"
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": "Invalid token",
                "code": "TOKEN_PARSE_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Token验证通过，记录日志
    logger.info(f"AI平台请求验证通过: {request.method} {request.url.path}")
    
    # 将验证信息添加到请求状态
    request.state.auth_info = {
        "token": token,
        "verified": True,
        "verified_at": datetime.utcnow().isoformat()
    }

    # 继续处理请求
    response = await call_next(request)
    return response

# 添加中间件
app.middleware("http")(ai_platform_auth_middleware)

# 示例路由
@app.get("/api/ai/chat")
async def ai_chat(request: Request):
    return {
        "message": "AI Chat API",
        "auth_info": request.state.auth_info
    }

# Token撤销路由
@app.post("/api/auth/revoke")
async def revoke_token(
    request: Request,
    x_age_verified_token: Optional[str] = Header(None)
):
    if x_age_verified_token:
        token_manager.add_to_blacklist(x_age_verified_token)
        SecurityLogger.log_security_event(
            "Token已撤销",
            request,
            "TOKEN_REVOKED"
        )
    return {"message": "Token revoked"}

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
