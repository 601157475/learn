### 第一题

核心方法如下

```
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

```

---

### 第二题

核心方法如下

```
 const controller = new AbortController();
  // 监听页面卸载事件，取消请求
  // vue 组件中可以使用 beforeDestroy ||  berforeUnmounted 生命周期钩子来取消请求
  //   window.addEventListener("beforeunload", () => {
  //     controller.abort(); // 页面卸载时取消请求
  //   });
  const response = await fetch("http://localhost:3000/stream-data", {
    signal: controller.signal,
    headers: {
      "Custom-Header": "custom-value",
      token: "xxx", // 自定义请求头   自定义请求头需要服务器允许跨域请求时设置 Access-Control-Allow-Headers
      session_id: "abc123", // 自定义请求头
    },
  });
  const reader = response.body.getReader();
  console.time("读取数据"); // 开始计时
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = new TextDecoder().decode(value);
    // console.log("🚀 ~ value:", value);
    // console.log(text);
    // 伪代码 - 将数据追加到页面上
    // document.getElementById("data").innerText += text;
  }
  console.timeEnd("读取数据"); // 结束计时
  res.send("数据已接收");
```

---

### 第三题

思路如下

> 1. 中间件符合洋葱圈模型，先进后出。
> 2. 在后端框架开发中，我们可以通过中间件来拦截请求，对请求进行校验，比如 token 校验，ip 黑名单校验等。如果报错return可以强行终止本次请求。
> 3. 为了安全我们可以自定义一系列的安全规则，相关数据可以保存在header中，比如请求的时间戳，请求的ip地址，请求的token等， 并且根据自定义的一些算法，生成一个校验码，后端可以重新计算校验码，如果校验码一致，则认为请求合法，否则认为请求不合法。并且可以设置请求的过期时间，比如5秒钟，如果超过5秒钟，则认为请求过期，不合法。增加非法用户破解难度。
