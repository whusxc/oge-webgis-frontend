// DeepSeek AI 服务
// 离线模式下提供模拟回复

const OFFLINE_MODE = true

// 模拟回复数据
const mockReplies = [
  "您好！我是OGE智能助手。当前运行在离线模式下，无法提供真实的AI分析功能。",
  "在离线模式下，我可以为您展示界面功能，但无法进行实际的地理空间分析。",
  "要使用完整功能，请在内网环境中连接到遥感大楼的服务器。",
  "您可以通过左侧工具箱查看可用的分析工具，或浏览地图界面。",
  "如需帮助，请查看系统说明文档或联系技术支持。"
]

// DeepSeek服务配置
const deepseekConfig = {
  apiKey: process.env.DEEPSEEK_API_KEY || '',
  baseUrl: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat',
  maxTokens: 2000,
  temperature: 0.7
}

// DeepSeek服务类
class DeepSeekService {
  constructor(config = deepseekConfig) {
    this.config = config
    this.isOnline = !OFFLINE_MODE && !!config.apiKey
  }

  // 聊天接口
  async chat(message, sessionId = null, conversationHistory = []) {
    if (!this.isOnline) {
      // 离线模式：返回模拟回复
      return this.getMockReply(message)
    }

    try {
      // 在线模式：调用真实API
      const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          model: this.config.model,
          messages: [
            ...conversationHistory,
            { role: 'user', content: message }
          ],
          max_tokens: this.config.maxTokens,
          temperature: this.config.temperature
        })
      })

      if (!response.ok) {
        throw new Error(`DeepSeek API error: ${response.status}`)
      }

      const data = await response.json()
      return {
        content: data.choices[0].message.content,
        sessionId: sessionId || this.generateSessionId(),
        model: this.config.model,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('DeepSeek服务调用失败:', error)
      // 降级到模拟回复
      return this.getMockReply(message)
    }
  }

  // 获取模拟回复
  getMockReply(message) {
    // 根据用户消息选择合适的回复
    let reply = mockReplies[0] // 默认回复
    
    if (message.includes('地图') || message.includes('分析')) {
      reply = mockReplies[1]
    } else if (message.includes('功能') || message.includes('怎么')) {
      reply = mockReplies[3]
    } else if (message.includes('帮助') || message.includes('问题')) {
      reply = mockReplies[4]
    }

    return new Promise(resolve => {
      // 模拟网络延迟
      setTimeout(() => {
        resolve({
          content: reply,
          sessionId: this.generateSessionId(),
          model: 'offline-mock',
          timestamp: new Date().toISOString(),
          isOffline: true
        })
      }, 500 + Math.random() * 1000) // 0.5-1.5秒延迟
    })
  }

  // 生成会话ID
  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  // 检查服务状态
  async checkStatus() {
    return {
      online: this.isOnline,
      mode: this.isOnline ? 'online' : 'offline',
      model: this.isOnline ? this.config.model : 'offline-mock',
      timestamp: new Date().toISOString()
    }
  }
}

// 创建服务实例
export const deepseekService = new DeepSeekService()

// 默认导出
export default deepseekService 