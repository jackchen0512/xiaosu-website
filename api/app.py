#!/usr/bin/env python3
"""
小苏网站 - Flask API
评论系统 + 博客系统 + 统计接收
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_file, make_response
from functools import wraps
from pathlib import Path

# 配置
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'data' / 'comments.db'
ANALYTICS_LOG = BASE_DIR / 'logs' / 'analytics.jsonl'
BLOG_PATH = BASE_DIR / 'data' / 'blog.json'

# 确保数据目录存在
BASE_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / 'data').mkdir(exist_ok=True)
(BASE_DIR / 'logs').mkdir(exist_ok=True)

app = Flask(__name__)

# 初始化数据库
def init_db():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'approved'
        )
    ''')

    conn.commit()
    conn.close()

# JSON响应装饰器
def json_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            if isinstance(result, tuple):
                data, status_code = result[:2]
            else:
                data, status_code = result, 200

            if not isinstance(data, dict):
                data = {'data': data}

            response = jsonify(data)
            response.status_code = status_code
            return response
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return decorated_function

# ===== 评论系统 =====

@app.route('/api/comments', methods=['GET'])
@json_response
def get_comments():
    """获取所有评论"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, content, reply, created_at
        FROM comments
        WHERE status = 'approved'
        ORDER BY created_at DESC
        LIMIT 100
    ''')

    comments = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'success': True,
        'comments': comments
    }

@app.route('/api/comments', methods=['POST'])
@json_response
def add_comment():
    """添加新评论"""
    data = request.get_json()

    # 验证
    if not data:
        return {
            'success': False,
            'error': '无效的请求数据'
        }, 400

    name = data.get('name', '匿名').strip()
    content = data.get('content', '').strip()

    if not content:
        return {
            'success': False,
            'error': '评论内容不能为空'
        }, 400

    if len(content) > 500:
        return {
            'success': False,
            'error': '评论内容不能超过500字'
        }, 400

    if len(name) > 50:
        name = name[:50]

    # 简单的内容过滤
    forbidden_words = ['广告', '加微信', '代写', '']
    for word in forbidden_words:
        if word in content:
            return {
                'success': False,
                'error': '评论内容包含违禁词'
            }, 400

    # 保存到数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO comments (name, content)
        VALUES (?, ?)
    ''', (name, content))

    conn.commit()
    comment_id = cursor.lastrowid
    conn.close()

    # 记录到日志（用于AI回复触发）
    with open(ANALYTICS_LOG, 'a') as f:
        f.write(json.dumps({
            'type': 'new_comment',
            'comment_id': comment_id,
            'name': name,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }) + '\n')

    return {
        'success': True,
        'comment_id': comment_id
    }

@app.route('/api/comments/<int:comment_id>/reply', methods=['POST'])
@json_response
def reply_comment(comment_id):
    """回复评论（AI调用）"""
    data = request.get_json()

    if not data:
        return {
            'success': False,
            'error': '无效的请求数据'
        }, 400

    reply_content = data.get('reply', '').strip()

    if not reply_content:
        return {
            'success': False,
            'error': '回复内容不能为空'
        }, 400

    # 更新数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE comments
        SET reply = ?
        WHERE id = ?
    ''', (reply_content, comment_id))

    conn.commit()
    conn.close()

    return {
        'success': True
    }

# ===== 博客系统 =====

@app.route('/api/blog', methods=['GET'])
@json_response
def get_blog_posts():
    """获取博客文章列表"""
    if not BLOG_PATH.exists():
        return {
            'success': True,
            'posts': []
        }

    with open(BLOG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return {
        'success': True,
        'posts': data.get('posts', [])
    }

@app.route('/api/blog', methods=['POST'])
@json_response
def add_blog_post():
    """添加博客文章（AI调用）"""
    data = request.get_json()

    if not data:
        return {
            'success': False,
            'error': '无效的请求数据'
        }, 400

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    summary = data.get('summary', '').strip()

    if not title or not content:
        return {
            'success': False,
            'error': '标题和内容不能为空'
        }, 400

    # 加载现有数据
    if BLOG_PATH.exists():
        with open(BLOG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {'posts': []}

    # 创建新文章
    post = {
        'id': len(data['posts']) + 1,
        'title': title,
        'content': content,
        'summary': summary[:200],
        'created_at': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'read_time': f"{len(content) // 500 + 1} 分钟"
    }

    data['posts'].insert(0, post)

    # 保存
    with open(BLOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        'success': True,
        'post_id': post['id']
    }

# ===== 统计系统 =====

@app.route('/api/analytics/pixel.png')
def analytics_pixel():
    """1x1像素统计tracker"""
    # 创建1x1透明PNG
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    response = make_response(png_data)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

    # 记录访问日志
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'referrer': request.args.get('ref', '')[:500],
            'title': request.args.get('title', '')[:200],
            'user_agent': request.args.get('ua', '')[:500],
            'ip': request.remote_addr,
            'path': request.path
        }

        with open(ANALYTICS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        app.logger.error(f'Analytics logging error: {e}')

    return response

@app.route('/api/analytics/stats')
@json_response
def get_analytics_stats():
    """获取统计数据"""
    if not ANALYTICS_LOG.exists():
        return {
            'success': True,
            'stats': {
                'total_visits': 0,
                'unique_visitors': 0,
                'last_update': datetime.now().isoformat()
            }
        }

    # 解析日志
    visits = []
    unique_ips = set()

    try:
        with open(ANALYTICS_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                if 'type' in data:  # 跳过新评论日志
                    continue
                visits.append(data)
                if 'ip' in data:
                    unique_ips.add(data['ip'])
    except Exception as e:
        app.logger.error(f'Analytics parse error: {e}')

    # 简单统计
    today = datetime.now().strftime('%Y-%m-%d')
    today_visits = len([v for v in visits if v.get('timestamp', '').startswith(today)])

    return {
        'success': True,
        'stats': {
            'total_visits': len(visits),
            'unique_visitors': len(unique_ips),
            'today_visits': today_visits,
            'last_update': datetime.now().isoformat()
        }
    }

# ===== 健康检查 =====

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if DB_PATH.exists() else 'not initialized'
    })

# ===== 主程序 =====

if __name__ == '__main__':
    init_db()

    print('🎯 小苏网站 API 启动')
    print(f'📁 数据库: {DB_PATH}')
    print(f'📋 日志: {ANALYTICS_LOG}')
    print('🚀 服务器运行中...')

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
