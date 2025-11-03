# Ubuntu 服务器部署指南 (使用 PM2)

## 1. 系统要求
- Ubuntu Server (推荐 20.04 LTS 或更高版本)
- Python 3.8+ 
- Node.js 14+ (用于 PM2)

## 2. 安装步骤

### 2.1 安装系统依赖
```bash
# 更新系统包
sudo apt update
sudo apt upgrade -y

# 安装 Python 和相关工具
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js 和 npm
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 PM2
sudo npm install -g pm2
```

### 2.2 准备项目
```bash
# 创建项目目录（示例）
mkdir -p /opt/fishbowl_trend
cd /opt/fishbowl_trend

# 复制项目文件到服务器
# 方法1：使用 git（如果是git仓库）
git clone [your-repository-url]

# 方法2：使用 scp（从本地复制）
# 在本地执行：
scp -r /path/to/fishbowl_trend/* user@your-server:/opt/fishbowl_trend/
```

### 2.3 设置 Python 环境
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2.3 配置 PM2
创建 `ecosystem.config.js` 文件：
```javascript
module.exports = {
  apps: [{
    name: "fishbowl_trend",
    cwd: "/home/ubuntu/fishbowl_trend/fishvowl_trend/web",
    script: "/home/ubuntu/fishbowl_trend/venv/bin/gunicorn",
    args: "server:app -b 127.0.0.1:5000 -w 3",
    interpreter: "/home/ubuntu/fishbowl_trend/venv/bin/python",
    env: {
      "PYTHONPATH": "/home/ubuntu/fishbowl_trend",
      "FLASK_ENV": "production"
    },
    exec_mode: "fork",
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: "500M",
    error_file: "/home/ubuntu/fishbowl_trend/logs/err.log",
    out_file: "/home/ubuntu/fishbowl_trend/logs/out.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss"
  }]
}
```

### 2.4 配置 Nginx
创建服务文件：
```bash
sudo nano /etc/systemd/system/fishbowl.service
```

写入以下内容：
```ini
[Unit]
Description=Fishbowl Trend Analysis Web Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/fishbowl_trend
Environment="PATH=/opt/fishbowl_trend/.venv/bin"
ExecStart=/opt/fishbowl_trend/.venv/bin/python web/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable fishbowl
sudo systemctl start fishbowl
```

### 2.6 配置 Nginx（可选，推荐）
```bash
sudo apt install nginx

# 创建 Nginx 配置
sudo nano /etc/nginx/sites-available/fishbowl
```

写入以下配置：
```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/fishbowl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2.7 配置防火墙（如果启用了防火墙）
```bash
# 如果使用 UFW
sudo ufw allow 80/tcp  # 如果使用 Nginx
sudo ufw allow 5000/tcp  # 如果直接访问 Flask
```

## 3. 注意事项

### 3.1 文件权限
确保运行服务的用户有权限访问所有必要的文件：
```bash
# 假设使用 www-data 用户运行
sudo chown -R www-data:www-data /opt/fishbowl_trend
```

### 3.2 日志
系统日志查看：
```bash
sudo journalctl -u fishbowl -f
```

### 3.3 安全建议
- 使用 HTTPS（通过 Nginx + Let's Encrypt）
- 设置适当的文件权限
- 使用非 root 用户运行服务
- 考虑添加基本的认证机制

### 3.4 定时任务（可选）
如果需要定期自动刷新数据，可以设置 cron 任务：
```bash
crontab -e
```

添加类似下面的行：
```
*/5 * * * * curl -X POST http://localhost:5000/api/refresh
```

## 4. 常见问题排查

### 4.1 服务无法启动
检查日志：
```bash
sudo journalctl -u fishbowl -n 50
```

### 4.2 无法访问网页
- 检查防火墙设置
- 检查 Nginx 配置和日志
- 确认 Flask 服务正在运行
```bash
ps aux | grep python
netstat -tlpn | grep 5000
```