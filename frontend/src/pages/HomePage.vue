<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import AnimeCard from '../components/AnimeCard.vue'
import AnimeDetailDrawer from '../components/AnimeDetailDrawer.vue'
import { fetchAnimeDetail, fetchAnimeList, fetchRecommendations } from '../api'
import { useAuthStore } from '../stores/auth'
import { useLibraryStore } from '../stores/library'

const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const heroMessage = ref('')
const recommendations = ref([])
const trending = ref([])
const detailOpen = ref(false)
const detailLoading = ref(false)
const detailAnime = ref(null)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const favoriteIds = computed(() => libraryStore.favoriteIds)

async function loadHomeFeed() {
  loading.value = true
  errorMessage.value = ''
  heroMessage.value = ''

  try {
    if (isAuthenticated.value) {
      await Promise.allSettled([libraryStore.loadHistory(), libraryStore.loadFavorites()])
      const preferenceIds = libraryStore.preferenceIds
      if (preferenceIds.length) {
        const { data } = await fetchRecommendations({
          raw_anime_history: preferenceIds,
          top_k: 10,
        })
        recommendations.value = data.items
        heroMessage.value = '这是系统根据你的观看历史和收藏偏好自动生成的推荐流。'
      } else {
        const { data } = await fetchAnimeList({ page: 1, page_size: 10 })
        recommendations.value = data.items
        heroMessage.value = '你还没有历史和收藏记录，先从高分动漫开始逛起。'
      }
    } else {
      const { data } = await fetchAnimeList({ page: 1, page_size: 10 })
      recommendations.value = data.items
      heroMessage.value = '登录后这里会自动切换成属于你的推荐流。'
    }

    const trendingResponse = await fetchAnimeList({ page: 1, page_size: 6 })
    trending.value = trendingResponse.data.items
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '首页数据加载失败，请确认后端已经启动。'
  } finally {
    loading.value = false
  }
}

async function openDetail(animeId) {
  detailOpen.value = true
  detailLoading.value = true
  try {
    const { data } = await fetchAnimeDetail(animeId)
    detailAnime.value = data
  } finally {
    detailLoading.value = false
  }
}

async function markAsWatched(animeId) {
  if (!isAuthenticated.value) {
    await router.push('/auth')
    return
  }

  try {
    await libraryStore.createHistory(animeId)
    await loadHomeFeed()
    heroMessage.value = `已将动漫 ${animeId} 加入历史，推荐流已根据新偏好刷新。`
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '追加观看历史失败。'
  }
}

async function toggleFavorite(animeId) {
  if (!isAuthenticated.value) {
    await router.push('/auth')
    return
  }

  try {
    if (favoriteIds.value.has(animeId)) {
      await libraryStore.deleteFavorite(animeId)
      await loadHomeFeed()
      heroMessage.value = `已取消收藏动漫 ${animeId}，推荐流已重新计算。`
    } else {
      await libraryStore.createFavorite(animeId)
      await loadHomeFeed()
      heroMessage.value = `已收藏动漫 ${animeId}，推荐流已根据收藏偏好刷新。`
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '收藏操作失败。'
  }
}

onMounted(loadHomeFeed)
</script>

<template>
  <section class="hero-grid hero-grid--wide">
    <div class="hero-panel hero-panel--feature">
      <p class="eyebrow">For You</p>
      <h2>首页直接展示系统推送的动漫推荐</h2>
      <p class="hero-copy">
        {{ heroMessage || '系统会结合你的观看历史、收藏和高分内容，在主页持续展示值得点开的动漫。' }}
      </p>
      <div class="action-row">
        <button class="primary-button" type="button" @click="loadHomeFeed" :disabled="loading">
          {{ loading ? '正在刷新推荐...' : '刷新推荐流' }}
        </button>
        <RouterLink class="ghost-button nav-button" to="/anime">浏览全部动漫</RouterLink>
      </div>
      <p v-if="errorMessage" class="status status-error">{{ errorMessage }}</p>
    </div>

    <div class="control-panel spotlight-panel">
      <p class="eyebrow">Trending Shelf</p>
      <h3>站内热门浏览</h3>
      <ul class="spotlight-list">
        <li v-for="item in trending" :key="item.anime_id">
          <button type="button" @click="openDetail(item.anime_id)">
            <strong>{{ item.name }}</strong>
            <span>{{ item.type || '未知类型' }} · 评分 {{ item.rating ?? '暂无' }}</span>
          </button>
        </li>
      </ul>
    </div>
  </section>

  <section class="section-head">
    <div>
      <p class="eyebrow">Feed</p>
      <h3>推荐流</h3>
    </div>
    <p>{{ recommendations.length ? `当前展示 ${recommendations.length} 部动漫` : '正在等待推荐结果' }}</p>
  </section>

  <section class="card-grid">
    <AnimeCard
      v-for="item in recommendations"
      :key="item.anime_id"
      :item="item"
      :favorite-ids="favoriteIds"
      @view-detail="openDetail"
      @add-history="markAsWatched"
      @toggle-favorite="toggleFavorite"
    />
  </section>

  <AnimeDetailDrawer
    :open="detailOpen"
    :anime="detailAnime"
    :loading="detailLoading"
    @close="detailOpen = false"
  />
</template>
