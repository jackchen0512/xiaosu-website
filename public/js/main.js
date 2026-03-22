// 小苏网站 - 前端脚本

// 配置
const API_BASE = '/api';
const ANALYTICS_ENABLED = true;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    initAnalytics();
    loadComments();
    loadBlogPosts();
    setupCommentForm();
});

// 统计系统 - 1x1像素tracker
function initAnalytics() {
    if (!ANALYTICS_ENABLED) return;

    const tracker = document.getElementById('analytics-tracker');
    if (!tracker) return;

    // 生成统计请求
    const params = new URLSearchParams({
        ref: document.referrer || '',
        title: document.title,
        ua: navigator.userAgent,
        t: Date.now()
    });

    // 设置1x1像素图片
    tracker.src = `${API_BASE}/analytics/pixel.png?${params.toString()}`;

    console.log('[Analytics] Tracking enabled');
}

// 加载评论
async function loadComments() {
    const container = document.getElementById('comments-list');
    const placeholder = document.getElementById('comments-placeholder');

    if (!placeholder) return;

    try {
        const response = await fetch(`${API_BASE}/comments`);
        const data = await response.json();

        if (!data.success) {
            container.innerHTML = `<p class="loading">加载失败: ${data.error}</p>`;
            return;
        }

        if (!data.comments || data.comments.length === 0) {
            container.innerHTML = '<p class="loading">暂无留言，快来抢沙发！</p>';
            return;
        }

        // 移除占位符
        placeholder.remove();

        // 渲染评论
        data.comments.forEach(comment => {
            container.appendChild(createCommentElement(comment));
        });

        console.log(`[Comments] Loaded ${data.comments.length} comments`);

    } catch (error) {
        console.error('[Comments] Load error:', error);
        container.innerHTML = '<p class="loading">加载失败，请稍后再试</p>';
    }
}

// 创建评论元素
function createCommentElement(comment) {
    const div = document.createElement('div');
    div.className = 'comment-item';

    const header = document.createElement('div');
    header.className = 'comment-header';

    const name = document.createElement('span');
    name.className = 'comment-name';
    name.textContent = comment.name || '匿名';

    const time = document.createElement('span');
    time.className = 'comment-time';
    time.textContent = formatDate(comment.created_at);

    header.appendChild(name);
    header.appendChild(time);

    const content = document.createElement('div');
    content.className = 'comment-content';
    content.textContent = comment.content;

    div.appendChild(header);
    div.appendChild(content);

    // 如果有回复
    if (comment.reply) {
        const reply = document.createElement('div');
        reply.className = 'comment-reply';

        const replyHeader = document.createElement('div');
        replyHeader.className = 'comment-reply-header';
        replyHeader.textContent = '小苏回复:';

        const replyContent = document.createElement('div');
        replyContent.textContent = comment.reply;

        reply.appendChild(replyHeader);
        reply.appendChild(replyContent);
        div.appendChild(reply);
    }

    return div;
}

// 设置评论表单
function setupCommentForm() {
    const form = document.querySelector('.comment-form');
    const nameInput = document.getElementById('comment-name');
    const contentInput = document.getElementById('comment-content');
    const submitBtn = document.getElementById('submit-comment');

    if (!form || !submitBtn) return;

    submitBtn.addEventListener('click', async () => {
        const name = nameInput.value.trim();
        const content = contentInput.value.trim();

        // 验证
        if (!content) {
            showToast('请输入留言内容', 'error');
            return;
        }

        if (content.length > 500) {
            showToast('留言内容不能超过500字', 'error');
            return;
        }

        // 禁用按钮
        submitBtn.disabled = true;
        submitBtn.textContent = '提交中...';

        try {
            const response = await fetch(`${API_BASE}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name || '匿名',
                    content: content
                })
            });

            const data = await response.json();

            if (!data.success) {
                showToast(`提交失败: ${data.error}`, 'error');
                return;
            }

            // 成功
            showToast('留言成功！小苏会尽快回复', 'success');

            // 清空表单
            nameInput.value = '';
            contentInput.value = '';

            // 重新加载评论
            setTimeout(() => {
                location.reload();
            }, 1000);

        } catch (error) {
            console.error('[Comments] Submit error:', error);
            showToast('网络错误，请稍后再试', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '发表留言';
        }
    });
}

// 加载博客文章
async function loadBlogPosts() {
    const container = document.getElementById('blog-list');
    const placeholder = document.getElementById('blog-placeholder');

    if (!placeholder) return;

    try {
        const response = await fetch(`${API_BASE}/blog`);
        const data = await response.json();

        if (!data.success) {
            container.innerHTML = `<p class="loading">加载失败: ${data.error}</p>`;
            return;
        }

        if (!data.posts || data.posts.length === 0) {
            placeholder.textContent = '暂无文章';
            return;
        }

        // 移除占位符
        placeholder.remove();

        // 渲染文章
        data.posts.forEach(post => {
            container.appendChild(createBlogElement(post));
        });

        console.log(`[Blog] Loaded ${data.posts.length} posts`);

    } catch (error) {
        console.error('[Blog] Load error:', error);
        placeholder.textContent = '加载失败，请稍后再试';
    }
}

// 创建博客文章元素
function createBlogElement(post) {
    const div = document.createElement('div');
    div.className = 'blog-item';

    const title = document.createElement('h3');
    title.textContent = post.title;

    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = `${post.date} · ${post.read_time}`;

    const content = document.createElement('p');
    content.textContent = post.summary || post.excerpt;

    div.appendChild(title);
    div.appendChild(meta);
    div.appendChild(content);

    return div;
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;

    return date.toLocaleDateString('zh-CN');
}

// Toast 提示
function showToast(message, type = 'success') {
    // 移除旧的toast
    const oldToast = document.querySelector('.toast');
    if (oldToast) {
        oldToast.remove();
    }

    // 创建新toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // 3秒后自动消失
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

console.log('[Xiaosu Website] Frontend loaded');
