# -*- coding: utf-8 -*-
"""
趋势报告生成模块 - 生成文本报告和微信推送
"""
import logging
from datetime import datetime
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('trend_reporter')

class TrendReporter:
    """趋势报告生成器"""
    
    def __init__(self, notifier=None):
        self.notifier = notifier
    
    def generate_text_report(self, results, title="鱼盆趋势模型v2.0"):
        """
        生成文本格式报告
        :param results: 分析结果列表
        :param title: 报告标题
        :return: str, 报告文本
        """
        today = datetime.now().strftime('%Y.%m.%d')
        
        # 构建表格数据
        table_data = []
        for result in results:
            # 在状态上添加颜色
            status = '\033[32mYES\033[0m' if result['status'] == 'YES' else '\033[31mNO\033[0m'
            
            # 格式化涨跌幅和偏离率，添加颜色
            price_change = result['price_change_pct']
            price_change_str = f"\033[32m{price_change:+.2f}%\033[0m" if price_change >= 0 else f"\033[31m{price_change:.2f}%\033[0m"
            
            deviation = result['deviation_rate']
            deviation_str = f"\033[32m{deviation:.2f}%\033[0m" if deviation >= 0 else f"\033[31m{deviation:.2f}%\033[0m"
            
            interval_change = result['interval_change_pct']
            interval_change_str = f"\033[32m{interval_change:+.2f}%\033[0m" if interval_change >= 0 else f"\033[31m{interval_change:.2f}%\033[0m"
            
            row = [
                result['rank'],
                result['index_code'],
                result['index_name'],
                status,
                price_change_str,
                result['current_price'],
                result['threshold'],
                deviation_str,
                result['status_change_time'],
                interval_change_str
            ]
            table_data.append(row)
        
        # 表头
        headers = ['趋势\n强度', '代码', '名称', '状态', '涨幅%', '现价', 
                   '临界\n值点', '偏离率%', '状态转\n变时间', '区间涨幅\n%']
        
        # 生成表格
        report = f"{title}    日期: {today}\n"
        report += "数据仅供市场风格趋势分析，不提供投资建议\n\n"
        report += tabulate(table_data, headers=headers, tablefmt='simple', numalign='right', stralign='left')
        
        return report
    
    def generate_simple_report(self, results, summary=None):
        """
        生成简化版报告（适合微信推送）
        :param results: 分析结果列表
        :param summary: 摘要信息
        :return: str
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        report = f"【鱼盆趋势模型 {today}】\n\n"
        
        # 添加摘要信息
        if summary:
            report += f"📊 市场概况\n"
            report += f"总计: {summary['total']}个指数\n"
            report += f"趋势向上(YES): {summary['yes_count']}个\n"
            report += f"趋势向下(NO): {summary['no_count']}个\n"
            
            if summary['new_yes']:
                report += f"\n🔥 新转YES: {', '.join(summary['new_yes'])}\n"
            if summary['new_no']:
                report += f"❄️ 新转NO: {', '.join(summary['new_no'])}\n"
            
            report += "\n" + "="*30 + "\n\n"
        
        # YES状态指数
        yes_indices = [r for r in results if r['status'] == 'YES']
        if yes_indices:
            report += "✅ 趋势向上(YES):\n"
            for r in yes_indices:
                report += f"\n{r['rank']}. {r['index_name']} ({r['index_code']})\n"
                report += f"   现价: {r['current_price']}, 临界值: {r['threshold']}\n"
                report += f"   偏离率: {r['deviation_rate']:.2f}%\n"
                report += f"   区间涨幅: {r['interval_change_pct']:+.2f}%\n"
                report += f"   状态转变时间: {r['status_change_time']}\n"
            report += "\n"
        
        # NO状态指数
        no_indices = [r for r in results if r['status'] == 'NO']
        if no_indices:
            report += "❌ 趋势向下(NO):\n"
            for r in no_indices:
                report += f"\n{r['rank']}. {r['index_name']} ({r['index_code']})\n"
                report += f"   现价: {r['current_price']}, 临界值: {r['threshold']}\n"
                report += f"   偏离率: {r['deviation_rate']:.2f}%\n"
                report += f"   区间跌幅: {r['interval_change_pct']:+.2f}%\n"
                report += f"   状态转变时间: {r['status_change_time']}\n"
        
        return report
    
    def generate_html_report(self, results, title="鱼盆趋势模型v2.0"):
        """
        生成HTML格式报告
        :param results: 分析结果列表
        :param title: 报告标题
        :return: str, HTML文本
        """
        today = datetime.now().strftime('%Y.%m.%d')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 10px 0;
        }}
        .header p {{
            color: #666;
            margin: 5px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-yes {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .status-no {{
            color: #f44336;
            font-weight: bold;
        }}
        .positive {{
            color: #4CAF50;
        }}
        .negative {{
            color: #f44336;
        }}
        .rank {{
            font-weight: bold;
            color: #2196F3;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>日期: {today}</p>
        <p>数据仅供市场风格趋势分析，不提供投资建议</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>趋势强度</th>
                <th>代码</th>
                <th>名称</th>
                <th>状态</th>
                <th>涨幅%</th>
                <th>现价</th>
                <th>临界值点</th>
                <th>偏离率</th>
                <th>状态转变时间</th>
                <th>区间涨幅%</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for result in results:
            status_class = 'status-yes' if result['status'] == 'YES' else 'status-no'
            price_change_class = 'positive' if result['price_change_pct'] >= 0 else 'negative'
            interval_change_class = 'positive' if result['interval_change_pct'] >= 0 else 'negative'
            
            html += f"""
            <tr>
                <td class="rank">{result['rank']}</td>
                <td>{result['index_code']}</td>
                <td>{result['index_name']}</td>
                <td class="{status_class}">{result['status']}</td>
                <td class="{price_change_class}">{result['price_change_pct']:+.2f}%</td>
                <td>{result['current_price']}</td>
                <td>{result['threshold']}</td>
                <td>{result['deviation_rate']:.2f}%</td>
                <td>{result['status_change_time']}</td>
                <td class="{interval_change_class}">{result['interval_change_pct']:+.2f}%</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
</body>
</html>
"""
        return html
    
    def send_wechat_report(self, results, summary=None):
        """发送微信报告"""
        if not self.notifier:
            logger.warning("未配置微信通知器，跳过推送")
            return
        
        try:
            self.notifier.start()
            report = self.generate_simple_report(results, summary)
            
            # 微信消息有长度限制，可能需要分段发送
            max_length = 2000
            if len(report) > max_length:
                # 分段发送
                parts = [report[i:i+max_length] for i in range(0, len(report), max_length)]
                for i, part in enumerate(parts):
                    message = {'content': f"【第{i+1}/{len(parts)}部分】\n{part}"}
                    self.notifier.add_message(message)
                    if i < len(parts) - 1:  # 不是最后一条消息
                        import time
                        time.sleep(60)  # 每条消息间隔1分钟
            else:
                message = {'content': report}
                self.notifier.add_message(message)
            
            import time
            time.sleep(10)
            self.notifier.stop()
            logger.info("趋势报告已推送至微信")
        except Exception as e:
            logger.error(f"微信推送失败: {str(e)}")

