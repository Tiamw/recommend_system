import axios from 'axios'

import router from '../router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('anime-rec-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('anime-rec-token')
      localStorage.removeItem('anime-rec-user')
      if (router.currentRoute.value.name !== 'auth') {
        router.push({ name: 'auth' })
      }
    }
    return Promise.reject(error)
  },
)

export default api
