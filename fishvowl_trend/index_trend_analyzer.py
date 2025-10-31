# -*- coding: utf-8 -*-
"""
渔盆趋势模型 - 指数趋势分析核心模块
基于20日均线判断指数YES/NO状态，计算偏离率和状态转换
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/trend_analyzer.log'), logging.StreamHandler()]
)
logger = logging.getLogger('index_trend_analyzer')

class IndexTrendAnalyzer:
    """指数趋势分析器"""
    
    def __init__(self, data_source, ma_period=20):
        """
        初始化趋势分析器
        :param data_source: 数据源实例
        :param ma_period: 均线周期，默认20日
        """
        self.data_source = data_source
        self.ma_period = ma_period
        self.status_path = 'data/trend_status'
        os.makedirs(self.status_path, exist_ok=True)
        
        # 加载历史状态
        self.history_status = self._load_history_status()
    
    def _load_history_status(self):
        """加载历史状态记录"""
        status_file = os.path.join(self.status_path, 'trend_status_history.json')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载历史状态失败: {str(e)}")
                return {}
        return {}
    
    def _save_history_status(self):
        """保存历史状态记录"""
        status_file = os.path.join(self.status_path, 'trend_status_history.json')
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_status, f, ensure_ascii=False, indent=2)
            logger.info(f"历史状态已保存")
        except Exception as e:
            logger.error(f"保存历史状态失败: {str(e)}")
    
    def analyze_index_trend(self, index_code, index_name, rank=None, force_refresh=False):
        """
        分析单个指数的趋势状态
        :param index_code: 指数代码
        :param index_name: 指数名称
        :param rank: 趋势强度排名（可选）
        :param force_refresh: 是否强制刷新行情缓存
        :return: dict, 包含状态、偏离率等信息
        """
        try:
            # 获取指数行情数据（最近90天，确保有足够数据计算20日均线）
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            quote_df = self.data_source.get_index_quote(index_code, start_date, end_date, force_refresh=force_refresh)
            
            if quote_df.empty or len(quote_df) < self.ma_period:
                logger.warning(f"{index_name}({index_code})数据不足，当前{len(quote_df)}条，需要{self.ma_period}条")
                return None
            
            # 计算20日均线作为临界值
            quote_df['ma20'] = quote_df['close'].rolling(window=self.ma_period).mean()
            
            # 过滤掉均线为NaN的行
            quote_df = quote_df[quote_df['ma20'].notna()]
            
            if quote_df.empty:
                logger.warning(f"{index_name}({index_code})计算均线后无有效数据")
                return None
            
            # 获取最新数据
            latest = quote_df.iloc[-1]
            current_price = latest['close']
            threshold = latest['ma20']  # 临界值
            
            # 判断状态：现价 >= 临界值 为 YES，否则为 NO
            current_status = 'YES' if current_price >= threshold else 'NO'
            
            # 计算偏离率：(现价 - 临界值) / 临界值 * 100%
            deviation_rate = ((current_price - threshold) / threshold) * 100
            
            # 计算涨幅百分比（与前一交易日相比）
            if len(quote_df) >= 2:
                prev_close = quote_df.iloc[-2]['close']
                price_change_pct = ((current_price - prev_close) / prev_close) * 100
            else:
                price_change_pct = 0
            
            # 检查状态转换
            prev_status_info = self.history_status.get(index_code, {})
            prev_status = prev_status_info.get('status', None)
            status_change_time = prev_status_info.get('status_change_time', None)
            status_change_price = prev_status_info.get('status_change_price', current_price)
            
            # 如果状态发生变化，更新转换时间和价格
            if prev_status and prev_status != current_status:
                status_change_time = datetime.now().strftime('%Y.%m.%d').replace('.0', '.')
                status_change_price = current_price
                logger.info(f"{index_name}状态变化: {prev_status} -> {current_status}，价格: {current_price}")
            elif not prev_status:
                # 首次记录
                status_change_time = datetime.now().strftime('%Y.%m.%d').replace('.0', '.')
                status_change_price = current_price
            
            # 计算区间涨幅（从状态转换时的价格到现在）
            if status_change_price and status_change_price > 0:
                interval_change_pct = ((current_price - status_change_price) / status_change_price) * 100
            else:
                interval_change_pct = 0
            
            # 构建结果
            result = {
                'rank': rank if rank is not None else 0,
                'index_code': index_code,
                'index_name': index_name,
                'status': current_status,
                'price_change_pct': round(price_change_pct, 2),
                'current_price': round(current_price, 2),
                'threshold': round(threshold, 2),
                'deviation_rate': round(deviation_rate, 2),
                'status_change_time': status_change_time if status_change_time else datetime.now().strftime('%Y.%m.%d').replace('.0', '.'),
                'interval_change_pct': round(interval_change_pct, 2),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 更新历史状态
            self.history_status[index_code] = {
                'status': current_status,
                'status_change_time': status_change_time if status_change_time else datetime.now().strftime('%Y.%-m.%-d'),
                'status_change_price': status_change_price
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析{index_name}({index_code})趋势失败: {str(e)}", exc_info=True)
            return None
    
    def analyze_all_indices(self, index_list, force_refresh=False):
        """
        批量分析所有指数
        :param index_list: 指数列表 [{'code': 'xxx', 'name': 'xxx'}, ...]
        :param force_refresh: 是否强制刷新行情缓存
        :return: list, 分析结果列表
        """
        results = []
        for index_info in index_list:
            result = self.analyze_index_trend(index_info['code'], index_info['name'], force_refresh=force_refresh)
            if result:
                results.append(result)
        
        # 保存历史状态
        self._save_history_status()
        
        # 按趋势强度排序
        # YES状态的按偏离率降序（偏离率越大越强）
        # NO状态的按偏离率升序（偏离率越小（负值越大）越弱）
        results.sort(key=lambda x: (x['status'] == 'NO', -x['deviation_rate']))
        
        # 添加排名
        for i, result in enumerate(results, 1):
            result['rank'] = i
        
        return results
    
    def get_status_change_summary(self, results):
        """
        获取状态变化摘要
        :param results: 分析结果列表
        :return: dict, 摘要信息
        """
        yes_count = len([r for r in results if r['status'] == 'YES'])
        no_count = len([r for r in results if r['status'] == 'NO'])
        
        # 找出新转YES和新转NO的指数
        new_yes = []
        new_no = []
        
        for result in results:
            index_code = result['index_code']
            current_status = result['status']
            
            # 检查是否是今天转换的
            status_change_time = result.get('status_change_time', '')
            today = datetime.now().strftime('%Y.%m.%d').replace('.0', '.')
            
            if status_change_time == today:
                if current_status == 'YES':
                    new_yes.append(result['index_name'])
                else:
                    new_no.append(result['index_name'])
        
        return {
            'total': len(results),
            'yes_count': yes_count,
            'no_count': no_count,
            'new_yes': new_yes,
            'new_no': new_no
        }

