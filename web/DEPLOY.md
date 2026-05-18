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

### 2.4 配置 PM2 + Gunicorn（仅本机 5000）

仓库根目录 `ecosystem.config.js` 默认 **`127.0.0.1:5000`**，不应对公网直接暴露 5000（可减少扫描器刷 Gunicorn 日志）。

```bash
cd /root/fishbowl_trend   # 与 ecosystem.config.js 同级
source venv/bin/activate
pip install -r requirements.txt
pm2 delete fishbowl_trend 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
```

虚拟环境路径非默认时：

```bash
export FISHBOWL_VENV=/root/fishbowl_trend/venv
pm2 start ecosystem.config.js
```

### 2.5 配置 Nginx（推荐，对外 80）

```bash
sudo apt install -y nginx
sudo cp /root/fishbowl_trend/deploy/nginx/fishbowl.conf /etc/nginx/sites-available/fishbowl
# 编辑 server_name 为你的公网 IP 或域名
sudo nano /etc/nginx/sites-available/fishbowl
sudo ln -sf /etc/nginx/sites-available/fishbowl /etc/nginx/sites-enabled/fishbowl
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

浏览器访问：**`http://47.79.93.60/`**（换成你的 IP）。

### 2.6 安全组 / 防火墙

- **放行**：TCP **80**（Nginx）
- **关闭**：对 `0.0.0.0/0` 的 TCP **5000**（仅本机访问即可）

```bash
sudo ufw allow 80/tcp
sudo ufw deny 5000/tcp
sudo ufw reload
```

阿里云控制台 → 安全组入方向：同样只开放 80，删除 5000 的公网规则。

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

### 4.0 PM2 报 `gunicorn:2 SyntaxError`（Node 栈）

PM2 把 `venv/bin/gunicorn` 当成 **Node** 脚本执行时会这样。请使用仓库里的 `ecosystem.config.js`：**`script` 为虚拟环境的 `python`，`args` 为 `-m gunicorn ...`**，然后 `pm2 delete fishbowl_trend && pm2 start ecosystem.config.js`。

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