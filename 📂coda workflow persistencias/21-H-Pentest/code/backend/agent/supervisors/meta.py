"""
Meta Supervisor - 元层Agent
负责：全局协调、质量控制、异常处理
"""
from typing import Dict, Any, List
from agent.core.llm import LLMClient
from agent.core.output import OutputManager


class MetaSupervisor:
    """元督导 - 全局协调和质量控制"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        output_manager: OutputManager,
        max_rounds: int = 30,
        mode: str = 'ctf'  # 🔥 添加模式参数
    ):
        self.llm = llm_client
        self.output = output_manager
        self.max_rounds = max_rounds
        self.mode = mode.lower()  # ctf 或 realworld
        self.context_mgr = None  # 🔥 将由Agent注入
        
        self.execution_history = []
        self.quality_checks = []
    
    async def should_force_stop(
        self,
        current_round: int,
        execution_results: List[Dict],
        conversation_history: List[Dict],
        flags_found: List[str]
    ) -> Dict[str, Any]:
        """
        🔥🔥🔥 Meta自主决策：是否强制停止
        
        区分模式：
        - CTF模式：尽可能在真正获取到真flag前不停止
        - RW模式：自己判断，但不要过早放弃
        
        Returns:
            {
                'should_stop': True/False,
                'reason': '停止原因',
                'confidence': 0.0-1.0
            }
        """
        # 1. 达到最大轮数
        if current_round >= self.max_rounds:
            return {
                'should_stop': True,
                'reason': f'达到最大轮数 {self.max_rounds}',
                'confidence': 1.0
            }
        
        # 2. CTF模式：只有确认是真flag才停止
        if self.mode == 'ctf':
            if flags_found:
                # 🔥 使用LLM验证flag是否真实
                is_real_flag = await self._verify_flag_authenticity(
                    flags_found,
                    conversation_history
                )
                
                if is_real_flag:
                    return {
                        'should_stop': True,
                        'reason': f'已获取到真flag: {flags_found[0]}',
                        'confidence': 0.95
                    }
                else:
                    self.output.log("warning", "⚠️  检测到flag但不确定真实性，继续执行")
                    return {'should_stop': False, 'reason': 'flag不确定', 'confidence': 0.3}
            else:
                # CTF模式下，只要还没到最大轮数就继续
                return {'should_stop': False, 'reason': '未找到flag，继续搜索', 'confidence': 0.8}
        
        # 3. RW模式：使用LLM智能判断
        elif self.mode == 'realworld':
            # 检查是否陷入死循环（连续10轮无进展）
            if len(execution_results) >= 10:
                recent_10 = execution_results[-10:]
                no_progress = all(
                    r.get('tool_calls', 0) == 0 or r.get('status') == 'failed'
                    for r in recent_10
                )
                
                if no_progress:
                    return {
                        'should_stop': True,
                        'reason': '连续10轮无进展，陷入死循环',
                        'confidence': 0.85
                    }
            
            # 🔥 使用LLM智能判断是否应该停止
            llm_decision = await self._llm_decide_stop(
                current_round,
                execution_results,
                conversation_history
            )
            
            return llm_decision
        
        return {'should_stop': False, 'reason': '继续执行', 'confidence': 0.5}
    
    def _detect_loop(self, results: List[Dict]) -> bool:
        """检测是否陷入循环（重复执行相同任务）"""
        if len(results) < 6:
            return False
        
        recent = results[-6:]
        contents = [r.get('content', '')[:100] for r in recent]
        
        # 简单检测：如果最近6条中有4条内容相似
        from collections import Counter
        counter = Counter(contents)
        most_common_count = counter.most_common(1)[0][1] if counter else 0
        
        return most_common_count >= 4
    
    async def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证单个结果的质量
        
        Returns:
            {
                'valid': True/False,
                'confidence': 0.0-1.0,
                'issues': [...],
                'suggestions': [...]
            }
        """
        validation = {
            'valid': True,
            'confidence': 0.7,
            'issues': [],
            'suggestions': []
        }
        
        # 检查结果完整性
        if not result.get('content'):
            validation['issues'].append("结果内容为空")
            validation['confidence'] -= 0.3
        
        # 检查是否有错误
        content = str(result.get('content', '')).lower()
        if any(err in content for err in ['error', '错误', 'failed', '失败']):
            validation['issues'].append("执行中有错误")
            validation['confidence'] -= 0.2
        
        # 检查是否有有价值信息
        if any(kw in content for kw in ['flag', 'vuln', '成功', 'success']):
            validation['confidence'] += 0.2
        
        validation['confidence'] = max(0.0, min(1.0, validation['confidence']))
        validation['valid'] = validation['confidence'] > 0.4
        
        return validation
    
    async def quality_control(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        质量控制检查
        
        Returns:
            质量报告
        """
        self.output.log("info", "🔍 Meta Supervisor: 质量检查...")
        
        total = len(results)
        if total == 0:
            return {'score': 0.0, 'issues': ['无执行结果']}
        
        # 验证每个结果
        validations = []
        for r in results:
            val = await self.validate_result(r)
            validations.append(val)
        
        # 计算总体质量分数
        avg_confidence = sum(v['confidence'] for v in validations) / len(validations)
        valid_count = sum(1 for v in validations if v['valid'])
        
        quality_report = {
            'score': avg_confidence,
            'total_results': total,
            'valid_results': valid_count,
            'invalid_results': total - valid_count,
            'issues': [],
            'suggestions': []
        }
        
        # 收集所有问题
        all_issues = []
        for v in validations:
            all_issues.extend(v['issues'])
        
        # 统计常见问题
        from collections import Counter
        issue_counter = Counter(all_issues)
        quality_report['issues'] = [
            f"{issue}: {count}次" 
            for issue, count in issue_counter.most_common(3)
        ]
        
        # 生成建议
        if avg_confidence < 0.5:
            quality_report['suggestions'].append("整体质量较低，建议调整执行策略")
        
        if valid_count < total * 0.6:
            quality_report['suggestions'].append("有效结果占比低，建议优化工具调用")
        
        self.output.log("info", f"📊 质量分数: {avg_confidence:.2f}, 有效率: {valid_count}/{total}")
        
        return quality_report
    
    async def handle_exception(self, exception: Exception, context: Dict[str, Any]) -> str:
        """
        异常处理和恢复建议
        
        Returns:
            恢复策略
        """
        self.output.log("error", f"❌ Meta Supervisor: 处理异常 - {str(exception)}")
        
        error_type = type(exception).__name__
        
        recovery_strategies = {
            'TimeoutError': '增加超时时间，或分解任务',
            'ConnectionError': '检查网络连接，重试请求',
            'ValueError': '检查输入参数格式',
            'KeyError': '检查数据结构完整性',
        }
        
        strategy = recovery_strategies.get(error_type, '记录错误，继续执行其他任务')
        
        self.output.log("info", f"🔧 恢复策略: {strategy}")
        
        return strategy
    
    async def generate_meta_insights(self, execution_data: Dict[str, Any], conversation_history: List[Dict] = None) -> List[str]:
        """
        生成元层洞察（高层次的观察和建议，🔥 传递完整对话）
        
        Args:
            execution_data: 执行数据
            conversation_history: 完整对话历史
        
        Returns:
            洞察列表
        """
        insights = []
        
        # 分析执行效率
        total_rounds = execution_data.get('total_rounds', 0)
        time_per_round = execution_data.get('total_time', 0) / max(total_rounds, 1)
        
        if time_per_round > 60:
            insights.append(f"⚠️  每轮平均耗时 {time_per_round:.1f}秒，较慢")
        
        # 分析工具使用
        tool_usage = execution_data.get('tool_usage', {})
        if tool_usage:
            most_used = max(tool_usage.items(), key=lambda x: x[1])
            insights.append(f"🔧 最常用工具: {most_used[0]} ({most_used[1]}次)")
        
        # 分析成功率
        success_rate = execution_data.get('success_rate', 0)
        if success_rate < 0.5:
            insights.append(f"⚠️  成功率仅 {success_rate*100:.1f}%，建议优化")
        elif success_rate > 0.8:
            insights.append(f"✅ 成功率高达 {success_rate*100:.1f}%")
        
        # 🔥 使用LLM生成深度洞察（传递完整对话）
        if conversation_history and len(conversation_history) > 0:
            messages = conversation_history.copy()
            
            prompt = f"""分析渗透测试进度，提供3-5条元层洞察。

执行数据：轮数={total_rounds}, 耗时={time_per_round:.1f}s/轮, 成功率={success_rate*100:.1f}%, 工具={tool_usage}

要求：
1. 每条不超过50字
2. 直接输出，每行一条
3. 不要序号和额外说明

关注：战略建议、潜在问题、优化方向
"""
            
            messages.append({'role': 'user', 'content': prompt})
            
            # 🔥 检查tokens，大于120k*0.8就压缩
            if self.context_mgr:
                current_tokens = self.context_mgr.count_messages_tokens(messages)
                threshold = int(120000 * 0.8)
                
                if current_tokens > threshold:
                    self.output.log("warning", f"⚠️  Meta: 对诏tokens过大 ({current_tokens}/{threshold})")
                    self.output.log("info", "🗜️  触发LangChain智能压缩...")
                    
                    messages = await self.context_mgr.smart_compress(
                        messages,
                        keep_recent=5,
                        target_ratio=0.5
                    )
                    
                    new_tokens = self.context_mgr.count_messages_tokens(messages)
                    self.output.log("success", f"✅ 压缩完成: {current_tokens} -> {new_tokens} tokens")
            
            try:
                response = await self.llm.chat(
                    messages=messages,
                    temperature=0.7,
                    stream=True  # 🔥🔥🔥 全流式输出
                )
                
                llm_insights = response.get('content', '').strip().split('\n')
                insights.extend([i.strip() for i in llm_insights if i.strip() and len(i.strip()) > 5])
            
            except Exception as e:
                self.output.log("warning", f"⚠️  LLM生成洞察失败: {e}")
        
        return insights[:8]  # 最多8条
    
    async def _verify_flag_authenticity(
        self,
        flags: List[str],
        conversation_history: List[Dict]
    ) -> bool:
        """
        🔥 验证flag是否真实（使用LLM分析）
        
        Args:
            flags: 找到的flag列表
            conversation_history: 对话历史
        
        Returns:
            True 如果是真flag
        """
        if not flags:
            return False
        
        # 构建提示词
        prompt = f"""你是一个CTF专家，请判断以下找到的flag是否是真实的目标flag。

找到的flag: {flags[0]}

判断标准：
1. flag格式正确（通常为flag{{...}}或flag{{.*}}格式）
2. flag是通过漏洞利用获取的，不是页面上的假flag
3. flag出现在关键位置（如数据库、文件系统、命令执行结果）

请分析最近的对话，判断这个flag的真实性。

只输出：
- "REAL" 如果是真flag
- "FAKE" 如果不确定或是假flag
"""
        
        # 准备消息（只保留最近10条）
        messages = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history.copy()
        messages.append({'role': 'user', 'content': prompt})
        
        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.1,  # 低温度，更确定
                stream=False
            )
            
            content = response.get('content', '').strip().upper()
            
            if 'REAL' in content:
                self.output.log("success", "✅ Meta: Flag验证通过，确认为真flag")
                return True
            else:
                self.output.log("warning", "⚠️  Meta: Flag验证未通过，可能是假flag")
                return False
        
        except Exception as e:
            self.output.log("error", f"❌ Flag验证失败: {e}")
            # 默认为真，避免过早停止
            return True
    
    async def _llm_decide_stop(
        self,
        current_round: int,
        execution_results: List[Dict],
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        🔥 RW模式：使用LLM智能判断是否停止
        
        Args:
            current_round: 当前轮次
            execution_results: 执行结果
            conversation_history: 对话历史
        
        Returns:
            {'should_stop': bool, 'reason': str, 'confidence': float}
        """
        # 统计信息
        total_rounds = len(execution_results)
        tool_calls = sum(r.get('tool_calls', 0) for r in execution_results)
        recent_5 = execution_results[-5:] if len(execution_results) > 5 else execution_results
        recent_tool_calls = sum(r.get('tool_calls', 0) for r in recent_5)
        
        # 构建提示词
        prompt = f"""你是一个渗透测试Meta监督，请判断当前测试是否应该停止。

当前状态：
- 轮次: {current_round}/{self.max_rounds}
- 总工具调用: {tool_calls}
- 最近5轮工具调用: {recent_tool_calls}

判断标准：
1. **不要过早放弃**: 只有当确定无法继续时才停止
2. **检查进展**: 如果最近还有工具调用，说明还在探索
3. **检查成果**: 是否发现了足够的漏洞
4. **避免死循环**: 如果连续无进展且重复相同操作

请分析最近的对话，判断是否应该停止。

只输出 JSON：
```json
{{
  "should_stop": true/false,
  "reason": "停止或继续的原因",
  "confidence": 0.0-1.0
}}
```
"""
        
        # 准备消息（只保留最近15条）
        messages = conversation_history[-15:] if len(conversation_history) > 15 else conversation_history.copy()
        messages.append({'role': 'user', 'content': prompt})
        
        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,
                stream=False,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.get('content', '{}')
            decision = json.loads(content)
            
            should_stop = decision.get('should_stop', False)
            reason = decision.get('reason', '未知')
            confidence = decision.get('confidence', 0.5)
            
            if should_stop:
                self.output.log("warning", f"🛑 Meta决定停止: {reason} (置信度: {confidence})")
            else:
                self.output.log("info", f"▶️  Meta决定继续: {reason}")
            
            return {
                'should_stop': should_stop,
                'reason': reason,
                'confidence': confidence
            }
        
        except Exception as e:
            self.output.log("error", f"❌ LLM决策失败: {e}")
            # 默认继续，避免过早停止
            return {
                'should_stop': False,
                'reason': 'LLM决策失败，默认继续',
                'confidence': 0.3
            }
