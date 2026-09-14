<template>
  <div class="settings-page tech-background">
    <!-- 科技风背景 -->
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="grid-overlay"></div>
    
    <div class="settings-container">
      <div class="page-header">
        <el-button @click="$router.push('/')" class="back-button" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h1 class="page-title">
          <i class="el-icon-setting"></i>
          系统配置
        </h1>
      </div>
      
      <!-- 配置标签页 -->
      <el-tabs v-model="activeTab" class="config-tabs">
        <!-- Agent配置 -->
        <el-tab-pane label="Agent配置" name="agent">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span><i class="el-icon-cpu"></i> Agent核心配置</span>
                <el-button type="primary" size="small" @click="saveAgentConfig" :loading="saving">
                  保存配置
                </el-button>
              </div>
            </template>
            
            <el-form :model="agentConfig" label-width="150px" class="config-form">
              <el-form-item label="最大轮数">
                <el-input-number 
                  v-model="agentConfig.max_rounds" 
                  :min="1" 
                  :max="100"
                  controls-position="right"
                />
                <span class="form-tip">Agent执行的最大思考-行动轮数</span>
              </el-form-item>
              
              <el-form-item label="超时时间(秒)">
                <el-input-number 
                  v-model="agentConfig.timeout" 
                  :min="60" 
                  :max="3600"
                  controls-position="right"
                />
                <span class="form-tip">单次任务的最大执行时间</span>
              </el-form-item>
              
              <el-form-item label="详细输出">
                <el-switch v-model="agentConfig.verbose" />
                <span class="form-tip">是否输出详细的调试信息</span>
              </el-form-item>
              
              <el-form-item label="调试模式">
                <el-switch v-model="agentConfig.debug" />
                <span class="form-tip">开启后会保存更多调试数据</span>
              </el-form-item>
              
              <el-divider />
              
              <el-form-item label="智能预处理">
                <el-switch v-model="agentConfig.preprocessing_enabled" />
                <span class="form-tip">启用目标站点的自动分析和指纹识别</span>
              </el-form-item>
              
              <el-form-item label="知识库检索">
                <el-switch v-model="agentConfig.knowledge_base_enabled" />
                <span class="form-tip">使用RAG知识库增强Agent能力</span>
              </el-form-item>
              
              <el-form-item label="检索重排序">
                <el-switch v-model="agentConfig.rerank_enabled" />
                <span class="form-tip">使用Rerank提升检索精度</span>
              </el-form-item>
              
              <el-form-item label="检索Top-K">
                <el-input-number 
                  v-model="agentConfig.search_top_k" 
                  :min="1" 
                  :max="20"
                  controls-position="right"
                />
                <span class="form-tip">知识库检索返回的文档数量</span>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>
        
        <!-- 工具管理 -->
        <el-tab-pane label="工具管理" name="tools">
          <div class="tools-header">
            <div class="tools-stats">
              <el-statistic title="总工具数" :value="toolsStats.total" />
              <el-statistic title="已启用" :value="toolsStats.enabled" class="enabled" />
              <el-statistic title="已禁用" :value="toolsStats.disabled" class="disabled" />
            </div>
            <el-button type="primary" @click="showAddToolDialog">
              <i class="el-icon-plus"></i> 添加工具
            </el-button>
          </div>
          
          <el-table 
            :data="toolsList" 
            class="tools-table"
            :row-class-name="getToolRowClass"
          >
            <el-table-column prop="name" label="工具名称" width="200">
              <template #default="{ row }">
                <span class="tool-name">{{ row.name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="描述" min-width="200" />
            
            <el-table-column prop="priority" label="优先级" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="getPriorityType(row.priority)">
                  P{{ row.priority }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="timeout" label="超时(秒)" width="100" align="center" />
            
            <el-table-column prop="enabled" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch 
                  v-model="row.enabled" 
                  @change="toggleTool(row.name, row.enabled)"
                />
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" align="center">
              <template #default="{ row }">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="editTool(row)"
                  link
                >
                  编辑
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="deleteTool(row.name)"
                  link
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <!-- API配置 -->
        <el-tab-pane label="API配置" name="api">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span><i class="el-icon-key"></i> LLM API配置</span>
                <el-button type="primary" size="small" @click="saveAPIConfig" :loading="saving">
                  保存配置
                </el-button>
              </div>
            </template>
            
            <el-form :model="apiConfig" label-width="150px" class="config-form">
              <el-form-item label="API密钥">
                <el-input 
                  v-model="apiConfig.api_key" 
                  type="password"
                  show-password
                  placeholder="输入新密钥以更新"
                />
                <span class="form-tip">保持为空则不修改当前密钥</span>
              </el-form-item>
              
              <el-form-item label="Base URL">
                <el-input v-model="apiConfig.base_url" placeholder="https://api.moonshot.cn/v1" />
                <span class="form-tip">LLM服务的API地址</span>
              </el-form-item>
              
              <el-form-item label="模型">
                <el-select v-model="apiConfig.model" placeholder="选择或输入模型名称" allow-create filterable>
                  <el-option label="kimi-k2-turbo-preview (推荐)" value="kimi-k2-turbo-preview" />
                  <el-option label="kimi-k1" value="kimi-k1" />
                  <el-option label="qwen-plus" value="qwen-plus" />
                  <el-option label="qwen-turbo" value="qwen-turbo" />
                  <el-option label="qwen-max" value="qwen-max" />
                  <el-option label="glm-4" value="glm-4" />
                  <el-option label="glm-4-plus" value="glm-4-plus" />
                  <el-option label="gpt-4" value="gpt-4" />
                  <el-option label="gpt-4-turbo" value="gpt-4-turbo" />
                  <el-option label="deepseek-chat" value="deepseek-chat" />
                </el-select>
                <span class="form-tip">可选择预设模型或手动输入自定义模型名称</span>
              </el-form-item>
              
              <el-form-item label="温度(Temperature)">
                <el-slider 
                  v-model="apiConfig.temperature" 
                  :min="0" 
                  :max="2" 
                  :step="0.1"
                  show-input
                />
                <span class="form-tip">控制输出的随机性，越低越确定</span>
              </el-form-item>
              
              <el-form-item label="最大Token数">
                <el-input-number 
                  v-model="apiConfig.max_tokens" 
                  :min="1024" 
                  :max="131072"
                  :step="1024"
                  controls-position="right"
                />
                <span class="form-tip">单次请求的最大Token限制</span>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 添加/编辑工具对话框 -->
    <el-dialog 
      v-model="toolDialogVisible" 
      :title="editingTool ? '编辑工具' : '添加工具'"
      width="600px"
    >
      <el-form :model="toolForm" label-width="120px">
        <el-form-item label="工具名称">
          <el-input v-model="toolForm.tool_name" :disabled="!!editingTool" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="toolForm.description" type="textarea" />
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-input-number v-model="toolForm.priority" :min="1" :max="100" />
        </el-form-item>
        
        <el-form-item label="超时(秒)">
          <el-input-number v-model="toolForm.timeout" :min="1" :max="600" />
        </el-form-item>
        
        <el-form-item label="启用">
          <el-switch v-model="toolForm.enabled" />
        </el-form-item>
        
        <el-form-item label="工具路径">
          <el-input v-model="toolForm.path" placeholder="例如: tools/my_tool/scanner.py">
            <template #prepend>
              <span style="color: rgba(255,255,255,0.6); font-size: 12px;">项目根目录/</span>
            </template>
          </el-input>
          <div class="path-tip">
            <el-icon><FolderOpened /></el-icon>
            <span>默认工具位置: <code>core/tools/</code></span>
            <el-divider direction="vertical" />
            <span>项目根目录: <code>/home/H-pentest/H-pentest/</code></span>
          </div>
          <div class="path-help">
            💡 如何添加工具？查看文档: <a href="#" @click.prevent="showToolDoc">docs/TOOL_DEVELOPMENT_GUIDE.md</a>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="toolDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTool" :loading="saving">
          {{ editingTool ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderOpened, ArrowLeft } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

// 标签页
const activeTab = ref('agent')

// Agent配置
const agentConfig = ref({
  max_rounds: 30,
  timeout: 300,
  verbose: false,
  debug: false,
  preprocessing_enabled: true,
  knowledge_base_enabled: true,
  rerank_enabled: true,
  search_top_k: 8
})

// 工具配置
const toolsConfig = ref({})
const toolsStats = ref({
  total: 0,
  enabled: 0,
  disabled: 0
})

// 工具列表
const toolsList = computed(() => {
  return Object.entries(toolsConfig.value).map(([name, config]: [string, any]) => ({
    name,
    ...config
  }))
})

// API配置
const apiConfig = ref({
  api_key: '',
  base_url: '',
  model: '',
  temperature: 0.2,
  max_tokens: 32768
})

// 状态
const saving = ref(false)
const toolDialogVisible = ref(false)
const editingTool = ref<string | null>(null)
const toolForm = ref({
  tool_name: '',
  description: '',
  priority: 1,
  timeout: 60,
  enabled: true,
  path: ''
})

// 加载配置
const loadConfigs = async () => {
  try {
    const response = await axios.get(`${API_BASE}/config/all`)
    const data = response.data.data
    
    // Agent配置 - 安全访问
    if (data.agent) {
      agentConfig.value = {
        max_rounds: data.agent.agent?.max_rounds || data.agent.max_rounds || 30,
        timeout: data.agent.agent?.timeout || data.agent.timeout || 300,
        verbose: data.agent.agent?.verbose || data.agent.verbose || false,
        debug: data.agent.agent?.debug || data.agent.debug || false,
        preprocessing_enabled: data.agent.preprocessing?.enabled || false,
        knowledge_base_enabled: data.agent.knowledge_base?.enabled || true,
        rerank_enabled: data.agent.knowledge_base?.rerank_enabled || false,
        search_top_k: data.agent.knowledge_base?.search_top_k || 5
      }
    }
    
    // 工具配置
    if (data.tools) {
      toolsConfig.value = data.tools.config
      toolsStats.value = data.tools.stats
    }
    
    // API配置
    if (data.api) {
      apiConfig.value = {
        api_key: '',
        base_url: data.api.llm_config?.base_url || '',
        model: data.api.llm_config?.model || '',
        temperature: data.api.llm_config?.temperature || 0.2,
        max_tokens: data.api.llm_config?.max_tokens || 32768
      }
    }
  } catch (error) {
    ElMessage.error('加载配置失败')
    console.error(error)
  }
}

// 保存Agent配置
const saveAgentConfig = async () => {
  saving.value = true
  try {
    await axios.put(`${API_BASE}/config/agent`, agentConfig.value)
    ElMessage.success('Agent配置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 保存API配置
const saveAPIConfig = async () => {
  saving.value = true
  try {
    await axios.put(`${API_BASE}/config/api`, apiConfig.value)
    ElMessage.success('API配置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 切换工具状态
const toggleTool = async (toolName: string, enabled: boolean) => {
  try {
    await axios.put(`${API_BASE}/config/tools/${toolName}`, {
      tool_name: toolName,
      enabled
    })
    ElMessage.success(`工具 ${toolName} 已${enabled ? '启用' : '禁用'}`)
    loadConfigs()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

// 显示添加工具对话框
const showAddToolDialog = () => {
  editingTool.value = null
  toolForm.value = {
    tool_name: '',
    description: '',
    priority: toolsList.value.length + 1,
    timeout: 60,
    enabled: true,
    path: ''
  }
  toolDialogVisible.value = true
}

// 编辑工具
const editTool = (tool: any) => {
  editingTool.value = tool.name
  toolForm.value = {
    tool_name: tool.name,
    description: tool.description,
    priority: tool.priority,
    timeout: tool.timeout,
    enabled: tool.enabled,
    path: tool.path || ''
  }
  toolDialogVisible.value = true
}

// 保存工具
const saveTool = async () => {
  saving.value = true
  try {
    if (editingTool.value) {
      // 更新工具
      await axios.put(`${API_BASE}/config/tools/${editingTool.value}`, toolForm.value)
      ElMessage.success('工具已更新')
    } else {
      // 创建工具
      await axios.post(`${API_BASE}/config/tools`, toolForm.value)
      ElMessage.success('工具已创建')
    }
    toolDialogVisible.value = false
    loadConfigs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 显示工具文档
const showToolDoc = () => {
  window.open('/docs/TOOL_DEVELOPMENT_GUIDE.md', '_blank')
}

// 删除工具
const deleteTool = async (toolName: string) => {
  try {
    await ElMessageBox.confirm(`确定要删除工具 "${toolName}" 吗？`, '警告', {
      type: 'warning'
    })
    
    await axios.delete(`${API_BASE}/config/tools/${toolName}`)
    ElMessage.success('工具已删除')
    loadConfigs()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

// 获取工具行样式
const getToolRowClass = ({ row }: any) => {
  return row.enabled ? '' : 'disabled-row'
}

// 获取优先级类型
const getPriorityType = (priority: number) => {
  if (priority <= 3) return 'danger'
  if (priority <= 6) return 'warning'
  return 'info'
}

// 粒子背景
const particleCanvas = ref<HTMLCanvasElement | null>(null)
let animationId: number

const initParticles = () => {
  const canvas = particleCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles: any[] = []
  const particleCount = 50

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2
    })
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    particles.forEach(p => {
      p.x += p.vx
      p.y += p.vy
      
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1
      
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(64, 158, 255, 0.3)'
      ctx.fill()
    })
    
    animationId = requestAnimationFrame(animate)
  }
  
  animate()
}

onMounted(() => {
  loadConfigs()
  initParticles()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow-x: hidden;
}

.particle-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.grid-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(64, 158, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  z-index: 0;
  pointer-events: none;
}

.settings-container {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.back-button {
  background: rgba(64, 158, 255, 0.2) !important;
  border: 1px solid rgba(64, 158, 255, 0.4);
  color: #409eff !important;
  width: 40px;
  height: 40px;
  transition: all 0.3s;
}

.back-button:hover {
  background: rgba(64, 158, 255, 0.3) !important;
  border-color: #409eff;
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.5);
  transform: translateX(-3px);
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 30px;
  text-shadow: 0 0 20px rgba(64, 158, 255, 0.5);
}

.page-title i {
  margin-right: 10px;
  color: #409eff;
}

.config-tabs :deep(.el-tabs__header) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 20px;
}

.config-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.config-tabs :deep(.el-tabs__item) {
  color: rgba(255, 255, 255, 0.7);
  font-size: 16px;
}

.config-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
}

.config-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.config-card :deep(.el-card__header) {
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
  padding: 15px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 600;
}

.card-header i {
  margin-right: 8px;
  color: #409eff;
}

.config-form :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.8);
}

.config-form :deep(.el-input__inner),
.config-form :deep(.el-textarea__inner),
.config-form :deep(.el-input-number__decrease),
.config-form :deep(.el-input-number__increase),
.config-form :deep(.el-select__wrapper) {
  background: rgba(26, 31, 58, 0.6) !important;
  border-color: rgba(64, 158, 255, 0.3);
  color: rgba(255, 255, 255, 0.9) !important;
}

.config-form :deep(.el-input__inner::placeholder),
.config-form :deep(.el-textarea__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4);
}

.config-form :deep(.el-input__inner:focus),
.config-form :deep(.el-textarea__inner:focus),
.config-form :deep(.el-select__wrapper.is-focused) {
  border-color: #409eff;
  background: rgba(26, 31, 58, 0.8) !important;
}

.config-form :deep(.el-input-number input) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.config-form :deep(.el-slider__bar) {
  background: linear-gradient(90deg, #409eff, #67c23a);
}

.config-form :deep(.el-slider__button) {
  border-color: #409eff;
  background: #409eff;
}

.config-form :deep(.el-slider__runway) {
  background: rgba(255, 255, 255, 0.1);
}

.config-form :deep(.el-input-group__prepend) {
  background: rgba(26, 31, 58, 0.5) !important;
  border-color: rgba(64, 158, 255, 0.3);
  color: rgba(255, 255, 255, 0.6) !important;
}

.config-form :deep(.el-input-group__append) {
  background: rgba(26, 31, 58, 0.5) !important;
  border-color: rgba(64, 158, 255, 0.3);
  color: rgba(255, 255, 255, 0.6) !important;
}

.config-form :deep(.el-switch) {
  --el-switch-on-color: #409eff;
  --el-switch-off-color: rgba(255, 255, 255, 0.2);
}

.config-form :deep(.el-switch__core) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(64, 158, 255, 0.3);
}

.config-form :deep(.el-switch.is-checked .el-switch__core) {
  background: #409eff !important;
  border-color: #409eff;
}

.config-form :deep(.el-input-number) {
  background: transparent;
}

.config-form :deep(.el-input-number .el-input__wrapper) {
  background: rgba(26, 31, 58, 0.6) !important;
  border-color: rgba(64, 158, 255, 0.3);
  box-shadow: none;
}

.config-form :deep(.el-input-number .el-input__wrapper:hover),
.config-form :deep(.el-input-number .el-input__wrapper.is-focus) {
  background: rgba(26, 31, 58, 0.8) !important;
  border-color: #409eff;
  box-shadow: none;
}

.config-form :deep(.el-select-dropdown) {
  background: rgba(26, 31, 58, 0.98);
  border-color: rgba(64, 158, 255, 0.3);
}

.config-form :deep(.el-select-dropdown__item) {
  color: rgba(255, 255, 255, 0.85);
}

.config-form :deep(.el-select-dropdown__item:hover) {
  background: rgba(64, 158, 255, 0.2);
}

.config-form :deep(.el-select-dropdown__item.is-selected) {
  color: #409eff;
  background: rgba(64, 158, 255, 0.15);
}

.form-tip {
  margin-left: 10px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.tools-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 12px;
}

.tools-stats {
  display: flex;
  gap: 40px;
}

.tools-stats :deep(.el-statistic__head) {
  color: rgba(255, 255, 255, 0.6);
}

.tools-stats :deep(.el-statistic__number) {
  color: rgba(255, 255, 255, 0.9);
  font-size: 32px;
  font-weight: 600;
}

.tools-stats .enabled :deep(.el-statistic__number) {
  color: #67c23a;
}

.tools-stats .disabled :deep(.el-statistic__number) {
  color: #f56c6c;
}

.tools-table {
  background: transparent !important;
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 12px;
  overflow: hidden;
}

.tools-table::before {
  display: none;
}

.tools-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.tools-table :deep(.el-table__header-wrapper) {
  background: transparent !important;
}

.tools-table :deep(.el-table__header) {
  background: transparent !important;
}

.tools-table :deep(.el-table__header th) {
  background: rgba(26, 31, 58, 0.8) !important;
  color: rgba(255, 255, 255, 0.9) !important;
  border-bottom: 1px solid rgba(64, 158, 255, 0.3);
  font-weight: 600;
}

.tools-table :deep(.el-table__header th .cell) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 600;
}

.tools-table :deep(.el-table__header-wrapper tr),
.tools-table :deep(.el-table__header-wrapper thead) {
  background: transparent !important;
}

.tools-table :deep(.el-table__body tr) {
  background: rgba(255, 255, 255, 0.02) !important;
  color: rgba(255, 255, 255, 0.85);
}

.tools-table :deep(.el-table__body tr:hover) {
  background: rgba(64, 158, 255, 0.1) !important;
}

.tools-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
  background: transparent !important;
}

.tools-table :deep(.el-table__body td .cell) {
  color: rgba(255, 255, 255, 0.85);
}

.tools-table :deep(.el-table__inner-wrapper) {
  background: transparent !important;
}

.tools-table :deep(.el-table__body-wrapper) {
  background: transparent !important;
}

.tools-table :deep(.el-table__empty-block) {
  background: transparent !important;
}

.tools-table :deep(.el-table__empty-text) {
  color: rgba(255, 255, 255, 0.5);
}

.tools-table :deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background-color: rgba(64, 158, 255, 0.1) !important;
}

.tools-table :deep(.el-table__fixed),
.tools-table :deep(.el-table__fixed-right) {
  background: rgba(255, 255, 255, 0.03) !important;
}

.tools-table :deep(.disabled-row) {
  opacity: 0.4;
  background: rgba(0, 0, 0, 0.2) !important;
}

.tools-table :deep(.disabled-row):hover {
  opacity: 0.6;
}

.tools-table :deep(.disabled-row) td {
  background: rgba(0, 0, 0, 0.2) !important;
}

.tool-name {
  font-weight: 600;
  color: #409eff;
  font-family: 'Courier New', monospace;
}

.path-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.path-tip code {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 3px;
  color: #67c23a;
  font-family: 'Courier New', monospace;
}

.path-help {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(103, 194, 58, 0.1);
  border: 1px solid rgba(103, 194, 58, 0.3);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.path-help a {
  color: #67c23a;
  text-decoration: none;
  font-weight: 600;
}

.path-help a:hover {
  text-decoration: underline;
}

:deep(.el-dialog) {
  background: rgba(26, 31, 58, 0.95);
  border: 1px solid rgba(64, 158, 255, 0.3);
  backdrop-filter: blur(20px);
}

:deep(.el-dialog__title) {
  color: rgba(255, 255, 255, 0.9);
}

:deep(.el-dialog__body) {
  color: rgba(255, 255, 255, 0.85);
}

:deep(.el-dialog) .el-form-item__label {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.el-dialog) .el-input__inner,
:deep(.el-dialog) .el-textarea__inner,
:deep(.el-dialog) .el-input-number input {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(64, 158, 255, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

:deep(.el-dialog) .el-input__inner:focus,
:deep(.el-dialog) .el-textarea__inner:focus {
  border-color: #409eff;
  background: rgba(255, 255, 255, 0.08);
}

:deep(.el-dialog) .el-input-group__prepend {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(64, 158, 255, 0.3);
  color: rgba(255, 255, 255, 0.6);
}
</style>
