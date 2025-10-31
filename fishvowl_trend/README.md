# 鱼盆趋势模型 v2.0

## 📊 项目简介

鱼盆趋势模型是一个基于20日均线的指数趋势分析系统，用于实时监控各大市场指数的趋势状态。系统通过计算指数现价与20日均线（临界值）的关系，判断指数趋势方向（YES/NO），并计算偏离率等关键指标。

### 核心功能

- ✅ **实时趋势分析**：基于20日均线判断指数YES/NO状态
- ✅ **偏离率计算**：量化现价与临界值的偏离程度
- ✅ **状态转换追踪**：记录并监控状态变化时间点
- ✅ **区间涨跌幅**：计算状态转换后的价格变化
- ✅ **多格式报告**：支持文本、HTML、微信推送
- ✅ **数据缓存**：本地缓存行情数据，提高分析效率

### 系统特点

- 🎯 **专注信号分析**：不涉及交易操作，纯趋势判断
- 📈 **多指数支持**：支持沪深港美等多个市场指数
- 🔄 **自动数据获取**：多数据源冗余（东方财富、新浪、网易）
- 📱 **微信推送**：可选的微信消息推送功能
- 💾 **历史追踪**：自动保存历史状态，追踪趋势变化

## 🚀 快速开始

### 1. 安装依赖

```bash
cd fishvowl_trend
pip install -r requirements.txt
```

### 2. 配置指数列表

编辑 `config/index_config.json`，添加或修改要监控的指数：

```json
{
  "indices": [
    {"code": "1B0688", "name": "科创50"},
    {"code": "399300", "name": "沪深300"},
    {"code": "399006", "name": "创业板指"}
  ],
  "ma_period": 20
}
```

### 3. 运行分析

```bash
# 基本分析（保存结果）
python main_trend.py --task analyze

# 生成文本报告（控制台输出）
python main_trend.py --task report --output console

# 生成文本报告（保存文件）
python main_trend.py --task report --output file

# 生成HTML报告
python main_trend.py --task html

# 推送至微信（需配置微信通知器）
python main_trend.py --task push

# 强制刷新数据
python main_trend.py --task analyze --force-refresh
```

## 📖 核心概念

### 状态定义

- **YES**：现价 ≥ 临界值（20日均线），趋势向上
- **NO**：现价 < 临界值（20日均线），趋势向下

### 关键指标

1. **临界值**：20日均线，作为判断趋势的基准线
2. **偏离率**：`(现价 - 临界值) / 临界值 × 100%`
   - 正值：现价高于均线，偏离率越大趋势越强
   - 负值：现价低于均线，偏离率越小（绝对值越大）趋势越弱
3. **区间涨跌幅**：从状态转换时的价格到当前价格的涨跌幅

### 趋势强度排序

系统按以下规则排序：
1. YES状态的指数排在前面
2. YES状态内部按偏离率降序（偏离率越大越强）
3. NO状态按偏离率升序（偏离率越小越弱）

## 📁 项目结构

```
fishvowl_trend/
├── main_trend.py              # 主程序入口
├── index_data_source.py       # 指数数据获取模块
├── index_trend_analyzer.py    # 趋势分析核心模块
├── trend_reporter.py          # 报告生成模块
├── requirements.txt           # 依赖包列表
├── README.md                  # 项目说明文档
├── config/
│   └── index_config.json      # 指数配置文件
├── data/
│   ├── index_quote/           # 行情数据缓存
│   └── trend_status/          # 趋势状态历史
│       ├── latest_trend_result.json
│       ├── trend_status_history.json
│       ├── trend_report_YYYYMMDD.txt
│       └── trend_report_YYYYMMDD.html
└── logs/
    ├── main_trend.log         # 主程序日志
    ├── index_data.log         # 数据获取日志
    └── trend_analyzer.log     # 趋势分析日志
```

## 🔧 配置说明

### index_config.json

```json
{
  "indices": [
    {"code": "指数代码", "name": "指数名称"}
  ],
  "ma_period": 20,
  "update_schedule": {
    "weekday": "Monday-Friday",
    "time": "21:30"
  },
  "notification": {
    "wechat_enabled": true,
    "email_enabled": false
  }
}
```

### 支持的指数代码

- **沪市指数**：`000001`（上证指数）、`1B0016`（上证50）、`1B0688`（科创50）等
- **深市指数**：`399001`（深证成指）、`399006`（创业板指）、`399300`（沪深300）等
- **北证指数**：`899050`（北证50）
- **港股指数**：`HSI`（恒生指数）、`HSCEI`（国企指数）、`HS2083`（恒生科技）

## 📊 输出示例

### 文本报告示例

```
鱼盆趋势模型v2.0    日期: 2025.10.30
数据仅供市场风格趋势分析，不提供投资建议

+--------+--------+----------+------+--------+------+----------+--------+----------+------------+
| 趋势   | 代码   | 名称     | 状态 | 涨幅%  | 现价 | 临界     | 偏离率 | 状态转   | 区间涨幅   |
| 强度   |        |          |      |        |      | 值点     |        | 变时间   | %          |
+========+========+==========+======+========+======+==========+========+==========+============+
|   1    | 1B0688 | 科创50   | YES  | -4.26% | 1410 | 1400     | 0.71%  | 25.7.8   | 42.28%     |
|   2    | 1B0016 | 上证50   | YES  | -0.21% | 2961 | 2953     | 0.27%  | 25.9.29  | -0.40%     |
|   3    | 399300 | 沪深300  | NO   | -1.20% | 4539 | 4551     | -0.26% | 25.8.4   | 11.52%     |
+--------+--------+----------+------+--------+------+----------+--------+----------+------------+
```

### JSON结果示例

```json
{
  "update_time": "2025-10-30 21:30:00",
  "summary": {
    "total": 10,
    "yes_count": 4,
    "no_count": 6,
    "new_yes": ["科创50"],
    "new_no": []
  },
  "results": [
    {
      "rank": 1,
      "index_code": "1B0688",
      "index_name": "科创50",
      "status": "YES",
      "price_change_pct": -4.26,
      "current_price": 1410,
      "threshold": 1400,
      "deviation_rate": 0.71,
      "status_change_time": "2025.7.8",
      "interval_change_pct": 42.28,
      "update_time": "2025-10-30 21:30:00"
    }
  ]
}
```

## 🔌 微信推送配置

如果需要微信推送功能，需要先配置原 fishvowl 项目中的 `wechat_notifier.py`。

1. 确保 `../fishvowl/wechat_notifier.py` 存在
2. 在 `config/index_config.json` 中启用微信推送：
   ```json
   {
     "notification": {
       "wechat_enabled": true
     }
   }
   ```
3. 运行推送命令：
   ```bash
   python main_trend.py --task push
   ```

## 🛠️ 开发说明

### 添加新的数据源

编辑 `index_data_source.py`，在 `IndexDataSource` 类中添加新的数据获取方法：

```python
def _fetch_from_new_source(self, index_code, start_date, end_date):
    """从新数据源获取数据"""
    # 实现数据获取逻辑
    pass
```

### 自定义分析指标

编辑 `index_trend_analyzer.py`，在 `analyze_index_trend` 方法中添加新的计算逻辑。

## ⚠️ 注意事项

1. **数据准确性**：本系统依赖第三方数据源，数据可能存在延迟或误差
2. **仅供参考**：系统生成的信号仅供市场趋势分析，不构成投资建议
3. **网络依赖**：首次运行或缓存过期时需要联网获取数据
4. **缓存管理**：数据缓存1小时，如需实时数据请使用 `--force-refresh`

## 📝 更新日志

### v2.0 (2025-10-30)
- ✨ 初始版本发布
- ✅ 实现基于20日均线的趋势判断
- ✅ 支持多种输出格式（文本、HTML、JSON）
- ✅ 集成微信推送功能
- ✅ 多数据源支持

## 📄 许可证

本项目仅供个人学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请通过 Issue 反馈。

