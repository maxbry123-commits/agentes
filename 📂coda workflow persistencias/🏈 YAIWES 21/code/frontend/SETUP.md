# H-Pentest Frontend 安装和运行指南

## 📦 安装依赖

```bash
cd /home/H-pentest/H-pentest/frontend
npm install
```

## 🚀 启动开发服务器

```bash
npm run dev
```

前端将运行在 `http://localhost:5173`

## 🔧 后端API适配说明

本前端已完全适配新后端API，使用以下端点：

### Tasks API (`/api/v1/tasks`)
- ✅ `POST /` - 创建任务
- ✅ `GET /` - 获取任务列表  
- ✅ `GET /{task_id}` - 获取任务详情
- ✅ `POST /{task_id}/intervention` - 人工干预（暂停/恢复/注入指令）
- ✅ `POST /{task_id}/stop` - 停止任务
- ✅ `DELETE /{task_id}` - 删除任务

### Messages API (`/api/v1/tasks/{task_id}/messages`)
- ✅ `GET /tasks/{task_id}/messages` - 获取消息列表
- ✅ `GET /tasks/{task_id}/messages/latest` - 增量轮询获取最新消息

### Conversations API (`/api/v1/tasks/{task_id}/conversations`)
- ✅ `GET /tasks/{task_id}/conversations` - 获取对话历史

### WebSocket API (`/api/v1/ws`)
- ✅ `WS /ws/{task_id}` - WebSocket实时连接

## 📁 目录结构

```
src/
├── services/           # API服务层
│   ├── api.ts          # 后端API封装
│   └── message-polling.ts  # 消息轮询服务
├── stores/            # 状态管理
│   └── taskStore.ts   # 任务状态管理
├── views/             # 页面组件
│   ├── Dashboard.vue  # 仪表盘
│   ├── Monitor.vue    # 实时监控
│   ├── TaskList.vue   # 任务列表
│   ├── Report.vue     # 测试报告
│   └── Settings.vue   # 系统配置
├── components/        # 可复用组件
├── router/           # 路由配置
└── styles/           # 样式文件
```

## 🎯 主要特性

- ✨ 科技风暗色主题界面
- 🔄 HTTP轮询实时消息（完全适配新后端messages API）
- 💬 对话式日志展示
- 📊 漏洞分析可视化（直接从Task对象获取数据）
- 🎮 人工干预支持（暂停/恢复/注入指令）
- 📈 实时进度监控

## ⚠️ 注意事项

1. 确保后端运行在 `http://localhost:8000`
2. 所有API调用已适配新后端结构
3. 移除了旧后端不支持的API调用（如 `/events`, `/messages/stats`, `/report` 等）
4. 统计数据直接从Task对象中获取，无需额外API请求
