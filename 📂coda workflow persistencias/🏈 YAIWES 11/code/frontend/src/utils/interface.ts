export interface Message {
  id: string
  msg_type: 'system' | 'solve_step' | 'approval'
  content?: string | null
  created_at?: string
}

export interface SystemMessage extends Message {
  msg_type: 'system'
  type: 'info' | 'warning' | 'success' | 'error'
}

export interface SolveStepMessage extends Message {
  msg_type: 'solve_step'
  step_num: number
  phase: 'recon' | 'exploit' | 'report'
  think: string
  tool_calls: Array<{ tool_name: string; arguments: Record<string, unknown> }>
  tool_names: string[]
  output: string
  analysis: string
  flag_found: boolean
  flag_value?: string
  stuck_warning: boolean
  vulnerability?: Record<string, unknown>
  token_stats: Record<string, unknown>
  cache_stats: Record<string, unknown>
}

export interface ApprovalMessage extends Message {
  msg_type: 'approval'
  checkpoint_id: string
  prompt: { message: string; type: string }
  options: string[]
  timeout: number
}

export type AnyMessage = SystemMessage | SolveStepMessage | ApprovalMessage | Message

export interface TaskInfo {
  task_id: string
  status: string
  mode: string
  created_at?: string
  message_count?: number
}
