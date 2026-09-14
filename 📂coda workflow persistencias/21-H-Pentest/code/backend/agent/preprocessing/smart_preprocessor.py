"""
智能预处理器 - 参考原项目设计，学习其思路重新实现
目标：全面收集页面信息、识别技术栈、提取特征、主动探测
"""
from typing import Dict, Any, List


class SmartPreprocessor:
    """
    智能预处理器
    
    分四个阶段：
    1. 页面分析 - 获取HTML、响应头、Cookies
    2. 特征提取 - 表单、参数、技术栈、JS文件
    3. 指纹匹配 - 基于特征识别可能的漏洞
    4. 主动探测 - 凭据爆破、SQL注入探测
    """
    
    def __init__(self, target_url: str, tool_instances: Dict, output_manager):
        self.target_url = target_url
        self.tool_instances = tool_instances
        self.output = output_manager
        
        self.page_data = {}
        self.features = {}
        self.vulnerabilities = []
        self.active_probe_results = {}
    
    async def analyze(self) -> Dict[str, Any]:
        """
        执行完整的智能预处理分析
        
        Returns:
            Dict包含所有分析结果
        """
        self.output.log("info", "🔍 智能预处理开始...")
        
        # Step 1: 页面分析
        await self._fetch_and_analyze_page()
        
        # Step 2: 特征提取
        await self._extract_features()
        
        # Step 3: Nuclei快速扫描
        await self._run_nuclei_scan()
        
        # Step 4: 主动探测（如果有登录表单）
        if self.features.get('has_login'):
            await self._run_active_probes()
        
        # 返回完整结果
        return {
            'success': True,
            'target': self.target_url,
            'page_data': self.page_data,
            'features': self.features,
            'vulnerabilities': self.vulnerabilities,
            'active_probe': self.active_probe_results
        }
    
    async def _fetch_and_analyze_page(self):
        """
        Step 1: 页面分析
        - 获取HTML（去除CSS，限制10000字符）
        - 获取响应头
        - 获取Cookies
        """
        self.output.log("info", "📝 Step 1: 页面分析...")
        
        try:
            python_tool = self.tool_instances.get('execute_python')
            if not python_tool:
                self.output.log("error", "❌ execute_python工具不可用")
                return
            
            page_code = f"""
import requests
from bs4 import BeautifulSoup
import json

try:
    # 获取页面
    resp = requests.get('{self.target_url}', timeout=10, allow_redirects=True)
    raw_html = resp.text
    
    # 使用BeautifulSoup清理HTML
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # 移除<style>标签
    for style in soup.find_all('style'):
        style.decompose()
    
    # 移除style属性
    for tag in soup.find_all(style=True):
        del tag['style']
    
    # 移除<link rel="stylesheet">
    for link in soup.find_all('link', rel='stylesheet'):
        link.decompose()
    
    # 转换回字符串
    cleaned_html = str(soup)
    
    # 限制最大10000字符
    truncated_html = cleaned_html[:10000]
    
    # 提取Cookies
    cookies = []
    for cookie in resp.cookies:
        cookies.append({{
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'path': cookie.path
        }})
    
    # 输出JSON
    result = {{
        'success': True,
        'status_code': resp.status_code,
        'headers': dict(resp.headers),
        'html': truncated_html,
        'html_length_original': len(raw_html),
        'html_length_cleaned': len(cleaned_html),
        'html_length_truncated': len(truncated_html),
        'cookies': cookies,
        'url': resp.url,
        'final_url': resp.url
    }}
    
    print(json.dumps(result, ensure_ascii=False))
    
except Exception as e:
    print(json.dumps({{
        'success': False,
        'error': str(e)
    }}, ensure_ascii=False))
"""
            
            page_result_str = await python_tool.execute(code=page_code)
            
            # 🔥 解析execute_python的返回格式：先提取Output部分，再解析JSON
            import json
            try:
                # execute_python返回格式:
                # Exit Code: 0
                # Execution Time: 1.23s
                # ============================================================
                # Output:
                # {"success": true, ...}
                
                # 提取Output后的内容
                if "Output:" in page_result_str:
                    json_str = page_result_str.split("Output:", 1)[1].strip()
                else:
                    json_str = page_result_str
                
                page_result = json.loads(json_str)
                if page_result.get('success'):
                    self.page_data = page_result
                    self.output.log("success", f"✅ 页面获取成功: {page_result['status_code']}")
                    self.output.log("info", f"   HTML: {page_result['html_length_original']} → {page_result['html_length_truncated']} 字符")
                    self.output.log("info", f"   Cookies: {len(page_result.get('cookies', []))}个")
                else:
                    self.output.log("error", f"❌ 页面获取失败: {page_result.get('error')}")
            except Exception as e:
                self.output.log("warning", f"⚠️ JSON解析失败: {e}")
                self.output.log("debug", f"   原始输出: {page_result_str[:500]}")
        
        except Exception as e:
            self.output.log("error", f"❌ 页面分析失败: {e}")
    
    async def _extract_features(self):
        """
        Step 2: 特征提取
        - 表单（action, method, inputs）
        - 技术栈（Server, X-Powered-By, HTML关键字）
        - JS文件
        - 链接
        - 是否有登录表单
        """
        self.output.log("info", "🔍 Step 2: 特征提取...")
        
        if not self.page_data.get('html'):
            self.output.log("warning", "⚠️ 无HTML内容，跳过特征提取")
            return
        
        try:
            python_tool = self.tool_instances.get('execute_python')
            if not python_tool:
                return
            
            html_content = self.page_data['html']
            headers = self.page_data.get('headers', {})
            
            feature_code = f"""
from bs4 import BeautifulSoup
import json

html = '''{html_content}'''
headers = {headers}

soup = BeautifulSoup(html, 'html.parser')

# 1. 提取表单
forms = []
for form in soup.find_all('form'):
    form_data = {{
        'action': form.get('action', ''),
        'method': (form.get('method') or 'GET').upper(),
        'inputs': []
    }}
    
    for inp in form.find_all(['input', 'textarea', 'select']):
        form_data['inputs'].append({{
            'name': inp.get('name', ''),
            'type': inp.get('type', 'text'),
            'value': inp.get('value', '')
        }})
    
    forms.append(form_data)

# 2. 提取技术栈
technologies = []
if 'Server' in headers:
    technologies.append(headers['Server'])
if 'X-Powered-By' in headers:
    technologies.append(headers['X-Powered-By'])

html_lower = html.lower()
if 'flask' in html_lower:
    technologies.append('Flask')
if 'django' in html_lower:
    technologies.append('Django')
if 'express' in html_lower:
    technologies.append('Express')
if 'php' in html_lower:
    technologies.append('PHP')

# 3. 提取JS文件
scripts = []
for script in soup.find_all('script', src=True):
    scripts.append(script['src'])

# 4. 提取链接
links = []
for a in soup.find_all('a', href=True):
    links.append(a['href'])

# 5. 检测登录表单
has_login = False
for form in forms:
    inputs = form.get('inputs', [])
    has_password = any(inp.get('type', '').lower() == 'password' for inp in inputs)
    if has_password:
        has_login = True
        break

result = {{
    'forms': forms,
    'technologies': technologies,
    'scripts': scripts[:10],
    'links': links[:20],
    'has_login': has_login,
    'form_count': len(forms)
}}

print(json.dumps(result, ensure_ascii=False))
"""
            
            feature_result_str = await python_tool.execute(code=feature_code)
            
            # 🔥 解析JSON结果
            import json
            try:
                # 提取Output后的内容
                if "Output:" in feature_result_str:
                    json_str = feature_result_str.split("Output:", 1)[1].strip()
                else:
                    json_str = feature_result_str
                
                feature_result = json.loads(json_str)
                self.features = feature_result
                
                self.output.log("success", f"✅ 特征提取成功")
                self.output.log("info", f"   表单: {feature_result.get('form_count', 0)}个")
                self.output.log("info", f"   技术栈: {', '.join(feature_result.get('technologies', [])) if feature_result.get('technologies') else '未知'}")
                self.output.log("info", f"   登录表单: {'是' if feature_result.get('has_login') else '否'}")
            except Exception as e:
                self.output.log("warning", f"⚠️ 特征JSON解析失败: {e}")
                self.output.log("debug", f"   原始输出: {feature_result_str[:500]}")
        
        except Exception as e:
            self.output.log("error", f"❌ 特征提取失败: {e}")
    
    async def _run_nuclei_scan(self):
        """
        Step 3: Nuclei快速扫描
        - 只扫描critical和high严重程度
        - 限制60秒超时
        """
        self.output.log("info", "🔥 Step 3: Nuclei快速扫描...")
        
        try:
            nuclei_tool = self.tool_instances.get('nuclei_scan')
            if not nuclei_tool:
                self.output.log("warning", "⚠️ nuclei_scan工具不可用，跳过")
                return
            
            nuclei_result = await nuclei_tool.execute(
                target=self.target_url,
                severity="critical,high",
                timeout=60
            )
            
            # 解析结果
            import json
            try:
                vulns_data = json.loads(nuclei_result)
                vulns = vulns_data.get('vulnerabilities', [])
                self.vulnerabilities.extend(vulns)
                
                self.output.log("success", f"✅ Nuclei: 发现 {len(vulns)} 个漏洞")
                
                for vuln in vulns[:3]:
                    self.output.log("info", f"  - [{vuln.get('severity', 'N/A')}] {vuln.get('name', 'N/A')}")
            except Exception as e:
                self.output.log("warning", f"⚠️ Nuclei结果解析失败: {e}")
        
        except Exception as e:
            self.output.log("warning", f"⚠️ Nuclei扫描失败: {e}")
    
    async def _run_active_probes(self):
        """
        Step 4: 主动探测
        - 凭据爆破（尝试常见凭据）
        """
        self.output.log("info", "🔑 Step 4: 凭据爆破...")
        
        try:
            python_tool = self.tool_instances.get('execute_python')
            if not python_tool:
                return
            
            login_code = f"""
import requests
import json

target = '{self.target_url}'

# 常见凭据列表
credentials = [
    ('admin', 'admin'),
    ('admin', '123456'),
    ('admin', 'password'),
    ('root', 'root'),
    ('test', 'test'),
    ('guest', 'guest')
]

valid_creds = []

for username, password in credentials:
    try:
        # 尝试POST登录
        resp = requests.post(
            target,
            data={{'username': username, 'password': password}},
            allow_redirects=False,
            timeout=5
        )
        
        # 检测成功标志
        success_indicators = [
            resp.status_code == 302,
            'welcome' in resp.text.lower(),
            'dashboard' in resp.text.lower(),
            'logout' in resp.text.lower(),
            'success' in resp.text.lower()
        ]
        
        if any(success_indicators):
            valid_creds.append({{
                'username': username,
                'password': password,
                'redirect': resp.headers.get('Location', ''),
                'status_code': resp.status_code
            }})
            break
    except:
        continue

result = {{
    'success': len(valid_creds) > 0,
    'valid_credentials': valid_creds,
    'tried_count': len(credentials)
}}

print(json.dumps(result, ensure_ascii=False))
"""
            
            login_result_str = await python_tool.execute(code=login_code)
            
            # 🔥 解析结果
            import json
            try:
                # 提取Output后的内容
                if "Output:" in login_result_str:
                    json_str = login_result_str.split("Output:", 1)[1].strip()
                else:
                    json_str = login_result_str
                
                login_result = json.loads(json_str)
                self.active_probe_results['credential_test'] = login_result
                
                if login_result.get('success'):
                    valid_cred = login_result['valid_credentials'][0]
                    self.output.log("success", f"✅ 登录成功! 凭据: {valid_cred['username']}:{valid_cred['password']}")
                    self.output.log("info", f"   重定向: {valid_cred.get('redirect', 'N/A')}")
                else:
                    self.output.log("info", f"   尝试{login_result.get('tried_count', 0)}组凭据，均失败")
            except Exception as e:
                self.output.log("warning", f"⚠️ 登录结果解析失败: {e}")
                self.output.log("debug", f"   原始输出: {login_result_str[:500]}")
        
        except Exception as e:
            self.output.log("error", f"❌ 凭据爆破失败: {e}")
