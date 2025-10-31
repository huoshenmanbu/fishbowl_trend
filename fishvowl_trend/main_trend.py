# -*- coding: utf-8 -*-
"""
鱼盆趋势模型主程序
实时分析各大指数趋势，生成YES/NO状态报告
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime

# 创建日志目录
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/main_trend.log'), logging.StreamHandler()]
)
logger = logging.getLogger('main_trend')

# 导入模块
from index_data_source import IndexDataSource
from index_trend_analyzer import IndexTrendAnalyzer
from trend_reporter import TrendReporter

# 可选：导入原有的微信通知器
WECHAT_AVAILABLE = False
try:
    # 尝试从父目录导入微信通知器
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(parent_dir, 'fishvowl'))
    from wechat_notifier import WechatNotifier
    WECHAT_AVAILABLE = True
    logger.info("微信通知器加载成功")
except Exception as e:
    logger.warning(f"微信通知器不可用: {str(e)}")

def load_index_config():
    """加载指数配置"""
    config_file = 'config/index_config.json'
    if not os.path.exists(config_file):
        logger.error(f"配置文件{config_file}不存在")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"配置加载成功，共{len(config['indices'])}个指数")
        return config
    except Exception as e:
        logger.error(f"配置加载失败: {str(e)}")
        return None

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='鱼盆趋势模型 - 实时信号分析系统')
    parser.add_argument('--task', default='analyze', 
                       choices=['analyze', 'report', 'push', 'html'],
                       help='任务类型: analyze-分析并保存, report-生成文本报告, push-推送微信, html-生成HTML报告')
    parser.add_argument('--output', default='console',
                       choices=['console', 'file', 'both'],
                       help='输出方式: console-控制台, file-文件, both-两者都输出')
    parser.add_argument('--force-refresh', action='store_true',
                       help='强制刷新数据，忽略缓存')
    args = parser.parse_args()
    
    logger.info("="*50)
    logger.info(f"鱼盆趋势模型启动 - 任务类型: {args.task}")
    logger.info("="*50)
    
    # 加载配置
    config = load_index_config()
    if not config:
        logger.error("配置加载失败，程序退出")
        return
    
    # 初始化组件
    logger.info("初始化数据源...")
    data_source = IndexDataSource()
    
    logger.info("初始化趋势分析器...")
    analyzer = IndexTrendAnalyzer(data_source, ma_period=config.get('ma_period', 20))
    
    notifier = None
    if WECHAT_AVAILABLE and config.get('notification', {}).get('wechat_enabled', False):
        logger.info("初始化微信通知器...")
        notifier = WechatNotifier()
    
    reporter = TrendReporter(notifier)
    
    # 执行分析
    logger.info(f"开始分析{len(config['indices'])}个指数...")
    results = analyzer.analyze_all_indices(config['indices'])
    
    if not results:
        logger.error("分析失败，无结果")
        return
    
    logger.info(f"分析完成，共{len(results)}个指数有效")
    
    # 获取摘要信息
    summary = analyzer.get_status_change_summary(results)
    logger.info(f"市场概况: YES={summary['yes_count']}, NO={summary['no_count']}")
    if summary['new_yes']:
        logger.info(f"新转YES: {', '.join(summary['new_yes'])}")
    if summary['new_no']:
        logger.info(f"新转NO: {', '.join(summary['new_no'])}")
    
    # 根据任务类型处理结果
    if args.task == 'analyze':
        # 仅分析，保存结果
        result_file = 'data/trend_status/latest_trend_result.json'
        os.makedirs(os.path.dirname(result_file), exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': summary,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"分析结果已保存至{result_file}")
        
        # 输出文本报告到控制台
        print("\n" + reporter.generate_text_report(results, title="鱼盆趋势模型v2.0"))
    
    elif args.task == 'report':
        # 生成文本报告
        report = reporter.generate_text_report(results)
        
        if args.output in ['console', 'both']:
            print("\n" + report)
        
        if args.output in ['file', 'both']:
            report_file = f"data/trend_status/trend_report_{datetime.now().strftime('%Y%m%d')}.txt"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存至{report_file}")
    
    elif args.task == 'html':
        # 生成HTML报告
        html_report = reporter.generate_html_report(results)
        html_file = f"data/trend_status/trend_report_{datetime.now().strftime('%Y%m%d')}.html"
        os.makedirs(os.path.dirname(html_file), exist_ok=True)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        logger.info(f"HTML报告已保存至{html_file}")
        
        if args.output == 'console':
            print(f"\nHTML报告已生成: {html_file}")
            print("请在浏览器中打开查看")
    
    elif args.task == 'push':
        # 推送微信
        if not WECHAT_AVAILABLE:
            logger.error("微信通知器不可用，无法推送")
            print("❌ 微信通知器不可用，请检查配置")
            return
        
        if not config.get('notification', {}).get('wechat_enabled', False):
            logger.warning("微信推送未启用")
            print("⚠️ 微信推送未启用，请在配置文件中启用")
            return
        
        logger.info("开始推送微信报告...")
        reporter.send_wechat_report(results, summary)
        logger.info("微信推送完成")
        print("✅ 微信推送完成")
    
    logger.info("程序执行完成")
    print("\n✅ 任务执行完成!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("\n⚠️ 程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
        print(f"\n❌ 程序执行出错: {str(e)}")
        sys.exit(1)

