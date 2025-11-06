# -*- coding: utf-8 -*-
"""
测试数据获取脚本
专门测试159857光伏ETF和HST00011恒生科技的数据获取
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_data_fetch')

# 导入数据源
from index_data_source import IndexDataSource

def test_single_index(data_source, index_code, index_name):
    """测试单个指数数据获取"""
    print(f"\n{'='*50}")
    print(f"测试 {index_name} ({index_code})")
    print(f"{'='*50}")
    
    # 设置日期范围（最近30天）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        # 获取数据
        df = data_source.get_index_quote(index_code, start_date, end_date, force_refresh=True)
        
        if df is not None and not df.empty:
            print(f"✅ 数据获取成功！")
            print(f"   数据条数: {len(df)}")
            print(f"   日期范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")
            print(f"   最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"   最新日期: {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')}")
            
            # 显示最近5天数据
            print(f"\n最近5天数据:")
            recent_data = df.tail(5)[['trade_date', 'open', 'high', 'low', 'close', 'volume']]
            for _, row in recent_data.iterrows():
                print(f"   {row['trade_date'].strftime('%Y-%m-%d')}: "
                      f"开盘={row['open']:.2f}, 最高={row['high']:.2f}, "
                      f"最低={row['low']:.2f}, 收盘={row['close']:.2f}, "
                      f"成交量={row['volume']:,.0f}")
            
            return True
        else:
            print(f"❌ 数据获取失败 - 返回空数据")
            return False
            
    except Exception as e:
        print(f"❌ 数据获取异常: {str(e)}")
        logger.error(f"获取{index_code}数据异常", exc_info=True)
        return False

def main():
    """主测试函数"""
    print("开始测试数据获取功能...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建数据源实例
    data_source = IndexDataSource()
    
    # 测试目标指数
    test_cases = [
        ('159857', '光伏ETF'),
        ('HST00011', '恒生科技'),
        ('HSI00001', '恒生指数'),  # 作为对比
        ('399300', '沪深300')     # 作为对比
    ]
    
    results = {}
    
    for index_code, index_name in test_cases:
        success = test_single_index(data_source, index_code, index_name)
        results[index_code] = success
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("测试结果汇总")
    print(f"{'='*50}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for index_code, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        index_name = dict(test_cases)[index_code]
        print(f"{index_name} ({index_code}): {status}")
    
    print(f"\n总体结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查日志")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"测试程序异常: {str(e)}", exc_info=True)
        print(f"❌ 测试程序异常: {str(e)}")