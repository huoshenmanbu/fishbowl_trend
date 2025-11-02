# 🚀 快速开始指南

## 第一步：安装依赖

```bash
cd /Users/RichChu/SourceCode/personal/fishvowl_trend
pip install -r requirements.txt
```

## 第二步：测试系统

```bash
# 运行测试脚本，验证所有模块是否正常
python test_trend.py
```

测试脚本会自动检查：
- ✅ 配置文件是否正确
- ✅ 数据源能否正常获取数据
- ✅ 趋势分析模块是否工作
- ✅ 报告生成是否正常

## 第三步：运行分析

### 方式一：基础分析（推荐新手）

```bash
# 分析所有配置的指数，并保存结果
python main_trend.py --task analyze
```

结果保存在：`data/trend_status/latest_trend_result.json`

### 方式二：生成文本报告

```bash
# 在控制台显示报告
python main_trend.py --task report --output console

# 保存报告到文件
python main_trend.py --task report --output file

# 同时显示并保存
python main_trend.py --task report --output both
```

### 方式三：生成HTML报告（推荐）

```bash
# 生成美观的HTML报告
python main_trend.py --task html
```

生成后在浏览器打开：`data/trend_status/trend_report_YYYYMMDD.html`

### 方式四：微信推送

```bash
# 推送到微信（需要配置微信通知器）
python main_trend.py --task push
```

## 常用命令速查

```bash
# 强制刷新数据（不使用缓存）
python main_trend.py --task analyze --force-refresh

# 生成HTML报告并在浏览器查看
python main_trend.py --task html && open data/trend_status/trend_report_*.html

# 查看最新分析结果
cat data/trend_status/latest_trend_result.json | python -m json.tool
```

## 配置自己的指数列表

编辑 `config/index_config.json`：

```json
{
  "indices": [
    {"code": "399300", "name": "沪深300"},
    {"code": "399006", "name": "创业板指"},
    {"code": "000001", "name": "上证指数"}
  ],
  "ma_period": 20
}
```

常用指数代码：
- `000001` - 上证指数
- `399001` - 深证成指
- `399006` - 创业板指
- `399300` - 沪深300
- `399905` - 中证500
- `1B0016` - 上证50
- `1B0688` - 科创50
- `1B0852` - 中证1000

## 定时自动运行（可选）

### macOS/Linux (使用crontab)

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天21:30执行）
30 21 * * * cd /Users/RichChu/SourceCode/personal/fishvowl_trend && /usr/bin/python main_trend.py --task analyze >> logs/cron.log 2>&1
```

### 使用GitHub Actions

在项目根目录创建 `.github/workflows/trend_analysis.yml`：

```yaml
name: 趋势分析

on:
  schedule:
    - cron: '30 13 * * 1-5'  # UTC时间13:30，北京时间21:30，周一到周五
  workflow_dispatch:  # 支持手动触发

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run analysis
        run: |
          python main_trend.py --task analyze
      - name: Generate report
        run: |
          python main_trend.py --task html
```

## 结果解读

### YES状态（趋势向上）
- 现价 ≥ 20日均线
- 偏离率为正值，数值越大趋势越强
- 适合关注上涨机会

### NO状态（趋势向下）
- 现价 < 20日均线
- 偏离率为负值，绝对值越大趋势越弱
- 建议谨慎或观望

### 关键指标
- **偏离率**：衡量价格偏离均线的程度
- **区间涨跌幅**：从状态转换后的价格变化
- **状态转变时间**：趋势改变的时间点

## 故障排查

### 问题1：数据获取失败

```bash
# 检查网络连接
ping api.eastmoney.com

# 查看详细错误日志
tail -f logs/index_data.log
```

### 问题2：依赖安装失败

```bash
# 升级pip
pip install --upgrade pip

# 使用国内源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题3：没有生成报告

```bash
# 检查是否有分析结果
ls -la data/trend_status/

# 手动运行分析
python main_trend.py --task analyze --force-refresh
```

## 获取帮助

```bash
# 查看所有可用选项
python main_trend.py --help

# 查看日志
tail -f logs/main_trend.log
```

## 下一步

- 📖 阅读 [README.md](README.md) 了解更多细节
- 🔧 根据需要修改 `config/index_config.json`
- 📊 定期运行分析，跟踪市场趋势
- 💡 结合自己的交易策略使用信号

## 重要提示

⚠️ 本系统仅提供趋势分析信号，不构成投资建议。投资有风险，决策需谨慎。

