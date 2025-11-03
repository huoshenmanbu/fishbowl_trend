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
    cwd: "/home/ubuntu/fishbowl_trend/web",
    script: "/home/ubuntu/fishbowl_trend/venv/bin/gunicorn",
    args: "server:app -b 0.0.0.0:5000 -w 3",
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

### 2.4 启动 PM2
```bash
cd /root/fishbowl_trend  # 进入项目根目录
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # 设置开机自启

# 查看运行状态
pm2 status
pm2 logs fishbowl_trend
```

### 2.5 配置 Nginx（必需，用于反向代理）
```bash
# 安装 Nginx
sudo apt install -y nginx

# 复制配置文件到 Nginx 目录
sudo cp /root/fishbowl_trend/web/nginx.conf /etc/nginx/sites-available/fishbowl

# 或者手动创建配置
sudo nano /etc/nginx/sites-available/fishbowl
```

写入以下配置（项目中已提供 `web/nginx.conf` 文件）：
```nginx
server {
    listen 80;
    server_name _;  # 接受任何域名/IP访问，或改为你的域名

    # 访问日志
    access_log /var/log/nginx/fishbowl_access.log;
    error_log /var/log/nginx/fishbowl_error.log;

    # 客户端请求体大小限制
    client_max_body_size 10M;

    # 代理到本地Flask应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用站点并重启 Nginx：
```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/fishbowl /etc/nginx/sites-enabled/

# 删除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
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

### 4.1 访问服务器IP出现404错误

**检查清单：**

1. **检查 PM2 服务是否运行**
```bash
pm2 status
# 应该看到 fishbowl_trend 状态为 online

# 查看详细日志
pm2 logs fishbowl_trend --lines 50
```

2. **检查 gunicorn 是否正确监听 5000 端口**
```bash
netstat -tlnp | grep 5000
# 应该显示: tcp  0  0  127.0.0.1:5000  0.0.0.0:*  LISTEN

# 或使用 ss 命令
ss -tlnp | grep 5000
```

3. **检查 Nginx 是否正在运行**
```bash
sudo systemctl status nginx
# 应该显示 active (running)

# 如果未运行，启动它
sudo systemctl start nginx
```

4. **检查 Nginx 配置是否正确**
```bash
# 测试配置文件语法
sudo nginx -t

# 查看已启用的站点
ls -la /etc/nginx/sites-enabled/

# 检查配置内容
cat /etc/nginx/sites-available/fishbowl
```

5. **查看 Nginx 日志**
```bash
# 查看错误日志
sudo tail -f /var/log/nginx/fishbowl_error.log
sudo tail -f /var/log/nginx/error.log

# 查看访问日志
sudo tail -f /var/log/nginx/fishbowl_access.log
sudo tail -f /var/log/nginx/access.log
```

6. **测试本地连接**
```bash
# 在服务器上测试 Flask 应用是否响应
curl http://127.0.0.1:5000/

# 测试 Nginx 代理
curl http://127.0.0.1/
```

7. **检查防火墙设置**
```bash
# 查看 UFW 状态
sudo ufw status

# 确保80端口开放
sudo ufw allow 80/tcp

# 查看 iptables 规则
sudo iptables -L -n
```

8. **重启所有服务**
```bash
# 重启 PM2 应用
pm2 restart fishbowl_trend

# 重启 Nginx
sudo systemctl restart nginx

# 查看状态
pm2 status
sudo systemctl status nginx
```

### 4.2 Nginx 常见错误修复

**错误：502 Bad Gateway**
- 原因：Nginx 无法连接到后端服务（gunicorn）
- 解决：
```bash
# 确认 gunicorn 正在运行
pm2 status
pm2 logs fishbowl_trend

# 检查端口
netstat -tlnp | grep 5000
```

**错误：403 Forbidden**
- 原因：权限问题或目录不存在
- 解决：
```bash
# 检查文件权限
ls -la /root/fishbowl_trend/web/

# 检查 Nginx 用户权限
ps aux | grep nginx
```

**错误：配置文件未生效**
```bash
# 删除旧的符号链接
sudo rm /etc/nginx/sites-enabled/fishbowl

# 重新创建
sudo ln -s /etc/nginx/sites-available/fishbowl /etc/nginx/sites-enabled/

# 测试并重启
sudo nginx -t
sudo systemctl restart nginx
```

### 4.3 完整的诊断命令集
```bash
# 一键诊断脚本
echo "=== PM2 状态 ==="
pm2 status

echo -e "\n=== 端口监听情况 ==="
netstat -tlnp | grep -E "5000|80"

echo -e "\n=== Nginx 状态 ==="
sudo systemctl status nginx

echo -e "\n=== Nginx 配置测试 ==="
sudo nginx -t

echo -e "\n=== 防火墙状态 ==="
sudo ufw status

echo -e "\n=== 最近的错误日志 ==="
pm2 logs fishbowl_trend --lines 20 --nostream
sudo tail -20 /var/log/nginx/error.log
```