/**
 * PM2 进程配置：在项目根目录执行 `pm2 start ecosystem.config.js`
 *
 * 外网访问：Gunicorn 绑定 0.0.0.0:5000 → http://<公网IP>:5000/
 * （云安全组 / 防火墙需放行 TCP 5000；若前面有 Nginx 反代，可改 WEB_BIND 为 127.0.0.1:5000）
 *
 * 可选环境变量（启动前 export 或写在下方 env）：
 *   FISHBOWL_VENV  虚拟环境根目录（含 bin/gunicorn），不设则自动在 .venv / venv 中查找
 *   WEB_BIND       监听地址，默认 0.0.0.0:5000
 *   WEB_WORKERS    worker 数，默认 3
 */
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;

function resolveVenvRoot() {
  if (process.env.FISHBOWL_VENV) {
    return path.resolve(process.env.FISHBOWL_VENV);
  }
  for (const name of ['.venv', 'venv']) {
    const candidate = path.join(ROOT, name);
    const gunicorn = path.join(candidate, 'bin', 'gunicorn');
    if (fs.existsSync(gunicorn)) {
      return candidate;
    }
  }
  return path.join(ROOT, '.venv');
}

const VENV = resolveVenvRoot();
const GUNICORN = path.join(VENV, 'bin', 'gunicorn');
const PYTHON = path.join(VENV, 'bin', 'python');

const WEB_BIND = process.env.WEB_BIND || '0.0.0.0:5000';
const WEB_WORKERS = process.env.WEB_WORKERS || '3';

module.exports = {
  apps: [
    {
      name: 'fishbowl_trend',
      cwd: path.join(ROOT, 'web'),
      script: GUNICORN,
      args: `server:app -b ${WEB_BIND} -w ${WEB_WORKERS}`,
      env: {
        PYTHONPATH: path.join(ROOT, 'web'),
        FLASK_ENV: 'production',
        // main_trend 后台任务 subprocess 使用与当前服务同一解释器
        PYTHON: PYTHON,
      },
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: path.join(ROOT, 'logs', 'pm2-err.log'),
      out_file: path.join(ROOT, 'logs', 'pm2-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
  ],
};
