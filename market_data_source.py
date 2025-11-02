# -*- coding: utf-8 -*-
"""
市场数据源模块 - 支持获取贵金属、港股等数据
"""
import logging
import pandas as pd
import requests
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('market_data_source')

class MarketDataSource:
    """市场数据源"""

    @staticmethod
    def get_metals_quote(code):
        """获取贵金属行情"""
        try:
            # 使用新浪财经的黄金数据接口
            url = "https://hq.sinajs.cn/"
            headers = {
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0"
            }
            params = {
                "list": f"gds_{code.lower()}"
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.encoding = 'gbk'
            data = response.text
            
            # 解析新浪数据格式：var hq_str_gds_au9999="黄金,285.50,285.45,285.50,285.55,285.45,..."
            if data and 'hq_str_gds_' in data:
                price_str = data.split('"')[1].split(',')[1]
                return float(price_str)
            return None
        except Exception as e:
            logger.error(f"获取贵金属{code}价格失败: {str(e)}")
            return None

    @staticmethod
    def get_hk_quote(code):
        """获取港股行情"""
        try:
            # 使用新浪财经的港股数据接口
            url = "https://hq.sinajs.cn/"
            headers = {
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0"
            }
            params = {
                "list": f"rt_hk{code}"
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.encoding = 'gbk'
            data = response.text
            
            if data and ',' in data:
                fields = data.split(',')
                current_price = float(fields[6])  # 当前价格在第7个字段
                return current_price
            return None
        except Exception as e:
            logger.error(f"获取港股{code}价格失败: {str(e)}")
            return None

    @staticmethod
    def get_cn_quote(code):
        """获取A股行情"""
        try:
            # 使用腾讯证券的API获取A股数据
            prefix = "sh" if code.startswith(('000', '1B', '883')) else "sz"
            url = "http://qt.gtimg.cn/q="
            params = {"q": f"{prefix}{code}"}
            response = requests.get(url, params=params, timeout=10)
            data = response.text
            
            # 解析新浪港股数据格式：var hq_str_rt_hkXXXXXX="名称,今开,昨收,最新,最高,最低,..."
            if data and 'hq_str_rt_hk' in data:
                fields = data.split('"')[1].split(',')
                if len(fields) > 3:
                    return float(fields[3])
            return None
            
            if 'hq_str_rt_hk' in data:
                fields = data.split('"')[1].split(',')
                if len(fields) > 3:
                    return float(fields[3])
            return None
            return None
        except Exception as e:
            logger.error(f"获取A股{code}价格失败: {str(e)}")
            return None