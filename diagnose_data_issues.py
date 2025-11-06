# -*- coding: utf-8 -*-
"""
数据问题诊断脚本
专门诊断159857光伏ETF和HST00011恒生科技的数据获取问题
"""
import os
import sys
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('diagnose')

def create_directories():
    """创建必要的目录"""
    dirs = ['data', 'data/index_quote', 'data/trend_status', 'logs']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ 目录创建: {dir_path}")

def test_network_connectivity():
    """测试网络连接"""
    print("\n" + "="*50)
    print("测试网络连接")
    print("="*50)
    
    test_urls = [
        "http://push2his.eastmoney.com",
        "https://query1.finance.yahoo.com", 
        "https://hq.sinajs.cn",
        "http://web.ifzq.gtimg.cn"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - 错误: {str(e)}")

def test_eastmoney_etf_api():
    """测试东方财富ETF接口"""
    print("\n" + "="*50)
    print("测试东方财富ETF接口 (159857)")
    print("="*50)
    
    try:
        url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        params = {
            'secid': '0.159857',
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',
            'fqt': '1',
            'beg': start_date,
            'end': end_date,
            '_': str(int(datetime.now().timestamp() * 1000))
        }
        
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        
        response = requests.get(url, params=params, timeout=15)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            if data.get('data') and data['data'].get('klines'):
                klines = data['data']['klines']
                print(f"✅ 获取到{len(klines)}条K线数据")
                
                # 显示前3条数据
                for i, kline in enumerate(klines[:3]):
                    parts = kline.split(',')
                    print(f"   数据{i+1}: 日期={parts[0]}, 开盘={parts[1]}, 收盘={parts[2]}")
                
                return True
            else:
                print(f"❌ 数据结构异常: {data}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 接口测试异常: {str(e)}")
        logger.exception("东方财富ETF接口测试异常")
        return False

def test_yahoo_hk_api():
    """测试雅虎财经港股接口"""
    print("\n" + "="*50)
    print("测试雅虎财经港股接口 (HST00011)")
    print("="*50)
    
    try:
        symbol = "^HSTECH"
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=30)).timestamp())
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "includePrePost": "false"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        print(f"请求头: {headers}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            if data.get('chart', {}).get('result'):
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                
                valid_count = sum(1 for i in range(len(timestamps)) if quotes['close'][i] is not None)
                print(f"✅ 获取到{len(timestamps)}条数据，其中{valid_count}条有效")
                
                # 显示最新3条有效数据
                valid_data = []
                for i, ts in enumerate(timestamps):
                    if quotes['close'][i] is not None:
                        date = datetime.fromtimestamp(ts)
                        valid_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'close': quotes['close'][i],
                            'open': quotes['open'][i]
                        })
                
                for item in valid_data[-3:]:
                    print(f"   {item['date']}: 开盘={item['open']:.2f}, 收盘={item['close']:.2f}")
                
                return True
            else:
                print(f"❌ 数据结构异常: {data}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 接口测试异常: {str(e)}")
        logger.exception("雅虎财经港股接口测试异常")
        return False

def test_sina_hk_api():
    """测试新浪港股接口"""
    print("\n" + "="*50)
    print("测试新浪港股接口 (HST00011)")
    print("="*50)
    
    try:
        # 测试实时数据接口
        url = "https://hq.sinajs.cn/list=rt_hkHSTECH"
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print(f"请求URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应编码: {response.encoding}")
        
        if response.status_code == 200:
            response.encoding = 'utf-8'
            data = response.text
            print(f"响应内容长度: {len(data)}")
            print(f"响应内容预览: {data[:200]}")
            
            if 'rt_hkHSTECH=' in data and ',' in data:
                content = data.split('"')[1]
                fields = content.split(',')
                print(f"✅ 解析到{len(fields)}个字段")
                
                if len(fields) > 6:
                    print(f"   指数名称: {fields[0]}")
                    print(f"   当前价格: {fields[6]}")
                    if len(fields) > 8:
                        print(f"   涨跌幅: {fields[8]}%")
                    return True
            else:
                print("❌ 数据格式不符合预期")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 接口测试异常: {str(e)}")
        logger.exception("新浪港股接口测试异常")
        return False

def test_data_source_integration():
    """测试数据源集成"""
    print("\n" + "="*50)
    print("测试数据源集成")
    print("="*50)
    
    try:
        # 导入数据源模块
        from index_data_source import IndexDataSource
        
        data_source = IndexDataSource()
        print("✅ 数据源模块导入成功")
        
        # 测试159857
        print("\n测试159857光伏ETF集成...")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        df = data_source.get_index_quote('159857', start_date, end_date, force_refresh=True)
        if df is not None and not df.empty:
            print(f"✅ 159857数据获取成功，共{len(df)}条")
            print(f"   最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"   最新日期: {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')}")
        else:
            print("❌ 159857数据获取失败")
        
        # 测试HST00011
        print("\n测试HST00011恒生科技集成...")
        df = data_source.get_index_quote('HST00011', start_date, end_date, force_refresh=True)
        if df is not None and not df.empty:
            print(f"✅ HST00011数据获取成功，共{len(df)}条")
            print(f"   最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"   最新日期: {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')}")
        else:
            print("❌ HST00011数据获取失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据源集成测试异常: {str(e)}")
        logger.exception("数据源集成测试异常")
        return False

def main():
    """主诊断函数"""
    print("数据问题诊断工具")
    print("="*60)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建目录
    create_directories()
    
    # 测试网络连接
    test_network_connectivity()
    
    # 测试各个API
    results = []
    results.append(("东方财富ETF接口", test_eastmoney_etf_api()))
    results.append(("雅虎财经港股接口", test_yahoo_hk_api()))
    results.append(("新浪港股接口", test_sina_hk_api()))
    results.append(("数据源集成", test_data_source_integration()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("诊断结果汇总")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(success for _, success in results)
    total_count = len(results)
    
    print(f"\n总体结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！数据获取功能正常")
    elif success_count > 0:
        print("⚠️ 部分测试通过，数据获取功能部分可用")
    else:
        print("❌ 所有测试失败，请检查网络连接和防火墙设置")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"诊断程序异常: {str(e)}", exc_info=True)
        print(f"❌ 诊断程序异常: {str(e)}")
    
    input("\n按回车键退出...")