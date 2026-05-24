import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    if (typeof msg === 'string') {
      ElMessage.error(msg)
    } else if (Array.isArray(msg)) {
      ElMessage.error(msg.map((e: any) => e.msg).join('; '))
    } else {
      ElMessage.error('请求失败')
    }
    return Promise.reject(error)
  }
)

export default api
