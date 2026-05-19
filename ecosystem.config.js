/**
 * PM2 进程配置：在项目根目录执行 `pm2 start ecosystem.config.js`
 *
 * 推荐：Gunicorn 仅本机 127.0.0.1:5000 + Nginx 对外 80（见 deploy/nginx/fishbowl.conf）
 * 访问：http://<公网IP>/ ；安全组只放行 80，勿对公网开放 5000
 *
 * 启动方式：必须用 venv 里的 python 执行 `python -m gunicorn`。
 * 勿把 `bin/gunicorn` 当作 PM2 的 script，否则 PM2 会用 Node 去执行该文件并报 SyntaxError。
 *
 * 可选环境变量（启动前 export）：
 *   FISHBOWL_VENV      虚拟环境根目录，不设则自动在 .venv / venv 中查找
 *   WEB_BIND           默认 127.0.0.1:5000；临时直连可 export WEB_BIND=0.0.0.0:5000
 *   WEB_WORKERS        默认 3
 *   GUNICORN_TIMEOUT   默认 120（秒），避免慢连接占满 worker
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
    const py = path.join(candidate, 'bin', 'python');
    if (fs.existsSync(py)) {
      return candidate;
    }
    const py3 = path.join(candidate, 'bin', 'python3');
    if (fs.existsSync(py3)) {
      return candidate;
    }
  }
  return path.join(ROOT, '.venv');
}

const VENV = resolveVenvRoot();
const PYTHON = fs.existsSync(path.join(VENV, 'bin', 'python'))
  ? path.join(VENV, 'bin', 'python')
  : path.join(VENV, 'bin', 'python3');

const WEB_BIND = process.env.WEB_BIND || '127.0.0.1:5000';
const WEB_WORKERS = process.env.WEB_WORKERS || '3';
const GUNICORN_TIMEOUT = process.env.GUNICORN_TIMEOUT || '300';
const GUNICORN_GRACEFUL_TIMEOUT = process.env.GUNICORN_GRACEFUL_TIMEOUT || '30';
const GUNICORN_KEEPALIVE = process.env.GUNICORN_KEEPALIVE || '5';
const GUNICORN_THREADS = process.env.GUNICORN_THREADS || '4';

module.exports = {
  apps: [
    {
      name: 'fishbowl_trend',
      cwd: path.join(ROOT, 'web'),
      script: PYTHON,
      args: `-m gunicorn server:app -b ${WEB_BIND} -w ${WEB_WORKERS} --worker-class gthread --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT} --keep-alive ${GUNICORN_KEEPALIVE}`,
      interpreter: 'none',
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
