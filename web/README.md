# fishvowl_trend — 本地网页查看器

这是一个简单的本地网页，用来展示 `data/trend_status/latest_trend_result.json` 的内容，并提供“获取最新趋势”按钮。

运行步骤（Windows PowerShell）：

1. 安装依赖（推荐使用虚拟环境）

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
```

2. 启动服务器

```powershell
python web\server.py
```

3. 浏览器打开：

http://127.0.0.1:5000

说明：
- 页面会从 `data/trend_status/latest_trend_result.json` 读取数据并渲染表格。
- 勾选“重新计算（执行 main_trend.py）”并点击“获取最新趋势”会在后台执行项目根目录的 `main_trend.py`（如果存在），运行时间取决于您的环境。此操作会在服务器端以子进程方式执行，请确认环境变量与依赖已正确安装。
