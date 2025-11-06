# -*- coding: utf-8 -*-
"""
简单测试脚本 - 直接测试数据获取API
"""
import requests
import json
import time
from datetime import datetime, timedelta

def test_etf_159857():
    """测试159857光伏ETF数据获取"""
    print("测试159857光伏ETF...")
    
    try:
        # 东方财富ETF接口
        url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        params = {
            'secid': '0.159857',  # 深交所ETF
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',  # 日K
            'fqt': '1',
            'beg': start_date,
            'end': end_date,
            '_': str(int(time.time() * 1000))
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines']
            print(f"✅ 159857光伏ETF数据获取成功，共{len(klines)}条")
            
            # 显示最新几条数据
            for i, kline in enumerate(klines[-3:]):
                parts = kline.split(',')
                print(f"   {parts[0]}: 开盘={parts[1]}, 收盘={parts[2]}, 最高={parts[3]}, 最低={parts[4]}")
            
            return True
        else:
            print(f"❌ 159857光伏ETF数据获取失败: {data}")
            return False
            
    except Exception as e:
        print(f"❌ 159857光伏ETF测试异常: {str(e)}")
        return False

def test_hk_hstech():
    """测试HST00011恒生科技数据获取"""
    print("\n测试HST00011恒生科技...")
    
    try:
        # 雅虎财经接口
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        data = response.json()
        
        if data.get('chart', {}).get('result'):
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            
            valid_data = []
            for i, ts in enumerate(timestamps):
                if quotes['close'][i] is not None:
                    date = datetime.fromtimestamp(ts)
                    valid_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'close': quotes['close'][i],
                        'open': quotes['open'][i],
                        'high': quotes['high'][i],
                        'low': quotes['low'][i]
                    })
            
            if valid_data:
                print(f"✅ HST00011恒生科技数据获取成功，共{len(valid_data)}条")
                
                # 显示最新几条数据
                for item in valid_data[-3:]:
                    print(f"   {item['date']}: 开盘={item['open']:.2f}, 收盘={item['close']:.2f}, "
                          f"最高={item['high']:.2f}, 最低={item['low']:.2f}")
                
                return True
            else:
                print("❌ HST00011恒生科技数据为空")
                return False
        else:
            print(f"❌ HST00011恒生科技数据获取失败: {data}")
            return False
            
    except Exception as e:
        print(f"❌ HST00011恒生科技测试异常: {str(e)}")
        return False

def test_alternative_hk_source():
    """测试备用港股数据源"""
    print("\n测试备用港股数据源...")
    
    try:
        # 新浪港股接口
        url = "https://hq.sinajs.cn/list=rt_hkHSTECH"
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        data = response.text
        
        if 'rt_hkHSTECH=' in data and ',' in data:
            # 解析新浪港股实时数据
            content = data.split('"')[1]
            fields = content.split(',')
            
            if len(fields) > 6:
                print(f"✅ 新浪港股接口获取成功")
                print(f"   指数名称: {fields[0]}")
                print(f"   当前价格: {fields[6]}")
                print(f"   涨跌幅: {fields[8]}%")
                return True
        
        print("❌ 新浪港股接口数据解析失败")
        return False
        
    except Exception as e:
        print(f"❌ 新浪港股接口测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("数据获取API测试")
    print("="*60)
    
    results = []
    
    # 测试ETF
    results.append(test_etf_159857())
    
    # 测试港股
    results.append(test_hk_hstech())
    
    # 测试备用港股源
    results.append(test_alternative_hk_source())
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"成功: {success_count}/{total_count}")
    
    if success_count > 0:
        print("🎉 至少有部分数据源可用！")
    else:
        print("❌ 所有数据源都失败，请检查网络连接")

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")