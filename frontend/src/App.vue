<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'

import { useAuthStore } from './stores/auth'
import { useLibraryStore } from './stores/library'
import { fetchHealth } from './api'

const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const router = useRouter()

const userName = computed(() => authStore.user?.username || '游客')
const isAuthenticated = computed(() => authStore.isAuthenticated)

async function logout() {
  authStore.clearSession()
  libraryStore.reset()
  await router.push('/')
}

onMounted(async () => {
  try {
    await fetchHealth()
  } catch {
    // 这里静默探测后端状态，避免首次打开页面就弹出错误。
  }
})
</script>

<template>
  <div class="app-shell">
    <div class="ambient ambient-left"></div>
    <div class="ambient ambient-right"></div>
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <span class="brand-badge">AR</span>
        <div>
          <p class="brand-kicker">Mini Anime Rec</p>
          <h1>动漫推荐与收藏站</h1>
        </div>
      </RouterLink>
      <nav class="nav-links">
        <RouterLink to="/">推荐首页</RouterLink>
        <RouterLink to="/anime">全部动漫</RouterLink>
        <RouterLink to="/profile">个人中心</RouterLink>
        <RouterLink v-if="!isAuthenticated" to="/auth">登录 / 注册</RouterLink>
        <button v-else class="ghost-button" type="button" @click="logout">退出 {{ userName }}</button>
      </nav>
    </header>

    <main class="page-wrap">
      <RouterView />
    </main>
  </div>
</template>
