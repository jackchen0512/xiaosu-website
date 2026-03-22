#!/usr/bin/env python3
"""
统计日志解析脚本
解析analytics.jsonl生成UV/PV统计
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# 配置
BASE_DIR = Path(__file__).parent.parent
ANALYTICS_LOG = BASE_DIR / 'logs' / 'analytics.jsonl'
REPORTS_DIR = BASE_DIR / 'reports'
ANALYTICS_JSON = REPORTS_DIR / 'analytics.json'


class AnalyticsParser:
    """统计日志解析器"""

    def __init__(self, log_path=ANALYTICS_LOG):
        self.log_path = log_path
        self.records = []
        self.stats = {}

    def load_logs(self):
        """加载日志"""
        if not self.log_path.exists():
            print(f'❌ 日志文件不存在: {self.log_path}')
            return False

        print(f'📋 加载日志: {self.log_path}')

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # 跳过非访问日志（如新评论）
                    if 'type' in data:
                        continue
                    self.records.append(data)
                except json.JSONDecodeError:
                    continue

        print(f'✅ 加载了 {len(self.records)} 条记录')
        return True

    def parse(self):
        """解析统计"""
        if not self.records:
            print('❌ 没有记录可解析')
            return

        # 初始化统计
        stats = {
            'total_visits': len(self.records),
            'unique_visitors': 0,
            'daily_visits': defaultdict(int),
            'daily_unique': defaultdict(set),
            'referrers': defaultdict(int),
            'paths': defaultdict(int),
            'last_update': datetime.now().isoformat()
        }

        unique_ips = set()

        for record in self.records:
            # 提取时间
            timestamp = record.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp)
                date = dt.strftime('%Y-%m-%d')
            except:
                date = 'unknown'

            # 提取IP（唯一访客）
            ip = record.get('ip', 'unknown')
            unique_ips.add(ip)
            stats['daily_unique'][date].add(ip)

            # 每日访问量
            stats['daily_visits'][date] += 1

            # 来源统计
            referrer = record.get('referrer', '')[:200]
            if referrer:
                # 简化来源（只显示域名）
                if referrer.startswith('http'):
                    referrer = referrer.split('/')[2]
                stats['referrers'][referrer] += 1

            # 路径统计
            path = record.get('path', '/')[:100]
            stats['paths'][path] += 1

        # 汇总
        stats['unique_visitors'] = len(unique_ips)
        stats['daily_unique'] = {k: len(v) for k, v in stats['daily_unique'].items()}

        self.stats = stats

    def print_stats(self):
        """打印统计"""
        print()
        print('=' * 50)
        print('📊 访问统计')
        print('=' * 50)
        print()

        # 总体统计
        print(f'总访问量 (PV): {self.stats["total_visits"]}')
        print(f'独立访客 (UV): {self.stats["unique_visitors"]}')
        print()

        # 每日统计
        print('📅 每日访问:')
        sorted_days = sorted(self.stats['daily_visits'].items())
        for date, visits in sorted_days[-7:]:  # 最近7天
            unique = self.stats['daily_unique'].get(date, 0)
            print(f'  {date}: PV={visits}, UV={unique}')
        print()

        # 来源统计（前10）
        print('🌐 主要来源 (Top 10):')
        sorted_refs = sorted(self.stats['referrers'].items(),
                            key=lambda x: x[1], reverse=True)
        for ref, count in sorted_refs[:10]:
            print(f'  {ref or "直接访问"}: {count}')
        print()

        # 页面统计
        print('📄 热门页面:')
        sorted_paths = sorted(self.stats['paths'].items(),
                             key=lambda x: x[1], reverse=True)
        for path, count in sorted_paths[:5]:
            print(f'  {path}: {count}')

    def save_report(self):
        """保存报告"""
        REPORTS_DIR.mkdir(exist_ok=True)

        # 转换defaultdict为普通dict
        stats = dict(self.stats)
        stats['daily_visits'] = dict(stats['daily_visits'])
        stats['daily_unique'] = dict(stats['daily_unique'])
        stats['referrers'] = dict(stats['referrers'])
        stats['paths'] = dict(stats['paths'])

        with open(ANALYTICS_JSON, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print()
        print(f'✅ 报告已保存: {ANALYTICS_JSON}')


def main():
    """命令行入口"""
    parser = AnalyticsParser()

    # 加载
    if not parser.load_logs():
        return

    # 解析
    parser.parse()

    # 打印
    parser.print_stats()

    # 保存
    parser.save_report()


if __name__ == '__main__':
    main()
