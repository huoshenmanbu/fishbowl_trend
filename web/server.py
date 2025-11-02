from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
import json
import subprocess
import threading
import os
from datetime import datetime
import pytz

# Server sits in fishvowl_trend/web, project root is parent
WEB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_DIR.parent
DATA_PATH = PROJECT_ROOT / 'data' / 'trend_status' / 'latest_trend_result.json'

print(f'''
[STARTUP] Server configuration:
  - WEB_DIR: {WEB_DIR}
  - PROJECT_ROOT: {PROJECT_ROOT}
  - DATA_PATH: {DATA_PATH}
  - DATA_PATH exists: {DATA_PATH.exists()}
''')

app = Flask(__name__, static_folder=str(WEB_DIR), template_folder=str(WEB_DIR))


@app.route('/')
def index():
    return send_from_directory(str(WEB_DIR), 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(str(WEB_DIR), filename)


@app.route('/api/latest')
def api_latest():
    try:
        print(f'[DEBUG] Trying to read data from: {DATA_PATH}')
        if not DATA_PATH.exists():
            error_msg = f'latest_trend_result.json not found at {DATA_PATH}'
            print(f'[ERROR] {error_msg}')
            return jsonify({'ok': False, 'error': error_msg}), 404
        try:
            with DATA_PATH.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 原始数据中的时间就是北京时间，无需转换
            
            print(f'[DEBUG] Successfully read data, update_time: {data.get("update_time")}')
            return jsonify({'ok': True, 'data': data})
        except json.JSONDecodeError as je:
            error_msg = f'JSON parse error: {str(je)}'
            print(f'[ERROR] {error_msg}')
            return jsonify({'ok': False, 'error': error_msg}), 500
        except IOError as io:
            error_msg = f'File read error: {str(io)}'
            print(f'[ERROR] {error_msg}')
            return jsonify({'ok': False, 'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        print(f'[ERROR] {error_msg}')
        return jsonify({'ok': False, 'error': error_msg}), 500


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """If JSON payload has {"run":true} we try to run main_trend.py in background, then return latest JSON if available."""
    payload = request.get_json(silent=True) or {}
    run = bool(payload.get('run'))
    result = {'ok': True, 'triggered_run': run}

    if run:
        main_py = PROJECT_ROOT / 'main_trend.py'
        if not main_py.exists():
            return jsonify({'ok': False, 'error': 'main_trend.py not found', 'path': str(main_py)}), 404

        def run_main():
            try:
                # Set timezone to Asia/Shanghai before running
                os.environ['TZ'] = 'Asia/Shanghai'
                # Respect PYTHON env var if provided, otherwise use default 'python'
                python_exe = os.environ.get('PYTHON', 'python')
                # Set PYTHONIOENCODING to ensure correct character encoding
                my_env = os.environ.copy()
                my_env['PYTHONIOENCODING'] = 'utf-8'
                my_env['TZ'] = 'Asia/Shanghai'
                subprocess.run([python_exe, str(main_py)], 
                            cwd=str(PROJECT_ROOT), 
                            timeout=600,
                            env=my_env)
            except Exception as e:
                print('Error running main_trend.py:', e)

        t = threading.Thread(target=run_main, daemon=True)
        t.start()
        result['message'] = 'started background run of main_trend.py'

    # Return latest data if available
    try:
        if DATA_PATH.exists():
            with DATA_PATH.open('r', encoding='utf-8') as f:
                data = json.load(f)
            result['data'] = data
        else:
            result['data'] = None
    except Exception as e:
        result['ok'] = False
        result['error'] = str(e)

    return jsonify(result)


if __name__ == '__main__':
    host = os.environ.get('WEB_HOST', '0.0.0.0')
    port = int(os.environ.get('WEB_PORT', '5000'))
    # 根据环境变量决定是否开启调试模式
    debug = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
from flask import Flask, send_from_directory, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREND_STATUS_FILE = os.path.join(BASE_DIR, 'data', 'trend_status', 'latest_trend_result.json')

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/get_latest_trend')
def get_latest_trend():
    try:
        with open(TREND_STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 格式化数据以适应前端需求
        formatted_data = {
            "date": datetime.now().strftime("%Y.%m.%d"),
            "trends": []
        }
        
        for item in data:
            formatted_item = {
                "code": item["代码"],
                "name": item["名称"],
                "status": item["状态"],
                "change_percent": item["涨幅%"],
                "current_price": item["现价"],
                "critical_point": item["临界值点"],
                "deviation_rate": item["偏离率%"],
                "range_change": item["区间涨幅%"],
                "strength": item["强度"]
            }
            formatted_data["trends"].append(formatted_item)
        
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)