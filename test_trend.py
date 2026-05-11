# -*- coding: utf-8 -*-
"""
鱼盆趋势模型测试脚本
用于快速测试系统各个模块是否正常工作
"""
import os
import sys
import json
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_trend')

def test_data_source():
    """测试数据源模块"""
    logger.info("=" * 50)
    logger.info("测试数据源模块")
    logger.info("=" * 50)
    
    try:
        from index_data_source import IndexDataSource
        from datetime import datetime, timedelta
        
        ds = IndexDataSource()
        
        # 测试获取沪深300指数数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        logger.info("正在获取沪深300指数数据...")
        df = ds.get_index_quote('399300', start_date, end_date)
        
        if not df.empty:
            logger.info(f"✅ 数据获取成功，共{len(df)}条记录")
            logger.info(f"最新数据: {df.tail(1).to_dict('records')}")
            return True
        else:
            logger.error("❌ 数据获取失败，返回空数据")
            return False
            
    except Exception as e:
        logger.error(f"❌ 数据源测试失败: {str(e)}", exc_info=True)
        return False

def test_ma5_ma10_signal_compute():
    """单元测试：MA5/MA10 金叉死叉与排列（不访问网络）"""
    logger.info("=" * 50)
    logger.info("测试 MA5/MA10 信号计算")
    logger.info("=" * 50)
    try:
        from index_trend_analyzer import _compute_ma5_ma10_signal

        # 金叉：前一日 ma5<=ma10，最新 ma5>ma10
        df_golden = pd.DataFrame({"ma5": [8.0, 10.0], "ma10": [9.0, 8.0]})
        assert _compute_ma5_ma10_signal(df_golden) == "金叉", "金叉"

        # 死叉
        df_death = pd.DataFrame({"ma5": [10.0, 8.0], "ma10": [9.0, 10.0]})
        assert _compute_ma5_ma10_signal(df_death) == "死叉", "死叉"

        # 无交叉：多头
        df_bull = pd.DataFrame({"ma5": [10.0, 11.0], "ma10": [9.0, 9.5]})
        assert _compute_ma5_ma10_signal(df_bull) == "多头", "多头"

        # 无交叉：空头
        df_bear = pd.DataFrame({"ma5": [9.0, 8.0], "ma10": [10.0, 9.0]})
        assert _compute_ma5_ma10_signal(df_bear) == "空头", "空头"

        # 行数不足
        assert _compute_ma5_ma10_signal(pd.DataFrame({"ma5": [1.0]})) == "", "单行应返回空"

        # 缺列
        assert _compute_ma5_ma10_signal(pd.DataFrame({"ma5": [1.0, 2.0]})) == "", "缺 ma10"

        logger.info("✅ MA5/MA10 信号单元测试通过")
        return True
    except AssertionError as e:
        logger.error(f"❌ MA5/MA10 断言失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ MA5/MA10 单元测试异常: {str(e)}", exc_info=True)
        return False


def test_data_source_meta_routing():
    """单元测试：数据源元信息应反映真实命中来源（不误标）"""
    logger.info("=" * 50)
    logger.info("测试数据源元信息路由")
    logger.info("=" * 50)
    try:
        from index_data_source import IndexDataSource

        class MockIndexDataSource(IndexDataSource):
            def _fetch_hk_from_yahoo(self, index_code, start_date, end_date):
                return None

            def _fetch_hk_from_sina(self, index_code, start_date, end_date):
                return None

            def _fetch_hk_from_tencent(self, index_code, start_date, end_date):
                return pd.DataFrame([{
                    'trade_date': pd.to_datetime('2026-05-07'),
                    'open': 1.0, 'high': 1.1, 'low': 0.9, 'close': 1.0, 'volume': 1
                }])

        ds = MockIndexDataSource()
        df = ds.get_index_quote('HSI00001', '2026-01-01', '2026-05-07', force_refresh=True)
        assert not df.empty, "应命中腾讯港股模拟结果"
        meta = ds.get_last_fetch_meta('HSI00001')
        assert meta.get('source') == 'tencent_hk', f"source 误标: {meta}"
        assert meta.get('data_quality') == 'fresh', f"quality 异常: {meta}"
        logger.info("✅ 数据源元信息路由测试通过")
        return True
    except AssertionError as e:
        logger.error(f"❌ 数据源元信息断言失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 数据源元信息测试异常: {str(e)}", exc_info=True)
        return False


def test_hk_no_synthetic_fallback():
    """单元测试：港股仅实时价可用时，不得补造历史数据（宁缺毋滥）"""
    logger.info("=" * 50)
    logger.info("测试港股不补造历史数据")
    logger.info("=" * 50)
    try:
        from index_data_source import IndexDataSource

        class MockIndexDataSource(IndexDataSource):
            def _fetch_hk_from_yahoo(self, index_code, start_date, end_date):
                return None

            def _fetch_hk_from_tencent(self, index_code, start_date, end_date):
                return None

            def _get_sina_hk_current(self, sina_code):
                return {
                    'name': 'mock',
                    'current_price': 100.0,
                    'change_pct': 0.0,
                    'open': 100.0,
                    'high': 101.0,
                    'low': 99.0
                }

            def _get_sina_hk_historical(self, sina_code, start_date, end_date):
                return None

        ds = MockIndexDataSource()
        df = ds.get_index_quote('HSI00001', '2026-01-01', '2026-05-07', force_refresh=True)
        assert df.empty, "仅有实时价时应返回空，不得补造历史数据"
        meta = ds.get_last_fetch_meta('HSI00001')
        assert meta.get('data_quality') == 'missing', f"质量标记应为 missing: {meta}"
        logger.info("✅ 港股不补造历史数据测试通过")
        return True
    except AssertionError as e:
        logger.error(f"❌ 港股不补造历史断言失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 港股不补造历史测试异常: {str(e)}", exc_info=True)
        return False


def test_trend_analyzer():
    """测试趋势分析模块"""
    logger.info("=" * 50)
    logger.info("测试趋势分析模块")
    logger.info("=" * 50)
    
    try:
        from index_data_source import IndexDataSource
        from index_trend_analyzer import IndexTrendAnalyzer
        
        ds = IndexDataSource()
        analyzer = IndexTrendAnalyzer(ds, ma_period=20)
        
        # 测试分析单个指数
        logger.info("正在分析沪深300指数...")
        result = analyzer.analyze_index_trend('399300', '沪深300')
        
        if result:
            logger.info("✅ 趋势分析成功")
            logger.info(f"指数代码: {result['index_code']}")
            logger.info(f"指数名称: {result['index_name']}")
            logger.info(f"趋势状态: {result['status']}")
            logger.info(f"当前价格: {result['current_price']}")
            logger.info(f"临界值: {result['threshold']}")
            logger.info(f"偏离率: {result['deviation_rate']:.2f}%")
            logger.info(f"MA5/MA10: {result.get('ma5_ma10_signal', '')}")
            logger.info(f"区间涨跌幅: {result['interval_change_pct']:+.2f}%")
            return True
        else:
            logger.error("❌ 趋势分析失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 趋势分析测试失败: {str(e)}", exc_info=True)
        return False

def test_reporter():
    """测试报告生成模块"""
    logger.info("=" * 50)
    logger.info("测试报告生成模块")
    logger.info("=" * 50)
    
    try:
        from index_data_source import IndexDataSource
        from index_trend_analyzer import IndexTrendAnalyzer
        from trend_reporter import TrendReporter
        
        ds = IndexDataSource()
        analyzer = IndexTrendAnalyzer(ds, ma_period=20)
        reporter = TrendReporter()
        
        # 分析几个指数
        test_indices = [
            {'code': '399300', 'name': '沪深300'},
            {'code': '399006', 'name': '创业板指'},
            {'code': '000001', 'name': '上证指数'}
        ]
        
        logger.info(f"正在分析{len(test_indices)}个指数...")
        results = analyzer.analyze_all_indices(test_indices)
        
        if results:
            logger.info(f"✅ 分析成功，共{len(results)}个指数")
            
            # 生成文本报告
            report = reporter.generate_text_report(results, title="鱼盆趋势模型测试报告")
            print("\n" + report)
            
            # 保存HTML报告
            html_report = reporter.generate_html_report(results, title="鱼盆趋势模型测试报告")
            test_html_file = 'data/trend_status/test_report.html'
            os.makedirs(os.path.dirname(test_html_file), exist_ok=True)
            with open(test_html_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            logger.info(f"✅ HTML测试报告已保存至: {test_html_file}")
            
            return True
        else:
            logger.error("❌ 报告生成失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 报告生成测试失败: {str(e)}", exc_info=True)
        return False

def test_config():
    """测试配置文件"""
    logger.info("=" * 50)
    logger.info("测试配置文件")
    logger.info("=" * 50)
    
    try:
        config_file = 'config/index_config.json'
        if not os.path.exists(config_file):
            logger.error(f"❌ 配置文件不存在: {config_file}")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"✅ 配置文件加载成功")
        logger.info(f"配置的指数数量: {len(config['indices'])}")
        logger.info(f"均线周期: {config.get('ma_period', 20)}天")
        
        # 显示配置的指数列表
        logger.info("配置的指数列表:")
        for idx in config['indices']:
            logger.info(f"  - {idx['code']}: {idx['name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置文件测试失败: {str(e)}", exc_info=True)
        return False

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("鱼盆趋势模型 - 系统测试")
    print("="*60 + "\n")
    
    results = {
        '配置文件': test_config(),
        '数据源': test_data_source(),
        'MA5/MA10信号': test_ma5_ma10_signal_compute(),
        '数据源元信息': test_data_source_meta_routing(),
        '港股不补造': test_hk_no_synthetic_fallback(),
        '趋势分析': test_trend_analyzer(),
        '报告生成': test_reporter()
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for module, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{module}: {status}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print("🎉 所有测试通过！系统运行正常。")
    else:
        print("⚠️ 部分测试失败，请检查日志。")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程出错: {str(e)}", exc_info=True)
        sys.exit(1)

