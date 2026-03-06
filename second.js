const express = require("express");
const app = express();

// 模拟大数据生成器
function generateLargeData() {
  let res = "";
  for (let i = 0; i < 10; i++) {
    //   for (let i = 0; i < 1001111; i++) {
    res += `数据行 ${i}: ${"x"}`;
  }
  return res;
}

app.get("/stream-data", (req, res) => {
  const headers = req.headers;
  console.log("🚀 ~ headers:", headers);
  // 设置响应头，表明这是一个流式响应
  res.writeHead(200, {
    "Content-Type": "application/json",
  });

  const data = generateLargeData();

  res.end(JSON.stringify({ data }));
});

// 模拟客户端
app.get("/client", async (req, res) => {
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
});

app.listen(3000, () => {
  console.log("服务器运行在 http://localhost:3000");
});
