import time
import random from typing 
import Dict, Any
import requests from fastapi 
import FastAPI, HTTPException from pydantic 
import BaseModel

app = FastAPI()

# 定义请求数据模型
class B2BLeadRequest(BaseModel):
    email: str
    create_b2b_lead: int

# 模拟 n8n Webhook URL
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/b2b-leads"

def call_n8n_webhook(data: Dict[str, Any], max_retries: int = 3) -> bool:
    """
    调用 n8n webhook，包含重试机制
    """
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=data,
            timeout=5  # 设置 5 秒超时
        )
        
        if response.status_code == 200:
            return True
            
    except requests.exceptions.Timeout:
        """
        如果有重试的机会，继续重试，否则把该信息记录等待消息队列异步执行任务，并且写入日志帮助员工定位问题
        """
        if max_retries > 0 :
            return call_n8n_webhook(data, max_retries - 1)
        else:
            """
            伪代码
            """
            log_error(data, "Timeout when calling n8n webhook")
            """
            此种消息队列可以以定时任务的方式执行命令，或者也可以在此处调用消息队列的 API 接口，将消息推送到消息队列中，等待消息队列异步执行任务
            """
            redis_client.lpush("b2b_leads_queue", json.dumps(data))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
    return False

@app.post("/api/create_b2b_lead")
async def create_b2b_lead(request: B2BLeadRequest):
    """
    AI 工具调用接口，创建 B2B 潜在客户
    """
    try:
        # 准备要发送到 n8n 的数据
        lead_data = {
            "email": request.email,
            "create_b2b_lead": request.create_b2b_lead,
            "timestamp": time.time()
        }

        # 调用 n8n webhook
        success = call_n8n_webhook(lead_data)
        
        if success:
            return {
                "status": "success",
                "message": "B2B lead created successfully",
                "lead_data": lead_data
            }
        return {
                "status": "success",
                "message": "抱歉，我们的专属大客户通道目前排队人数较多，您的诉求已记录，请稍后再试。",
                "lead_data": ""
            }
            
  

# 测试接口
@app.get("/api/test")
async def test():
    """
    测试接口，模拟 AI 识别结果
    """
    test_data = {
        "email": "distributor@example.com",
        "create_b2b_lead": 10000
    }
    return await create_b2b_lead(B2BLeadRequest(**test_data))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
