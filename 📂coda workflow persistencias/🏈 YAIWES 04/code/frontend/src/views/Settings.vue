<template>
  <div class="space-y-6">
    <!-- 设置选项卡 -->
    <t-tabs v-model="activeTab">
      <t-tab-panel value="agents" label="智能体模型配置">
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 mt-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-white">智能体模型配置</h3>
            <t-button theme="primary" size="small" @click="testAllConnections" :loading="testing">
              测试所有连接
            </t-button>
          </div>
          
          <div class="text-sm text-gray-400 mb-6">
            为每个智能体单独配置使用的大模型，实现专业的团队协作。不同智能体可以使用不同的模型以获得最佳效果。
          </div>
          
          <!-- 智能体配置卡片 -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div 
              v-for="agent in agentModels" 
              :key="agent.name"
              class="bg-dark-700 rounded-lg p-4 border border-dark-500"
              :class="{ 'border-cyber-blue': agent.enabled }"
            >
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div 
                    class="w-10 h-10 rounded-lg flex items-center justify-center"
                    :style="{ backgroundColor: agent.color + '20' }"
                  >
                    <span class="text-lg">{{ agent.icon }}</span>
                  </div>
                  <div>
                    <h4 class="text-white font-medium">{{ agent.display_name }}</h4>
                    <p class="text-xs text-gray-400">{{ agent.role }}</p>
                  </div>
                </div>
                <t-switch v-model="agent.enabled" @change="toggleAgent(agent.name, agent.enabled)" />
              </div>
              
              <t-form :data="agent" label-align="left" label-width="100px" size="small">
                <t-form-item label="模型提供商">
                  <t-select v-model="agent.provider" class="w-full" @change="onProviderChange(agent)">
                    <t-option v-for="(info, key) in providers" :key="key" :value="key" :label="info.description || key" />
                  </t-select>
                </t-form-item>
                
                <t-form-item label="模型名称">
                  <t-input v-model="agent.model_name" placeholder="如: deepseek-chat" class="w-full" />
                </t-form-item>
                
                <t-form-item label="API Key">
                  <t-input 
                    v-model="agent.api_key" 
                    type="password"
                    placeholder="输入API密钥"
                    class="w-full"
                  />
                </t-form-item>
                
                <t-form-item label="Base URL" v-if="agent.provider === 'custom' || agent.provider === 'openai'">
                  <t-input 
                    v-model="agent.base_url" 
                    placeholder="自定义API地址"
                    class="w-full"
                  />
                </t-form-item>
                
                <t-form-item label="Temperature">
                  <t-slider v-model="agent.temperature" :min="0" :max="1" :step="0.1" class="w-48" />
                  <span class="ml-2 text-gray-400 text-xs">{{ agent.temperature }}</span>
                </t-form-item>
                
                <t-form-item label="Max Tokens">
                  <t-input-number v-model="agent.max_tokens" :min="256" :max="8192" :step="256" />
                </t-form-item>
              </t-form>
              
              <div class="flex justify-end gap-2 mt-4">
                <t-button size="small" variant="outline" @click="testConnection(agent.name)" :loading="agent.testing">
                  测试连接
                </t-button>
                <t-button size="small" theme="primary" @click="saveAgentConfig(agent)">
                  保存
                </t-button>
              </div>
            </div>
          </div>
        </div>
      </t-tab-panel>
      
      <t-tab-panel value="llm" label="默认模型配置">
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 mt-6">
          <h3 class="text-lg font-semibold text-white mb-6">默认大语言模型配置</h3>
          
          <div class="text-sm text-gray-400 mb-6">
            此配置为系统默认设置。建议在"智能体模型配置"中为各个智能体单独配置以获得最佳效果。
          </div>
          
          <t-form :data="llmConfig" label-align="left" label-width="120px">
            <t-form-item label="默认模型">
              <t-select v-model="llmConfig.provider" class="w-80">
                <t-option value="deepseek" label="DeepSeek" />
                <t-option value="glm" label="GLM (智谱AI)" />
                <t-option value="qwen" label="Qwen (阿里云)" />
                <t-option value="openai" label="OpenAI" />
              </t-select>
            </t-form-item>
            
            <t-form-item label="DeepSeek">
              <t-input 
                v-model="llmConfig.apiKeys.deepseek" 
                type="password"
                placeholder="请输入DeepSeek API Key"
                class="w-80"
              />
            </t-form-item>
            
            <t-form-item label="GLM API Key">
              <t-input 
                v-model="llmConfig.apiKeys.glm" 
                type="password"
                placeholder="请输入智谱AI API Key"
                class="w-80"
              />
            </t-form-item>
            
            <t-form-item label="Qwen API Key">
              <t-input 
                v-model="llmConfig.apiKeys.qwen" 
                type="password"
                placeholder="请输入阿里云Qwen API Key"
                class="w-80"
              />
            </t-form-item>
            
            <t-form-item label="OpenAI API Key">
              <t-input 
                v-model="llmConfig.apiKeys.openai" 
                type="password"
                placeholder="请输入OpenAI API Key"
                class="w-80"
              />
            </t-form-item>
            
            <t-form-item label="Temperature">
              <t-slider v-model="llmConfig.temperature" :min="0" :max="1" :step="0.1" />
            </t-form-item>
            
            <t-form-item label="Max Tokens">
              <t-input-number v-model="llmConfig.maxTokens" :min="100" :max="8192" />
            </t-form-item>
          </t-form>
        </div>
      </t-tab-panel>
      
      <t-tab-panel value="system" label="系统设置">
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 mt-6">
          <h3 class="text-lg font-semibold text-white mb-6">系统设置</h3>
          
          <t-form :data="systemConfig" label-align="left" label-width="120px">
            <t-form-item label="运行模式">
              <t-select v-model="systemConfig.mode" class="w-64">
                <t-option value="auto" label="自动模式" />
                <t-option value="semi" label="半自动模式" />
                <t-option value="manual" label="手动模式" />
              </t-select>
            </t-form-item>
            
            <t-form-item label="并发任务数">
              <t-input-number v-model="systemConfig.maxConcurrent" :min="1" :max="10" />
            </t-form-item>
            
            <t-form-item label="结果保存路径">
              <t-input v-model="systemConfig.resultsDir" class="w-64" />
            </t-form-item>
            
            <t-form-item label="日志级别">
              <t-select v-model="systemConfig.logLevel" class="w-64">
                <t-option value="DEBUG" label="DEBUG" />
                <t-option value="INFO" label="INFO" />
                <t-option value="WARNING" label="WARNING" />
                <t-option value="ERROR" label="ERROR" />
              </t-select>
            </t-form-item>
          </t-form>
        </div>
      </t-tab-panel>
      
      <t-tab-panel value="security" label="安全设置">
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 mt-6">
          <h3 class="text-lg font-semibold text-white mb-6">安全设置</h3>
          
          <t-form :data="securityConfig" label-align="left" label-width="150px">
            <t-form-item label="启用速率限制">
              <t-switch v-model="securityConfig.rateLimit" />
            </t-form-item>
            
            <t-form-item label="请求/分钟" v-if="securityConfig.rateLimit">
              <t-input-number v-model="securityConfig.requestsPerMinute" :min="10" :max="200" />
            </t-form-item>
            
            <t-form-item label="禁止测试的IP">
              <t-textarea 
                v-model="securityConfig.blocklist" 
                placeholder="每行一个IP或CIDR"
                :autosize="{ minRows: 4, maxRows: 8 }"
                class="w-96"
              />
            </t-form-item>
            
            <t-form-item label="禁止危险操作">
              <t-checkbox-group v-model="securityConfig.blockedOps">
                <t-checkbox value="ddos">DDoS攻击</t-checkbox>
                <t-checkbox value="malware">恶意软件部署</t-checkbox>
                <t-checkbox value="destruction">数据破坏</t-checkbox>
              </t-checkbox-group>
            </t-form-item>
          </t-form>
        </div>
      </t-tab-panel>
      
      <t-tab-panel value="report" label="报告设置">
        <div class="bg-dark-800 rounded-xl p-6 border border-dark-500 mt-6">
          <h3 class="text-lg font-semibold text-white mb-6">报告设置</h3>
          
          <t-form :data="reportConfig" label-align="left" label-width="150px">
            <t-form-item label="默认报告格式">
              <t-select v-model="reportConfig.defaultFormat" class="w-64">
                <t-option value="json" label="JSON" />
                <t-option value="html" label="HTML" />
                <t-option value="markdown" label="Markdown" />
              </t-select>
            </t-form-item>
            
            <t-form-item label="报告内容">
              <t-checkbox-group v-model="reportConfig.include">
                <t-checkbox value="summary">执行摘要</t-checkbox>
                <t-checkbox value="methodology">测试方法</t-checkbox>
                <t-checkbox value="details">漏洞详情</t-checkbox>
                <t-checkbox value="remediation">修复建议</t-checkbox>
              </t-checkbox-group>
            </t-form-item>
          </t-form>
        </div>
      </t-tab-panel>
    </t-tabs>

    <!-- 保存按钮 -->
    <div class="flex justify-end gap-4">
      <t-button variant="outline" @click="resetSettings">重置</t-button>
      <t-button theme="primary" @click="saveSettings" :loading="saving">保存设置</t-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi, modelApi, teamApi } from '../api'
import { MessagePlugin } from 'tdesign-vue-next'

const activeTab = ref('agents')
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

// 模型提供商
const providers = ref<Record<string, any>>({})

// 智能体模型配置
interface AgentModel {
  name: string
  display_name: string
  role: string
  color: string
  icon: string
  enabled: boolean
  provider: string
  model_name: string
  api_key: string
  base_url: string
  temperature: number
  max_tokens: number
  testing?: boolean
}

const agentModels = ref<AgentModel[]>([])

const llmConfig = ref({
  provider: '',
  apiKeys: {
    deepseek: '',
    glm: '',
    qwen: '',
    openai: '',
  },
  temperature: 0.7,
  maxTokens: 4096,
})

const systemConfig = ref({
  mode: '',
  maxConcurrent: 3,
  resultsDir: '',
  logLevel: 'INFO',
})

const securityConfig = ref({
  rateLimit: false,
  requestsPerMinute: 60,
  blocklist: '',
  blockedOps: [] as string[],
})

const reportConfig = ref({
  defaultFormat: '',
  include: [] as string[],
})

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const res = await configApi.get() as any
    const config = res.config || {}
    
    // 填充LLM配置
    if (config.llm_provider) {
      llmConfig.value.provider = config.llm_provider
    }
    if (config.api_keys) {
      llmConfig.value.apiKeys = { ...llmConfig.value.apiKeys, ...config.api_keys }
    }
    if (config.temperature !== undefined) {
      llmConfig.value.temperature = config.temperature
    }
    if (config.max_tokens) {
      llmConfig.value.maxTokens = config.max_tokens
    }
    
    // 填充系统配置
    if (config.system) {
      systemConfig.value = { ...systemConfig.value, ...config.system }
    }
    
    // 填充安全配置
    if (config.security) {
      securityConfig.value = { ...securityConfig.value, ...config.security }
    }
    
    // 填充报告配置
    if (config.report) {
      reportConfig.value = { ...reportConfig.value, ...config.report }
    }
  } catch (error) {
    console.error('Failed to load config:', error)
    MessagePlugin.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 保存设置
const saveSettings = async () => {
  saving.value = true
  try {
    await configApi.update({
      llm_provider: llmConfig.value.provider,
      api_keys: llmConfig.value.apiKeys,
      temperature: llmConfig.value.temperature,
      max_tokens: llmConfig.value.maxTokens,
    })
    MessagePlugin.success('设置已保存')
  } catch (error) {
    console.error('Failed to save config:', error)
    MessagePlugin.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// 重置设置
const resetSettings = async () => {
  await loadConfig()
  MessagePlugin.success('设置已重置')
}

// 加载模型提供商
const loadProviders = async () => {
  try {
    const res = await modelApi.getProviders() as any
    providers.value = res.providers || {}
  } catch (error) {
    console.error('Failed to load providers:', error)
  }
}

// 加载智能体配置
const loadAgentModels = async () => {
  try {
    const res = await teamApi.getStatus() as any
    const agents = res.agents || []
    
    agentModels.value = agents.map((agent: any) => ({
      name: agent.name,
      display_name: agent.display_name,
      role: agent.role,
      color: agent.color || '#00d4ff',
      icon: getAgentIcon(agent.name),
      enabled: agent.enabled ?? true,
      provider: agent.model_provider || 'deepseek',
      model_name: agent.model_name || '',
      api_key: '',
      base_url: '',
      temperature: 0.7,
      max_tokens: 4096,
      testing: false
    }))
  } catch (error) {
    console.error('Failed to load agent models:', error)
    // 使用默认配置
    agentModels.value = [
      { name: 'CoordinatorAgent', display_name: '协调者', role: '团队领导，负责协调和决策', color: '#ef4444', icon: '👑', enabled: true, provider: 'deepseek', model_name: 'deepseek-chat', api_key: '', base_url: '', temperature: 0.7, max_tokens: 4096 },
      { name: 'ReconAgent', display_name: '侦察专家', role: '信息收集和目标侦察', color: '#00d4ff', icon: '🔍', enabled: true, provider: 'deepseek', model_name: 'deepseek-chat', api_key: '', base_url: '', temperature: 0.7, max_tokens: 4096 },
      { name: 'VulnAgent', display_name: '漏洞分析师', role: '漏洞扫描和风险评估', color: '#8b5cf6', icon: '🐛', enabled: true, provider: 'deepseek', model_name: 'deepseek-chat', api_key: '', base_url: '', temperature: 0.7, max_tokens: 4096 },
      { name: 'ExploitAgent', display_name: '攻击专家', role: '漏洞利用和权限获取', color: '#f59e0b', icon: '🎯', enabled: true, provider: 'deepseek', model_name: 'deepseek-chat', api_key: '', base_url: '', temperature: 0.7, max_tokens: 4096 },
      { name: 'ReportAgent', display_name: '报告专家', role: '生成渗透测试报告', color: '#10b981', icon: '📝', enabled: true, provider: 'deepseek', model_name: 'deepseek-chat', api_key: '', base_url: '', temperature: 0.7, max_tokens: 4096 },
    ]
  }
}

const getAgentIcon = (name: string): string => {
  const icons: Record<string, string> = {
    'CoordinatorAgent': '👑',
    'ReconAgent': '🔍',
    'VulnAgent': '🐛',
    'ExploitAgent': '🎯',
    'ReportAgent': '📝'
  }
  return icons[name] || '🤖'
}

// 提供商变更
const onProviderChange = (agent: AgentModel) => {
  const provider = providers.value[agent.provider]
  if (provider) {
    if (!agent.model_name && provider.default_model) {
      agent.model_name = provider.default_model
    }
    if (!agent.base_url && provider.base_url) {
      agent.base_url = provider.base_url
    }
  }
}

// 切换智能体启用状态
const toggleAgent = async (name: string, enabled: boolean) => {
  try {
    await modelApi.toggleAgent(name, enabled)
    MessagePlugin.success(`${name} 已${enabled ? '启用' : '禁用'}`)
  } catch (error) {
    MessagePlugin.error('操作失败')
  }
}

// 测试单个连接
const testConnection = async (agentName: string) => {
  const agent = agentModels.value.find(a => a.name === agentName)
  if (!agent) return
  
  agent.testing = true
  try {
    // 先保存配置
    await saveAgentConfig(agent, false)
    
    // 测试连接
    const res = await modelApi.testConnection(agentName) as any
    if (res.status === 'success') {
      MessagePlugin.success(`${agent.display_name} 连接测试成功`)
    } else {
      MessagePlugin.error(`${agent.display_name} 连接失败: ${res.error}`)
    }
  } catch (error: any) {
    MessagePlugin.error(`连接测试失败: ${error.message || '未知错误'}`)
  } finally {
    agent.testing = false
  }
}

// 测试所有连接
const testAllConnections = async () => {
  testing.value = true
  let success = 0
  let failed = 0
  
  for (const agent of agentModels.value) {
    if (!agent.enabled) continue
    try {
      const res = await modelApi.testConnection(agent.name) as any
      if (res.status === 'success') {
        success++
      } else {
        failed++
      }
    } catch {
      failed++
    }
  }
  
  testing.value = false
  MessagePlugin.info(`测试完成: ${success} 个成功, ${failed} 个失败`)
}

// 保存智能体配置
const saveAgentConfig = async (agent: AgentModel, showMessage: boolean = true) => {
  try {
    await modelApi.updateAgent(agent.name, {
      provider: agent.provider,
      model_name: agent.model_name,
      api_key: agent.api_key || undefined,
      base_url: agent.base_url || undefined,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens
    })
    if (showMessage) {
      MessagePlugin.success(`${agent.display_name} 配置已保存`)
    }
  } catch (error) {
    if (showMessage) {
      MessagePlugin.error('保存配置失败')
    }
    throw error
  }
}

onMounted(async () => {
  await Promise.all([
    loadConfig(),
    loadProviders(),
    loadAgentModels()
  ])
})
</script>
