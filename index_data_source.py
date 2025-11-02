# -*- coding: utf-8 -*-
"""
指数数据源模块 - 支持获取各类指数行情数据
支持多数据源：东方财富、新浪财经、腾讯财经
"""
import os
import logging
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from market_data_source import MarketDataSource

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/index_data.log'), logging.StreamHandler()]
)
logger = logging.getLogger('index_data_source')

class IndexDataSource:
    """指数数据源"""
    
    def __init__(self):
        self.cache_path = 'data/index_quote'
        os.makedirs(self.cache_path, exist_ok=True)
        self.cache_ttl = 3600  # 缓存1小时
        self.market_data = MarketDataSource()
    
    def get_index_quote(self, index_code, start_date, end_date, force_refresh=False):
        """
        获取指数行情数据
        :param index_code: 指数代码
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param force_refresh: 是否强制刷新
        :return: DataFrame
        """
        # 检查缓存
        cache_file = os.path.join(self.cache_path, f"{index_code}_{end_date.replace('-', '')}.csv")
        if not force_refresh and os.path.exists(cache_file):
            # 检查缓存时间
            cache_time = os.path.getmtime(cache_file)
            if time.time() - cache_time < self.cache_ttl:
                try:
                    df = pd.read_csv(cache_file, parse_dates=['trade_date'])
                    logger.info(f"从缓存加载{index_code}数据，共{len(df)}条")
                    return df
                except Exception as e:
                    logger.warning(f"缓存读取失败: {str(e)}")
        
        # 从数据源获取（优先级：东方财富 -> 新浪 -> 网易）
        df = self._fetch_from_eastmoney(index_code, start_date, end_date)
        if df is None or df.empty:
            logger.warning(f"东方财富获取{index_code}失败，尝试新浪财经")
            df = self._fetch_from_sina(index_code, start_date, end_date)
        if df is None or df.empty:
            logger.warning(f"新浪财经获取{index_code}失败，尝试网易财经")
            df = self._fetch_from_netease(index_code, start_date, end_date)
        
        # 保存缓存
        if df is not None and not df.empty:
            try:
                df.to_csv(cache_file, index=False)
                logger.info(f"{index_code}数据已保存至缓存，共{len(df)}条")
            except Exception as e:
                logger.error(f"保存缓存失败: {str(e)}")
        
        return df if df is not None else pd.DataFrame()
    
    def _fetch_from_eastmoney(self, index_code, start_date, end_date):
        """从东方财富获取指数数据"""
        try:
            # 特殊市场数据处理
            if index_code == 'AUUSDO':  # 伦敦金现
                # 使用华尔街见闻API
                logger.info(f"从华尔街见闻获取{index_code}数据")
                df = self._fetch_from_wsj(index_code, start_date, end_date)
                return df
            elif index_code in ['HSI00001', 'HSCEI00', 'HST00011']:  # 港股指数
                # 使用港股专门API
                logger.info(f"从港股专门API获取{index_code}数据")
                df = self._fetch_from_hk(index_code, start_date, end_date)
                return df
            
            # 常规A股指数代码转换
            if index_code.startswith('399'):  # 深证指数
                em_code = f"0.{index_code}"
            elif index_code.startswith('000'):  # 上证指数
                em_code = f"1.{index_code}"
            elif index_code == '883418':  # 微盘股
                em_code = "1.000852"  # 暂时使用中证1000代替
            elif index_code.startswith('1B0688'):  # 科创50
                em_code = "1.000688"
            elif index_code.startswith('1B0016'):  # 上证50
                em_code = "1.000016"
            elif index_code.startswith('1B0852'):  # 中证1000
                em_code = "1.000852"
            elif index_code == '932000':  # 中证2000
                em_code = "1.000985"
            elif index_code.startswith('88'):  # 北证指数
                em_code = f"0.{index_code}"
            elif index_code.startswith('899'):  # 北证指数
                em_code = f"0.{index_code}"
            else:
                em_code = index_code
            
            url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': em_code,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K
                'fqt': '1',
                'beg': start_date.replace('-', ''),
                'end': end_date.replace('-', ''),
                '_': str(int(time.time() * 1000))
            }
            
            logger.info(f"请求东方财富数据: {index_code} -> {em_code}")
            response = requests.get(url, params=params, timeout=10)
            response.encoding = 'utf-8'
            data = response.json()
            logger.debug(f"东方财富返回数据: {data}")
            
            if data.get('data') and data['data'].get('klines'):
                klines = data['data']['klines']
                records = []
                for kline in klines:
                    parts = kline.split(',')
                    records.append({
                        'trade_date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]) if len(parts) > 5 else 0
                    })
                
                df = pd.DataFrame(records)
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date').reset_index(drop=True)
                logger.info(f"东方财富获取{index_code}数据成功，共{len(df)}条")
                return df
            else:
                logger.warning(f"东方财富返回数据为空: {index_code}")
                return None
            
        except Exception as e:
            logger.error(f"东方财富获取{index_code}失败: {str(e)}")
            return None
    
    def _fetch_from_wsj(self, index_code, start_date, end_date):
        """从雅虎财经获取贵金属数据"""
        try:
            # 使用雅虎财经API获取黄金价格
            symbol = "GC=F"  # 黄金期货代码
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "period1": int(pd.to_datetime(start_date).timestamp()),
                "period2": int(pd.to_datetime(end_date).timestamp()),
                "interval": "1d",
                "includePrePost": "false"
            }
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('chart', {}).get('result'):
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                
                records = []
                for i, ts in enumerate(timestamps):
                    date = datetime.fromtimestamp(ts)
                    records.append({
                        'trade_date': date,
                        'close': quotes['close'][i],
                        'open': quotes['open'][i],
                        'high': quotes['high'][i],
                        'low': quotes['low'][i],
                        'volume': quotes['volume'][i]
                    })
            
            df = pd.DataFrame(records)
            df = df.sort_values('trade_date').reset_index(drop=True)
            logger.info(f"华尔街见闻获取{index_code}数据成功，共{len(df)}条")
            return df
            
        except Exception as e:
            logger.error(f"华尔街见闻获取{index_code}失败: {str(e)}")
            return None
    
    def _fetch_from_hk(self, index_code, start_date, end_date):
        """从雅虎财经获取港股数据"""
        try:
            # 映射指数代码到雅虎财经代码
            yahoo_code_map = {
                'HSI00001': '^HSI',    # 恒生指数
                'HSCEI00': '^HSCE',    # 国企指数
                'HST00011': '^HSTECH'  # 恒生科技
            }
            
            symbol = yahoo_code_map.get(index_code)
            if not symbol:
                logger.error(f"未知的港股指数代码: {index_code}")
                return None
                
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "period1": int(pd.to_datetime(start_date).timestamp()),
                "period2": int(pd.to_datetime(end_date).timestamp()),
                "interval": "1d",
                "includePrePost": "false"
            }
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('chart', {}).get('result'):
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                
                records = []
                for i, ts in enumerate(timestamps):
                    if None in (quotes['close'][i], quotes['open'][i], quotes['high'][i], quotes['low'][i], quotes['volume'][i]):
                        continue
                    date = datetime.fromtimestamp(ts)
                    records.append({
                        'trade_date': date,
                        'close': quotes['close'][i],
                        'open': quotes['open'][i],
                        'high': quotes['high'][i],
                        'low': quotes['low'][i],
                        'volume': quotes['volume'][i]
                    })
            
            df = pd.DataFrame(records)
            df = df.sort_values('trade_date').reset_index(drop=True)
            logger.info(f"雅虎财经获取{index_code}数据成功，共{len(df)}条")
            return df
            
        except Exception as e:
            logger.error(f"雅虎财经获取{index_code}失败: {str(e)}")
            return None
    
    def _fetch_from_sina(self, index_code, start_date, end_date):
        """从新浪财经获取指数数据"""
        try:
            # 新浪代码转换
            if index_code.startswith('399'):
                sina_code = f"sz{index_code}"
            elif index_code.startswith(('000', '1B')):
                sina_code = f"sh{index_code}"
            else:
                sina_code = index_code
            
            url = f"https://finance.sina.com.cn/realstock/company/{sina_code}/hisdata/klc_kl.js"
            
            response = requests.get(url, timeout=10)
            response.encoding = 'gb2312'
            
            # 解析返回数据
            data = response.text
            if not data or 'day_price_year' not in data:
                logger.warning(f"新浪接口返回数据格式错误: {index_code}")
                return None

            try:
                # 提取JSON数据部分
                data = data.split('=')[1].strip()
                if data.endswith(';'):
                    data = data[:-1]
                
                import json
                data = json.loads(data)
                
                records = []
                for item in data:
                    records.append({
                        'trade_date': item['d'],
                        'open': float(item['o']),
                        'close': float(item['c']),
                        'high': float(item['h']),
                        'low': float(item['l']),
                        'volume': float(item['v'])
                    })
                
                df = pd.DataFrame(records)
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                
                # 过滤日期范围
                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)
                df = df[(df['trade_date'] >= start) & (df['trade_date'] <= end)]
                
                df = df.sort_values('trade_date').reset_index(drop=True)
                logger.info(f"新浪财经获取{index_code}数据成功，共{len(df)}条")
                return df
                
            except Exception as e:
                logger.error(f"解析新浪数据失败: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"新浪获取{index_code}失败: {str(e)}")
            return None
    
    def _fetch_from_netease(self, index_code, start_date, end_date):
        """从网易财经获取指数数据"""
        try:
            # 网易代码转换
            if index_code.startswith('399'):
                netease_code = f"0{index_code}"
            elif index_code.startswith(('000', '1B')):
                netease_code = f"1{index_code}"
            else:
                return None
            
            # 计算时间戳
            start_ts = datetime.strptime(start_date, '%Y-%m-%d')
            end_ts = datetime.strptime(end_date, '%Y-%m-%d')
            
            url = f"http://quotes.money.163.com/service/chddata.html"
            params = {
                'code': netease_code,
                'start': start_ts.strftime('%Y%m%d'),
                'end': end_ts.strftime('%Y%m%d'),
                'fields': 'TCLOSE;HIGH;LOW;TOPEN;VOTURNOVER'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.encoding = 'gbk'
            
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # 重命名列
            df.rename(columns={
                '日期': 'trade_date',
                '收盘价': 'close',
                '开盘价': 'open',
                '最高价': 'high',
                '最低价': 'low',
                '成交量': 'volume'
            }, inplace=True)
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date').reset_index(drop=True)
            logger.info(f"网易获取{index_code}数据成功，共{len(df)}条")
            return df
            
        except Exception as e:
            logger.error(f"网易获取{index_code}失败: {str(e)}")
            return None

