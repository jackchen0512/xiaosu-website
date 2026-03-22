#!/usr/bin/env python3
"""
GitHub REST API 部署脚本
自动提交代码到GitHub仓库
"""

import os
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

# GitHub配置
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO_OWNER = os.environ.get('GITHUB_USER', 'xiaosu')
REPO_NAME = os.environ.get('GITHUB_REPO', 'xiaosu-website')
REPO_BRANCH = 'main'

API_BASE = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents'

# 需要提交的文件
FILES_TO_DEPLOY = {
    'public/index.html': 'public/index.html',
    'public/css/style.css': 'public/css/style.css',
    'public/js/main.js': 'public/js/main.js',
    'api/app.py': 'api/app.py',
}


class GitHubDeployer:
    """GitHub部署器"""

    def __init__(self, token='', owner='', repo='', branch='main'):
        self.token = token or GITHUB_TOKEN
        self.owner = owner or REPO_OWNER
        self.repo = repo or REPO_NAME
        self.branch = branch
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def get_file_sha(self, path):
        """获取文件的SHA值"""
        url = f'{API_BASE}/{path}'
        params = {'ref': self.branch}

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            return response.json().get('sha')
        elif response.status_code == 404:
            return None  # 文件不存在
        else:
            raise Exception(f'获取文件SHA失败: {response.text}')

    def update_file(self, local_path, remote_path, commit_message=''):
        """更新文件"""
        local_file = Path(local_path)
        if not local_file.exists():
            print(f'❌ 文件不存在: {local_file}')
            return False

        # 读取文件内容
        with open(local_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取SHA
        sha = self.get_file_sha(remote_path)

        # 编码内容（base64）
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        # 准备请求数据
        data = {
            'message': commit_message or f'Update {remote_path}',
            'content': content_base64,
            'branch': self.branch
        }

        if sha:
            data['sha'] = sha

        # 发送请求
        url = f'{API_BASE}/{remote_path}'
        response = requests.put(url, headers=self.headers, json=data)

        if response.status_code in [200, 201]:
            print(f'✅ 更新成功: {remote_path}')
            return True
        else:
            print(f'❌ 更新失败: {remote_path}')
            print(f'   {response.text}')
            return False

    def deploy(self, files_map=None, commit_message=''):
        """批量部署文件"""
        files_map = files_map or FILES_TO_DEPLOY

        if not self.token:
            print('❌ ERROR: GITHUB_TOKEN 环境变量未设置')
            return False

        print(f'🚀 开始部署到 {self.owner}/{self.repo}')
        print(f'📅 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print()

        success_count = 0
        total_count = len(files_map)

        for local_path, remote_path in files_map.items():
            print(f'📤 [{success_count+1}/{total_count}] {remote_path}')

            result = self.update_file(
                local_path=local_path,
                remote_path=remote_path,
                commit_message=f'{commit_message} ({remote_path})'
            )

            if result:
                success_count += 1

            print()

        # 总结
        print('=' * 50)
        print(f'✅ 部署完成！')
        print(f'📊 成功: {success_count}/{total_count}')
        print()

        if success_count == total_count:
            print('🎉 所有文件更新成功！')
        else:
            print('⚠️  部分文件更新失败，请检查日志')

        return success_count == total_count


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='GitHub部署脚本')
    parser.add_argument('--token', help='GitHub Personal Access Token')
    parser.add_argument('--owner', help='仓库所有者')
    parser.add_argument('--repo', help='仓库名称')
    parser.add_argument('--branch', default='main', help='分支名称')
    parser.add_argument('--message', default='Update website', help='提交信息')
    parser.add_argument('--test', action='store_true', help='测试模式（只检查SHA）')

    args = parser.parse_args()

    # 创建部署器
    deployer = GitHubDeployer(
        token=args.token or GITHUB_TOKEN,
        owner=args.owner or REPO_OWNER,
        repo=args.repo or REPO_NAME,
        branch=args.branch
    )

    if args.test:
        # 测试模式：只检查仓库连接
        print('🔍 测试模式：检查仓库连接')
        for local_path, remote_path in FILES_TO_DEPLOY.items():
            sha = deployer.get_file_sha(remote_path)
            status = '✅ 存在' if sha else '❓ 不存在'
            print(f'  {remote_path}: {status}')
    else:
        # 正常部署
        deployer.deploy(
            files_map=FILES_TO_DEPLOY,
            commit_message=args.message
        )


if __name__ == '__main__':
    main()
