module.exports = {
  apps: [{
    name: "fishbowl_trend",
    cwd: "./fishvowl_trend/web",
    script: "../venv/bin/gunicorn",
    args: "server:app -b 127.0.0.1:5000 -w 3",
    interpreter: "../venv/bin/python",
    env: {
      "PYTHONPATH": ".",
      "FLASK_ENV": "production"
    },
    exec_mode: "fork",
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: "500M",
    error_file: "../logs/err.log",
    out_file: "../logs/out.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss"
  }]
}