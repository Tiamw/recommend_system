import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { login, register } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('anime-rec-token') || '')
  const user = ref(JSON.parse(localStorage.getItem('anime-rec-user') || 'null'))
  const loading = ref(false)
  const errorMessage = ref('')

  const isAuthenticated = computed(() => Boolean(token.value))

  function persistSession(nextToken, nextUser) {
    token.value = nextToken
    user.value = nextUser
    localStorage.setItem('anime-rec-token', nextToken)
    localStorage.setItem('anime-rec-user', JSON.stringify(nextUser))
  }

  function clearSession() {
    token.value = ''
    user.value = null
    localStorage.removeItem('anime-rec-token')
    localStorage.removeItem('anime-rec-user')
  }

  async function handleAuth(action, payload) {
    loading.value = true
    errorMessage.value = ''
    try {
      const { data } = await action(payload)
      if (data.access_token) {
        persistSession(data.access_token, data.user)
      }
      return data
    } catch (error) {
      errorMessage.value = error.response?.data?.detail || '请求失败，请稍后再试。'
      throw error
    } finally {
      loading.value = false
    }
  }

  async function loginUser(payload) {
    return handleAuth(login, payload)
  }

  async function registerUser(payload) {
    loading.value = true
    errorMessage.value = ''
    try {
      await register(payload)
      return await handleAuth(login, payload)
    } catch (error) {
      errorMessage.value = error.response?.data?.detail || '注册失败，请稍后再试。'
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    token,
    user,
    loading,
    errorMessage,
    isAuthenticated,
    loginUser,
    registerUser,
    clearSession,
  }
})
