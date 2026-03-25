<script setup>
import { computed, onMounted, ref } from 'vue'

import AnimeCard from '../components/AnimeCard.vue'
import AnimeDetailDrawer from '../components/AnimeDetailDrawer.vue'
import { fetchAnimeDetail } from '../api'
import { useAuthStore } from '../stores/auth'
import { useLibraryStore } from '../stores/library'

const authStore = useAuthStore()
const libraryStore = useLibraryStore()

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailAnime = ref(null)
const statusMessage = ref('')
const errorMessage = ref('')

const favoriteIds = computed(() => libraryStore.favoriteIds)

async function loadProfileData() {
  errorMessage.value = ''
  await Promise.allSettled([libraryStore.loadHistory(), libraryStore.loadFavorites()])
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

async function addHistory(animeId) {
  try {
    await libraryStore.createHistory(animeId)
    statusMessage.value = `已将动漫 ${animeId} 加入历史。`
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '写入历史失败。'
  }
}

async function toggleFavorite(animeId) {
  try {
    if (favoriteIds.value.has(animeId)) {
      await libraryStore.deleteFavorite(animeId)
      statusMessage.value = `已移除收藏 ${animeId}。`
    } else {
      await libraryStore.createFavorite(animeId)
      statusMessage.value = `已收藏动漫 ${animeId}。`
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '收藏操作失败。'
  }
}

onMounted(loadProfileData)
</script>

<template>
  <section class="profile-banner">
    <div>
      <p class="eyebrow">Profile</p>
      <h2>{{ authStore.user?.username }} 的个人中心</h2>
      <p>这里会展示观看历史和收藏夹，方便你回看推荐轨迹。</p>
    </div>
    <button class="ghost-button" type="button" @click="loadProfileData">刷新数据</button>
  </section>

  <p v-if="errorMessage" class="status status-error">{{ errorMessage }}</p>
  <p v-if="statusMessage" class="status status-success">{{ statusMessage }}</p>

  <section class="section-head">
    <div>
      <p class="eyebrow">History</p>
      <h3>观看历史</h3>
    </div>
    <p>{{ libraryStore.history.length }} 条记录</p>
  </section>
  <section class="card-grid">
    <AnimeCard
      v-for="item in libraryStore.history"
      :key="`history-${item.anime_id}-${item.watched_at}`"
      :item="item"
      :favorite-ids="favoriteIds"
      @view-detail="openDetail"
      @add-history="addHistory"
      @toggle-favorite="toggleFavorite"
    />
  </section>

  <section class="section-head">
    <div>
      <p class="eyebrow">Favorites</p>
      <h3>收藏夹</h3>
    </div>
    <p>{{ libraryStore.favorites.length }} 条收藏</p>
  </section>
  <section class="card-grid">
    <AnimeCard
      v-for="item in libraryStore.favorites"
      :key="`favorite-${item.anime_id}-${item.created_at}`"
      :item="item"
      :favorite-ids="favoriteIds"
      @view-detail="openDetail"
      @add-history="addHistory"
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
