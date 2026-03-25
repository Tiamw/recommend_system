<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const mode = ref('login')
const form = ref({ username: '', password: '' })

const submitLabel = computed(() => (mode.value === 'login' ? '登录并进入系统' : '注册并自动登录'))

async function submit() {
  try {
    if (mode.value === 'login') {
      await authStore.loginUser(form.value)
    } else {
      await authStore.registerUser(form.value)
    }
    await router.push(route.query.redirect || '/profile')
  } catch {
    // 错误信息已写入 store，这里不重复处理。
  }
}
</script>

<template>
  <section class="auth-layout">
    <div class="auth-panel auth-panel--intro">
      <p class="eyebrow">Identity</p>
      <h2>登录后，把推荐、历史和收藏串成一条线</h2>
      <p>
        登录后你就可以直接把推荐结果加入历史、同步收藏夹，并在个人中心里查看自己的观看轨迹。
      </p>
      <div class="auth-switcher">
        <button :class="['ghost-button', mode === 'login' && 'is-active']" type="button" @click="mode = 'login'">登录</button>
        <button :class="['ghost-button', mode === 'register' && 'is-active']" type="button" @click="mode = 'register'">注册</button>
      </div>
    </div>

    <form class="auth-panel" @submit.prevent="submit">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="form.username" type="text" minlength="3" maxlength="50" required />
      </label>
      <label class="field">
        <span>密码</span>
        <input v-model="form.password" type="password" minlength="6" maxlength="128" required />
      </label>
      <p v-if="authStore.errorMessage" class="status status-error">{{ authStore.errorMessage }}</p>
      <button class="primary-button" type="submit" :disabled="authStore.loading">
        {{ authStore.loading ? '提交中...' : submitLabel }}
      </button>
    </form>
  </section>
</template>
