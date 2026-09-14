#!/usr/bin/env python3
"""
模拟靶机应用
包含常见Web漏洞用于安全测试
运行端口: 5000 (独立于主系统)
"""
from flask import Flask, request, render_template_string, render_template, jsonify, redirect, url_for, session, send_file
import base64
import json
import sqlite3
import os
import subprocess
import pickle
import hashlib
import re

app = Flask(__name__)
app.secret_key = 'vulnerable_secret_key_12345'  # 硬编码密钥 (漏洞)

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'vulndb.db')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
FLAGS_DIR = os.path.join(DATA_DIR, 'flags')
SECRET_DIR = os.path.join(os.path.dirname(__file__), 'secrets')
SUPPORT_DIR = os.path.join(DATA_DIR, 'support')
OPS_DIR = os.path.join(DATA_DIR, 'ops')
WORKFLOW_DIR = os.path.join(DATA_DIR, 'workflows')
PLUGINS_DIR = os.path.join(DATA_DIR, 'plugins')
REPLAY_DIR = os.path.join(DATA_DIR, 'replay')
RESTORE_ENV_PATH = os.path.join(BACKUP_DIR, 'restore.env')
FINAL_FLAG_PATH = os.path.join(BACKUP_DIR, 'final.flag')
OPS_BUNDLE_SEED_PATH = os.path.join(OPS_DIR, 'bundle.seed')
WORKFLOW_PREVIEW_SEED_PATH = os.path.join(WORKFLOW_DIR, 'preview.seed')
PLUGIN_IMPORT_SEED_PATH = os.path.join(PLUGINS_DIR, 'import.seed')
REPLAY_STATE_SEED_PATH = os.path.join(REPLAY_DIR, 'state.seed')
BACKUP_CHALLENGE = 'root-admin'
VULN_FLAGS = {
    'sqli': 'FLAG{sqli_query_breakout}',
    'cmdi': 'FLAG{command_injection_shell}',
    'xss': 'FLAG{stored_xss_payload}',
    'traversal': 'FLAG{path_traversal_file_read}',
    'upload': 'FLAG{unrestricted_file_upload}',
    'ssrf': 'FLAG{ssrf_internal_access}',
    'deserialize': 'FLAG{unsafe_deserialization}',
    'xxe': 'FLAG{xxe_entity_disclosure}',
    'info': 'FLAG{debug_information_leak}',
    'signed_export': 'FLAG{predictable_signed_export}',
    'chain': 'FLAG{full_chain_compromise}',
    'ops_console': 'FLAG{signed_ops_ssti_chain}',
    'workflow_preview': 'FLAG{cve_style_workflow_preview_chain}',
    'plugin_hotfix': 'FLAG{cve_style_plugin_hotfix_chain}',
    'report_replay': 'FLAG{cve_style_signed_report_replay}',
}
FINAL_CHAIN_FLAG = VULN_FLAGS['chain']
LOCAL_ONLY_ADDRESSES = {'127.0.0.1', '::1'}
INTERNAL_FETCH_HEADER = hashlib.sha256(f"{app.secret_key}:internal-fetch".encode()).hexdigest()[:20]
EXPORT_SIGNING_KEY = 'legacy-support-export-2026'

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(FLAGS_DIR, exist_ok=True)
os.makedirs(SECRET_DIR, exist_ok=True)
os.makedirs(SUPPORT_DIR, exist_ok=True)
os.makedirs(OPS_DIR, exist_ok=True)
os.makedirs(WORKFLOW_DIR, exist_ok=True)
os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(REPLAY_DIR, exist_ok=True)


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_challenge_files():
    """创建高难度链式挑战所需的本地文件。"""
    with open(RESTORE_ENV_PATH, 'w') as f:
        f.write(
            '# Internal restore manifest - do not expose externally\n'
            'RESTORE_SALT=ops-night-restore-2026\n'
            'RESTORE_OWNER=root-admin\n'
            'RESTORE_SERVICE=backup-restore\n'
        )

    with open(FINAL_FLAG_PATH, 'w') as f:
        f.write(FINAL_CHAIN_FLAG + '\n')

    with open(os.path.join(FLAGS_DIR, 'command_injection.flag'), 'w') as f:
        f.write(VULN_FLAGS['cmdi'] + '\n')

    with open(os.path.join(SECRET_DIR, 'path_traversal.flag'), 'w') as f:
        f.write(VULN_FLAGS['traversal'] + '\n')

    with open(os.path.join(FLAGS_DIR, 'xxe.flag'), 'w') as f:
        f.write(VULN_FLAGS['xxe'] + '\n')

    with open(os.path.join(SUPPORT_DIR, 'triage-notes.txt'), 'w') as f:
        f.write(
            'Support export - triage notes\n'
            'case=SR-1182\n'
            'status=archived\n'
            f'{VULN_FLAGS["signed_export"]}\n'
        )

    with open(OPS_BUNDLE_SEED_PATH, 'w') as f:
        f.write(
            'OPS_BUNDLE_SEED=ops-template-sign-2026\n'
            'OPS_QUEUE=nightly-reindex\n'
            'OPS_MODE=legacy-preview\n'
        )

    with open(WORKFLOW_PREVIEW_SEED_PATH, 'w') as f:
        f.write(
            'WORKFLOW_PREVIEW_SEED=workflow-preview-sign-2026\n'
            'WORKFLOW_JOB=asset-preview\n'
            'WORKFLOW_ENGINE=legacy-jinja-preview\n'
        )

    with open(PLUGIN_IMPORT_SEED_PATH, 'w') as f:
        f.write(
            'PLUGIN_IMPORT_SEED=plugin-hotfix-sign-2026\n'
            'PLUGIN_CHANNEL=stable-hotfix\n'
            'PLUGIN_FORMAT=manifest-v2\n'
        )

    with open(REPLAY_STATE_SEED_PATH, 'w') as f:
        f.write(
            'REPLAY_STATE_SEED=report-replay-sign-2026\n'
            'REPLAY_STREAM=nightly-delta\n'
            'REPLAY_MODE=state-restore\n'
        )


def get_restore_nonce():
    """基于靶机配置生成固定挑战值，便于通过内部接口获取。"""
    seed = f"{app.secret_key}:{BACKUP_CHALLENGE}:{os.path.basename(DATABASE)}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def get_restore_salt():
    """从泄露的恢复配置中读取盐值。"""
    with open(RESTORE_ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('RESTORE_SALT='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('restore salt not found')


def build_restore_ticket(nonce, salt, challenge):
    raw = f"{nonce}:{salt}:{challenge}"
    return hashlib.sha256(raw.encode()).hexdigest()


def build_export_signature(username, report_name):
    raw = f"{username}:{report_name}:{EXPORT_SIGNING_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_ops_queue():
    return 'nightly-reindex'


def get_ops_nonce():
    seed = f"{app.secret_key}:{get_ops_queue()}:ops-console"
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def get_ops_bundle_seed():
    with open(OPS_BUNDLE_SEED_PATH, 'r') as f:
        for line in f:
            if line.startswith('OPS_BUNDLE_SEED='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('ops bundle seed not found')


def build_ops_bundle_signature(operator, queue_name, nonce, bundle_seed):
    raw = f"{operator}:{queue_name}:{nonce}:{bundle_seed}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_workflow_job_name():
    return 'asset-preview'


def get_workflow_preview_nonce():
    seed = f"{app.secret_key}:{get_workflow_job_name()}:workflow-preview"
    return hashlib.sha256(seed.encode()).hexdigest()[:24]


def get_workflow_preview_seed():
    with open(WORKFLOW_PREVIEW_SEED_PATH, 'r') as f:
        for line in f:
            if line.startswith('WORKFLOW_PREVIEW_SEED='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('workflow preview seed not found')


def build_workflow_preview_signature(operator, job_name, nonce, template_name, preview_seed):
    raw = f"{operator}:{job_name}:{nonce}:{template_name}:{preview_seed}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_plugin_channel():
    return 'stable-hotfix'


def get_plugin_nonce():
    seed = f"{app.secret_key}:{get_plugin_channel()}:plugin-hotfix"
    return hashlib.sha256(seed.encode()).hexdigest()[:18]


def get_plugin_import_seed():
    with open(PLUGIN_IMPORT_SEED_PATH, 'r') as f:
        for line in f:
            if line.startswith('PLUGIN_IMPORT_SEED='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('plugin import seed not found')


def build_plugin_import_signature(operator, channel, nonce, manifest_name, import_seed):
    raw = f"{operator}:{channel}:{nonce}:{manifest_name}:{import_seed}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_replay_stream():
    return 'nightly-delta'


def get_replay_nonce():
    seed = f"{app.secret_key}:{get_replay_stream()}:report-replay"
    return hashlib.sha256(seed.encode()).hexdigest()[:22]


def get_replay_state_seed():
    with open(REPLAY_STATE_SEED_PATH, 'r') as f:
        for line in f:
            if line.startswith('REPLAY_STATE_SEED='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError('replay state seed not found')


def build_replay_state_signature(operator, stream_name, nonce, state_digest, replay_seed):
    raw = f"{operator}:{stream_name}:{nonce}:{state_digest}:{replay_seed}"
    return hashlib.sha256(raw.encode()).hexdigest()


def build_replay_state_digest(raw_state):
    return hashlib.sha256(raw_state.encode()).hexdigest()


def read_final_flag():
    with open(FINAL_FLAG_PATH, 'r') as f:
        return f.read().strip()


def is_local_request():
    forwarded = request.headers.get('X-Forwarded-For', '')
    remote_addr = request.remote_addr or ''
    source = forwarded.split(',', 1)[0].strip() if forwarded else remote_addr
    return source in LOCAL_ONLY_ADDRESSES


def is_internal_fetch():
    return request.headers.get('X-From-Fetcher') == INTERNAL_FETCH_HEADER


def looks_like_sqli(value):
    lowered = (value or '').lower()
    markers = ["'", '--', '/*', ' union ', ' select ', ' or ', 'sqlite_master']
    return any(marker in lowered for marker in markers)


def looks_like_xss(value):
    lowered = (value or '').lower()
    markers = ['<script', 'onerror=', 'onload=', 'javascript:', '<svg', '<img']
    return any(marker in lowered for marker in markers)


def is_dangerous_upload(filename):
    _, ext = os.path.splitext((filename or '').lower())
    return ext in {'.php', '.phtml', '.jsp', '.jspx', '.asp', '.aspx', '.py', '.sh', '.pl'}


ensure_challenge_files()


def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            api_key TEXT
        )
    ''')
    
    # 文章表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            author_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # 产品表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            image TEXT
        )
    ''')
    
    # 日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入默认数据
    try:
        # 默认管理员 (密码: admin123)
        cursor.execute('''
            INSERT INTO users (username, password, email, role, api_key)
            VALUES ('admin', '0192023a7bbd73250516f069df18b500', 'admin@vulnlab.local', 'admin', 'sk-admin-api-key-2024')
        ''')
        # 普通用户
        cursor.execute('''
            INSERT INTO users (username, password, email, role, api_key)
            VALUES ('user', 'ee11cbb19052e40b07aac8ca0c42b8a9', 'user@vulnlab.local', 'user', 'sk-user-api-key-2024')
        ''')
        # 测试用户
        cursor.execute('''
            INSERT INTO users (username, password, email, role, api_key)
            VALUES ('test', '098f6bcd4621d373cade4e832627b4f6', 'test@vulnlab.local', 'user', 'sk-test-api-key-2024')
        ''')
        
        # 示例文章
        cursor.execute('''
            INSERT INTO posts (title, content, author_id) 
            VALUES ('Welcome to VulnLab', 'This is a vulnerable web application for security testing.', 1)
        ''')
        
        # 示例产品
        cursor.execute('''
            INSERT INTO products (name, description, price) 
            VALUES ('Security Scanner', 'Advanced vulnerability scanner tool', 99.99)
        ''')
        cursor.execute('''
            INSERT INTO products (name, description, price) 
            VALUES ('Penetration Testing Guide', 'Comprehensive pentest methodology', 49.99)
        ''')
        
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # 数据已存在
    
    conn.close()


# ==================== 模板 ====================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - VulnLab</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
        .header { background: #16213e; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { color: #e94560; }
        .nav a { color: #eee; text-decoration: none; margin-left: 20px; padding: 8px 15px; background: #0f3460; border-radius: 5px; }
        .nav a:hover { background: #e94560; }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        .card { background: #16213e; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .card h2 { color: #e94560; margin-bottom: 15px; }
        .btn { background: #e94560; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #c73e54; }
        input, textarea, select { width: 100%; padding: 10px; margin: 10px 0; background: #0f3460; border: 1px solid #0f3460; color: #eee; border-radius: 5px; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .alert-success { background: #10b981; }
        .alert-danger { background: #ef4444; }
        .alert-info { background: #3b82f6; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .badge-danger { background: #ef4444; }
        .badge-success { background: #10b981; }
        .footer { text-align: center; padding: 20px; color: #666; margin-top: 50px; }
        pre { background: #0f3460; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #0f3460; }
        th { background: #0f3460; }
        .flag { background: #10b981; padding: 5px 10px; border-radius: 5px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 VulnLab</h1>
        <div class="nav">
            <a href="/">首页</a>
            <a href="/login">登录</a>
            <a href="/register">注册</a>
            <a href="/posts">文章</a>
            <a href="/products">产品</a>
            <a href="/tools">工具</a>
            <a href="/admin">管理</a>
            {% if session.get('user') %}
            <a href="/logout">退出 ({{ session.get('user') }})</a>
            {% endif %}
        </div>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    <div class="footer">
        <p>VulnLab - 模拟靶机 | 仅用于安全测试</p>
    </div>
</body>
</html>
'''


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页"""
    content = '''
    <div class="card">
        <h2>欢迎来到 VulnLab 靶场</h2>
        <p>这是一个包含多个历史模块的测试环境。</p>
        <p>应用包含认证、内容、工具、API、管理与支持相关功能。</p>
        <p>部分功能由旧版本保留，仅用于安全测试。</p>
    </div>
    <div class="card">
        <h2>环境说明</h2>
        <p>访问地址: <code>http://127.0.0.1:5000</code></p>
        <p>请自行完成环境验证。</p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='首页', session=session)


# ==================== SQL注入漏洞 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面 - 存在SQL注入"""
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # 计算MD5
        password_md5 = hashlib.md5(password.encode()).hexdigest()
        
        # 漏洞: SQL注入
        conn = get_db()
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password_md5}'"
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                session['user'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                error = "用户名或密码错误"
        except Exception as e:
            error = f"错误: {str(e)}"
        finally:
            conn.close()
    
    content = '''
    <div class="card">
        <h2>用户登录</h2>
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="用户名" required>
            <input type="password" name="password" placeholder="密码" required>
            <button type="submit" class="btn">登录</button>
        </form>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='登录', error=error, session=session)


@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    message = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        
        # 计算MD5
        password_md5 = hashlib.md5(password.encode()).hexdigest()
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?)", 
                          (username, password_md5))
            conn.commit()
            message = "注册成功！请登录"
        except sqlite3.IntegrityError:
            message = "用户名已存在"
        finally:
            conn.close()
    
    content = '''
    <div class="card">
        <h2>用户注册</h2>
        {% if message %}
        <div class="alert alert-info">{{ message }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="用户名" required>
            <input type="password" name="password" placeholder="密码" required>
            <input type="email" name="email" placeholder="邮箱">
            <button type="submit" class="btn">注册</button>
        </form>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='注册', message=message, session=session)


@app.route('/dashboard')
def dashboard():
    """用户仪表板"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    content = f'''
    <div class="card">
        <h2>欢迎, {session.get('user')}!</h2>
        <p>角色: {session.get('role')}</p>
        <p>已建立有效会话，可继续尝试其他漏洞点。</p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='仪表板', session=session)


@app.route('/support/export')
def support_export():
    """支持中心导出 - 使用可预测签名令牌，属于中等难度漏洞。"""
    if 'user' not in session:
        return redirect(url_for('login'))

    report_name = request.args.get('file', 'triage-notes.txt')
    signature = request.args.get('sig', '')
    expected = build_export_signature(session.get('user', ''), report_name)

    if signature != expected:
        content = '''
        <div class="card">
            <h2>支持中心导出</h2>
            <p>签名校验失败。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='支持中心', session=session), 403

    report_path = os.path.join(SUPPORT_DIR, report_name)
    try:
        with open(report_path, 'r') as f:
            exported = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='导出文件不存在')

    content = '''
    <div class="card">
        <h2>支持中心导出</h2>
        <pre>{{ exported }}</pre>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                  title='支持中心', exported=exported, session=session)


# ==================== 存储型XSS ====================

@app.route('/posts')
def posts():
    """文章列表 - 存在存储型XSS"""
    conn = get_db()
    cursor = conn.cursor()
    
    # SQL注入点
    search = request.args.get('search', '')
    if search:
        query = f"SELECT p.*, u.username FROM posts p JOIN users u ON p.author_id = u.id WHERE p.title LIKE '%{search}%' OR p.content LIKE '%{search}%'"
    else:
        query = "SELECT p.*, u.username FROM posts p JOIN users u ON p.author_id = u.id ORDER BY p.created_at DESC"
    
    try:
        cursor.execute(query)
        posts_list = cursor.fetchall()
    except:
        posts_list = []
    finally:
        conn.close()
    
    sqli_flag_html = ''
    if search and looks_like_sqli(search):
        sqli_flag_html = f'''
        <div class="card">
            <h3>验证结果</h3>
            <p><span class="flag">{VULN_FLAGS["sqli"]}</span></p>
        </div>
        '''

    posts_html = ''
    xss_flag_detected = False
    for post in posts_list:
        if looks_like_xss(post['content']):
            xss_flag_detected = True
        posts_html += f'''
        <div class="card">
            <h3>{post['title']}</h3>
            <p>作者: {post['username']}</p>
            <div>{post['content']}</div>
        </div>
        '''
    
    xss_flag_html = ''
    if xss_flag_detected:
        xss_flag_html = f'''
        <div class="card">
            <h3>验证结果</h3>
            <p><span class="flag">{VULN_FLAGS["xss"]}</span></p>
        </div>
        '''

    content = f'''
    <div class="card">
        <h2>文章列表</h2>
        <form method="GET">
            <input type="text" name="search" placeholder="搜索文章..." value="{search}">
            <button type="submit" class="btn">搜索</button>
        </form>
    </div>
    {sqli_flag_html}
    {xss_flag_html}
    {posts_html}
    <div class="card">
        <h3>发布新文章</h3>
        <form method="POST" action="/posts/create">
            <input type="text" name="title" placeholder="标题" required>
            <textarea name="content" rows="5" placeholder="内容 (支持HTML)"></textarea>
            <button type="submit" class="btn">发布</button>
        </form>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='文章', session=session)


@app.route('/posts/create', methods=['POST'])
def create_post():
    """创建文章"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (session['user'],))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)", 
                      (title, content, user['id']))
        conn.commit()
    conn.close()
    
    return redirect(url_for('posts'))


# ==================== 命令注入 ====================

@app.route('/tools')
def tools():
    """工具页面"""
    content = '''
    <div class="card">
        <h2>系统工具</h2>
        <ul>
            <li><a href="/tools/ping">Ping 测试</a></li>
            <li><a href="/tools/fetch">URL 获取</a></li>
            <li><a href="/upload">文件上传</a></li>
            <li><a href="/files">文件浏览</a></li>
        </ul>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='工具', session=session)


@app.route('/tools/ping', methods=['GET', 'POST'])
def ping():
    """Ping工具 - 存在命令注入"""
    result = None
    
    if request.method == 'POST':
        host = request.form.get('host', '')
        # 漏洞: 命令注入
        command = f"ping -c 4 {host}"
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            result = e.output
        except Exception as e:
            result = str(e)
    
    content = '''
    <div class="card">
        <h2>Ping 网络测试</h2>
        <form method="POST">
            <input type="text" name="host" placeholder="输入IP或域名" required>
            <button type="submit" class="btn">Ping</button>
        </form>
        {% if result %}
        <h3 style="margin-top: 20px;">结果:</h3>
        <pre>{{ result }}</pre>
        {% endif %}
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='Ping', result=result, session=session)


# ==================== SSRF ====================

import requests as http_requests

@app.route('/tools/fetch', methods=['GET', 'POST'])
def fetch_url():
    """URL获取 - 存在SSRF"""
    content_result = None
    error = None
    
    if request.method == 'POST':
        url = request.form.get('url', '')
        try:
            # 漏洞: SSRF, 没有URL验证
            resp = http_requests.get(
                url,
                timeout=10,
                headers={'X-From-Fetcher': INTERNAL_FETCH_HEADER}
            )
            content_result = resp.text[:5000]
        except Exception as e:
            error = str(e)
    
    content = '''
    <div class="card">
        <h2>URL 内容获取</h2>
        <form method="POST">
            <input type="text" name="url" placeholder="输入URL" required>
            <button type="submit" class="btn">获取</button>
        </form>
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        {% if content_result %}
        <h3 style="margin-top: 20px;">内容:</h3>
        <pre>{{ content_result }}</pre>
        {% endif %}
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='URL获取', content_result=content_result, error=error, session=session)


# ==================== 内部恢复服务 ====================

@app.route('/internal/backup/status')
def internal_backup_status():
    """内部备份状态 - 仅本机可访问，但可通过 SSRF 间接获取。"""
    if not is_local_request() or not is_internal_fetch():
        return jsonify({
            "status": "forbidden",
            "message": "internal service, fetch proxy only"
        }), 403

    return jsonify({
        "status": "ok",
        "challenge": BACKUP_CHALLENGE,
        "nonce": get_restore_nonce(),
        "flag": VULN_FLAGS['ssrf'],
    })


@app.route('/internal/ops/queue')
def internal_ops_queue():
    """内部维护队列状态，仅允许由 SSRF 代理访问。"""
    if not is_internal_fetch():
        return jsonify({"error": "forbidden"}), 403

    return jsonify({
        "status": "ready",
        "queue": get_ops_queue(),
        "nonce": get_ops_nonce(),
    })


@app.route('/internal/workflows/preview')
def internal_workflow_preview():
    """内部工作流预览状态，仅允许 SSRF 代理访问。"""
    if not is_internal_fetch():
        return jsonify({"error": "forbidden"}), 403

    return jsonify({
        "status": "ready",
        "job": get_workflow_job_name(),
        "nonce": get_workflow_preview_nonce(),
    })


@app.route('/internal/plugins/catalog')
def internal_plugin_catalog():
    """内部插件目录状态，仅允许 SSRF 代理访问。"""
    if not is_internal_fetch():
        return jsonify({"error": "forbidden"}), 403

    return jsonify({
        "status": "ready",
        "channel": get_plugin_channel(),
        "nonce": get_plugin_nonce(),
    })


@app.route('/internal/reports/replay')
def internal_report_replay():
    """内部报告重放状态，仅允许 SSRF 代理访问。"""
    if not is_internal_fetch():
        return jsonify({"error": "forbidden"}), 403

    return jsonify({
        "status": "ready",
        "stream": get_replay_stream(),
        "nonce": get_replay_nonce(),
    })


# ==================== 文件上传漏洞 ====================

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """文件上传 - 存在任意文件上传漏洞"""
    message = None
    files_list = []
    
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            # 漏洞: 没有文件类型验证
            filepath = os.path.join(upload_dir, file.filename)
            file.save(filepath)
            message = f"文件 {file.filename} 上传成功!"
            if is_dangerous_upload(file.filename):
                message += f" {VULN_FLAGS['upload']}"
    
    # 列出已上传文件
    if os.path.exists(upload_dir):
        files_list = os.listdir(upload_dir)
    
    files_html = ''.join([f'<li><a href="/uploads/{f}">{f}</a></li>' for f in files_list])
    
    content = '''
    <div class="card">
        <h2>文件上传</h2>
        {% if message %}
        <div class="alert alert-success">{{ message }}</div>
        {% endif %}
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit" class="btn">上传</button>
        </form>
    </div>
    <div class="card">
        <h2>已上传文件</h2>
        <ul>{{ files_html|safe }}</ul>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='上传', message=message, files_html=files_html, session=session)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """访问上传的文件"""
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_file(os.path.join(upload_dir, filename))


# ==================== 路径遍历 ====================

@app.route('/files')
def files():
    """文件浏览 - 存在路径遍历"""
    filename = request.args.get('file', 'readme.txt')
    content_result = None
    error = None
    
    base_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    try:
        # 漏洞: 路径遍历, 没有正确验证路径
        filepath = os.path.join(base_dir, filename)
        with open(filepath, 'r') as f:
            content_result = f.read()
    except Exception as e:
        error = str(e)
    
    content = '''
    <div class="card">
        <h2>文件查看</h2>
        <form method="GET">
            <input type="text" name="file" value="{{ filename }}" placeholder="文件名">
            <button type="submit" class="btn">查看</button>
        </form>
    </div>
    {% if error %}
    <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
    {% if content_result %}
    <div class="card">
        <h3>文件内容:</h3>
        <pre>{{ content_result }}</pre>
    </div>
    {% endif %}
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='文件', content_result=content_result, error=error, 
                                  filename=filename, session=session)


# ==================== 产品搜索 (SQL注入) ====================

@app.route('/products')
def products():
    """产品列表 - 存在SQL注入"""
    conn = get_db()
    cursor = conn.cursor()
    
    search = request.args.get('search', '')
    
    if search:
        # 漏洞: SQL注入
        query = f"SELECT * FROM products WHERE name LIKE '%{search}%' OR description LIKE '%{search}%'"
    else:
        query = "SELECT * FROM products"
    
    try:
        cursor.execute(query)
        products_list = cursor.fetchall()
    except Exception as e:
        products_list = []
    finally:
        conn.close()
    
    sqli_flag_html = ''
    if search and looks_like_sqli(search):
        sqli_flag_html = f'''
        <div class="card">
            <h3>验证结果</h3>
            <p><span class="flag">{VULN_FLAGS["sqli"]}</span></p>
        </div>
        '''

    products_html = ''
    for p in products_list:
        products_html += f'''
        <div class="card">
            <h3>{p['name']}</h3>
            <p>{p['description']}</p>
            <p>价格: ${p['price']}</p>
        </div>
        '''
    
    content = f'''
    <div class="card">
        <h2>产品列表</h2>
        <form method="GET">
            <input type="text" name="search" placeholder="搜索产品..." value="{search}">
            <button type="submit" class="btn">搜索</button>
        </form>
    </div>
    {sqli_flag_html}
    {products_html}
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='产品', session=session)


# ==================== 管理后台 ====================

@app.route('/admin')
def admin():
    """管理后台 - 存在认证绕过"""
    # 漏洞: 不安全的直接对象引用, 只检查cookie中的role
    if session.get('role') != 'admin':
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', 
            '<div class="card"><h2>拒绝访问</h2><p>需要管理员权限</p></div>'), 
            title='管理', session=session)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    
    users_html = '<table><tr><th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>API Key</th></tr>'
    for u in users:
        users_html += f'<tr><td>{u["id"]}</td><td>{u["username"]}</td><td>{u["email"]}</td><td>{u["role"]}</td><td>{u["api_key"]}</td></tr>'
    users_html += '</table>'
    
    content = f'''
    <div class="card">
        <h2>管理面板</h2>
        <h3 style="margin-top: 20px;">用户列表</h3>
        {users_html}
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='管理', session=session)


# ==================== 最终恢复挑战 ====================

@app.route('/admin/restore')
def admin_restore():
    """管理员恢复接口 - 需要管理员会话和计算出的恢复票据。"""
    if session.get('role') != 'admin':
        content = '''
        <div class="card">
            <h2>恢复中心</h2>
            <p>需要管理员会话。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='恢复中心', session=session)

    challenge = request.args.get('challenge', '')
    ticket = request.args.get('ticket', '')
    expected_ticket = build_restore_ticket(get_restore_nonce(), get_restore_salt(), BACKUP_CHALLENGE)

    if challenge != BACKUP_CHALLENGE or ticket != expected_ticket:
        content = '''
        <div class="card">
            <h2>恢复中心</h2>
            <p>票据校验失败。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='恢复中心', session=session), 403

    final_flag = read_final_flag()
    content = f'''
    <div class="card">
        <h2>恢复中心</h2>
        <p>备份恢复成功，已导出最终证明。</p>
        <p><span class="flag">{final_flag}</span></p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                  title='恢复中心', session=session)


@app.route('/admin/ops/console')
def admin_ops_console():
    """旧版维护控制台 - 依赖可伪造签名包且对模板做不安全渲染。"""
    if session.get('role') != 'admin':
        content = '''
        <div class="card">
            <h2>旧版维护控制台</h2>
            <p>需要管理员会话。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='维护控制台', session=session), 403

    bundle = request.args.get('bundle', '')
    signature = request.args.get('sig', '')
    if not bundle or not signature:
        content = '''
        <div class="card">
            <h2>旧版维护控制台</h2>
            <p>缺少维护包。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='维护控制台', session=session), 400

    try:
        padded = bundle + '=' * (-len(bundle) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        package = json.loads(decoded)
    except Exception as exc:
        return jsonify({"status": "error", "message": f"invalid bundle: {exc}"}), 400

    operator = package.get('operator', '')
    queue_name = package.get('queue', '')
    nonce = package.get('nonce', '')
    template = package.get('template', '')
    expected = build_ops_bundle_signature(operator, queue_name, nonce, get_ops_bundle_seed())

    if operator != session.get('user') or queue_name != get_ops_queue() or nonce != get_ops_nonce() or signature != expected:
        return jsonify({"status": "error", "message": "signature mismatch"}), 403

    rendered_preview = render_template_string(
        template,
        queue=queue_name,
        operator=operator,
        maintenance_window='02:00Z',
        ops_secret=VULN_FLAGS['ops_console'],
    )

    content = '''
    <div class="card">
        <h2>旧版维护控制台</h2>
        <p>签名维护包已接受。</p>
        <pre>{{ rendered_preview }}</pre>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                  title='维护控制台', rendered_preview=rendered_preview, session=session)


@app.route('/admin/workflows/preview')
def admin_workflow_preview():
    """旧版工作流预览控制台，存在签名包伪造与模板渲染风险。"""
    if session.get('role') != 'admin':
        content = '''
        <div class="card">
            <h2>工作流预览</h2>
            <p>需要管理员会话。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='工作流预览', session=session), 403

    bundle = request.args.get('bundle', '')
    signature = request.args.get('sig', '')
    if not bundle or not signature:
        content = '''
        <div class="card">
            <h2>工作流预览</h2>
            <p>缺少预览包。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='工作流预览', session=session), 400

    try:
        padded = bundle + '=' * (-len(bundle) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        package = json.loads(decoded)
    except Exception as exc:
        return jsonify({"status": "error", "message": f"invalid preview bundle: {exc}"}), 400

    operator = package.get('operator', '')
    job_name = package.get('job', '')
    nonce = package.get('nonce', '')
    template_name = package.get('template_name', '')
    mode = package.get('mode', '')
    expected = build_workflow_preview_signature(
        operator,
        job_name,
        nonce,
        template_name,
        get_workflow_preview_seed(),
    )

    if (
        operator != session.get('user')
        or job_name != get_workflow_job_name()
        or nonce != get_workflow_preview_nonce()
        or mode != 'legacy-jinja-preview'
        or signature != expected
    ):
        return jsonify({"status": "error", "message": "preview signature mismatch"}), 403

    template_path = os.path.join(UPLOAD_DIR, template_name)
    try:
        with open(template_path, 'r') as f:
            preview_template = f.read()
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "template not found"}), 404

    rendered_preview = render_template_string(
        preview_template,
        workflow_flag=VULN_FLAGS['workflow_preview'],
        operator=operator,
        job=job_name,
        render_mode=mode,
    )

    content = '''
    <div class="card">
        <h2>工作流预览</h2>
        <p>已加载签名预览包。</p>
        <pre>{{ rendered_preview }}</pre>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                  title='工作流预览', rendered_preview=rendered_preview, session=session)


@app.route('/admin/plugins/import')
def admin_plugin_import():
    """旧版插件热修复导入，存在签名包伪造与模板渲染风险。"""
    if session.get('role') != 'admin':
        content = '''
        <div class="card">
            <h2>插件导入</h2>
            <p>需要管理员会话。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='插件导入', session=session), 403

    bundle = request.args.get('bundle', '')
    signature = request.args.get('sig', '')
    if not bundle or not signature:
        content = '''
        <div class="card">
            <h2>插件导入</h2>
            <p>缺少导入包。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='插件导入', session=session), 400

    try:
        padded = bundle + '=' * (-len(bundle) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        package = json.loads(decoded)
    except Exception as exc:
        return jsonify({"status": "error", "message": f"invalid import bundle: {exc}"}), 400

    operator = package.get('operator', '')
    channel = package.get('channel', '')
    nonce = package.get('nonce', '')
    manifest_name = package.get('manifest_name', '')
    manifest_format = package.get('format', '')
    expected = build_plugin_import_signature(
        operator,
        channel,
        nonce,
        manifest_name,
        get_plugin_import_seed(),
    )

    if (
        operator != session.get('user')
        or channel != get_plugin_channel()
        or nonce != get_plugin_nonce()
        or manifest_format != 'manifest-v2'
        or signature != expected
    ):
        return jsonify({"status": "error", "message": "import signature mismatch"}), 403

    manifest_path = os.path.join(UPLOAD_DIR, manifest_name)
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "manifest not found"}), 404
    except json.JSONDecodeError as exc:
        return jsonify({"status": "error", "message": f"invalid manifest: {exc}"}), 400

    notes_template = manifest.get('notes_template', '')
    rendered_notes = render_template_string(
        notes_template,
        plugin_flag=VULN_FLAGS['plugin_hotfix'],
        operator=operator,
        channel=channel,
        package_name=manifest.get('package_name', 'plugin-package'),
    )

    content = '''
    <div class="card">
        <h2>插件导入</h2>
        <p>已加载签名导入包。</p>
        <pre>{{ rendered_notes }}</pre>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                  title='插件导入', rendered_notes=rendered_notes, session=session)


@app.route('/admin/reports/replay')
def admin_report_replay_console():
    """旧版报告状态重放，存在签名状态包伪造与模板渲染风险。"""
    if session.get('role') != 'admin':
        content = '''
        <div class="card">
            <h2>报告重放</h2>
            <p>需要管理员会话。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='报告重放', session=session), 403

    state = request.args.get('state', '')
    signature = request.args.get('sig', '')
    if not state or not signature:
        content = '''
        <div class="card">
            <h2>报告重放</h2>
            <p>缺少状态包。</p>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                      title='报告重放', session=session), 400

    try:
        padded = state + '=' * (-len(state) % 4)
        raw_state = base64.urlsafe_b64decode(padded.encode()).decode()
        package = json.loads(raw_state)
    except Exception as exc:
        return jsonify({"status": "error", "message": f"invalid state package: {exc}"}), 400

    operator = package.get('operator', '')
    stream_name = package.get('stream', '')
    nonce = package.get('nonce', '')
    renderer = package.get('renderer', '')
    summary_template = package.get('summary', '')
    state_digest = build_replay_state_digest(raw_state)
    expected = build_replay_state_signature(
        operator,
        stream_name,
        nonce,
        state_digest,
        get_replay_state_seed(),
    )

    if (
        operator != session.get('user')
        or stream_name != get_replay_stream()
        or nonce != get_replay_nonce()
        or renderer != 'legacy-state-render'
        or signature != expected
    ):
        return jsonify({"status": "error", "message": "replay signature mismatch"}), 403

    rendered_summary = render_template_string(
        summary_template,
        replay_flag=VULN_FLAGS['report_replay'],
        operator=operator,
        stream=stream_name,
        state_version=package.get('version', 'v1'),
    )

    content = '''
    <div class="card">
        <h2>报告重放</h2>
        <p>已恢复签名状态包。</p>
        <pre>{{ rendered_summary }}</pre>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content),
                                  title='报告重放', rendered_summary=rendered_summary, session=session)


# ==================== 反序列化漏洞 ====================

@app.route('/api/data', methods=['GET', 'POST'])
def api_data():
    """API接口 - 存在不安全反序列化"""
    if request.method == 'POST':
        data = request.form.get('data', '')
        try:
            # 漏洞: 不安全的pickle反序列化
            decoded = bytes.fromhex(data)
            result = pickle.loads(decoded)
            return jsonify({
                "status": "success",
                "result": str(result),
                "flag": VULN_FLAGS['deserialize']
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    content = '''
    <div class="card">
        <h2>数据反序列化API</h2>
        <form method="POST">
            <textarea name="data" rows="3" placeholder="输入hex编码的pickle数据"></textarea>
            <button type="submit" class="btn">反序列化</button>
        </form>
        <p style="margin-top: 10px;">接受pickle格式的hex编码数据</p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='API', session=session)


# ==================== XML外部实体 ====================

@app.route('/api/xml', methods=['GET', 'POST'])
def api_xml():
    """XML解析API - 存在XXE"""
    result = None
    error = None
    
    if request.method == 'POST':
        xml_data = request.form.get('xml', '')
        try:
            # 漏洞: XXE
            import xml.etree.ElementTree as ET
            entity_match = re.search(
                r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"file://([^"]+)">',
                xml_data,
                re.IGNORECASE
            )
            if entity_match:
                entity_name = entity_match.group(1)
                file_path = entity_match.group(2)
                with open(file_path, 'r') as f:
                    entity_value = f.read()
                xml_data = re.sub(r'<!DOCTYPE[\s\S]*?\]>', '', xml_data, flags=re.IGNORECASE)
                xml_data = xml_data.replace(f"&{entity_name};", entity_value)
            root = ET.fromstring(xml_data)
            result = ET.tostring(root, encoding='unicode')
        except Exception as e:
            error = str(e)
    
    content = '''
    <div class="card">
        <h2>XML解析API</h2>
        <form method="POST">
            <textarea name="xml" rows="5" placeholder="输入XML数据"></textarea>
            <button type="submit" class="btn">解析</button>
        </form>
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        {% if result %}
        <h3 style="margin-top: 20px;">解析结果:</h3>
        <pre>{{ result }}</pre>
        {% endif %}
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='XML', result=result, error=error, session=session)


# ==================== 信息泄露 ====================

@app.route('/debug')
def debug():
    """调试信息 - 信息泄露"""
    import sys
    import platform
    
    content = f'''
    <div class="card">
        <h2>调试信息</h2>
        <pre>
Python版本: {sys.version}
平台: {platform.platform()}
工作目录: {os.getcwd()}
service_profile=legacy-support-export:{EXPORT_SIGNING_KEY}
环境变量:
{chr(10).join([f"  {k}={v}" for k, v in os.environ.items() if 'KEY' in k or 'PASS' in k or 'SECRET' in k])}
        </pre>
        <span class="flag">{VULN_FLAGS["info"]}</span>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='调试', session=session)


@app.route('/robots.txt')
def robots():
    """robots.txt"""
    return '''
User-agent: *
Allow: /
Disallow: /static/
'''


@app.route('/.git/config')
def git_config():
    """模拟Git配置泄露"""
    return '''[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = https://github.com/example/vulnlab.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
'''


# ==================== 错误处理 ====================

@app.errorhandler(404)
def page_not_found(e):
    content = '''
    <div class="card">
        <h2>404 - 页面未找到</h2>
        <p>请求的页面不存在</p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='404', session=session), 404


@app.errorhandler(500)
def internal_error(e):
    content = '''
    <div class="card">
        <h2>500 - 服务器错误</h2>
        <p>内部服务器错误</p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}', content), 
                                  title='500', session=session), 500


# ==================== 启动 ====================

if __name__ == '__main__':
    init_db()
    
    # 创建readme文件
    readme_path = os.path.join(os.path.dirname(__file__), 'data', 'readme.txt')
    with open(readme_path, 'w') as f:
        f.write('''VulnLab 靶机说明
==================

这是一个包含多个历史模块的测试环境。
环境仅用于安全测试。
''')
    
    print("=" * 50)
    print("VulnLab 靶机启动中...")
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
