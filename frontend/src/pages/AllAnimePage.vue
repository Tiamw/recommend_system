<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AnimeCard from '../components/AnimeCard.vue'
import AnimeDetailDrawer from '../components/AnimeDetailDrawer.vue'
import { fetchAnimeDetail, fetchAnimeList } from '../api'
import { useAuthStore } from '../stores/auth'
import { useLibraryStore } from '../stores/library'

const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const router = useRouter()

const keyword = ref('')
const page = ref(1)
const pageSize = 24
const total = ref(0)
const loading = ref(false)
const items = ref([])
const errorMessage = ref('')
const detailOpen = ref(false)
const detailLoading = ref(false)
const detailAnime = ref(null)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const favoriteIds = computed(() => libraryStore.favoriteIds)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadAnimeList() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await fetchAnimeList({
      page: page.value,
      page_size: pageSize,
      keyword: keyword.value,
    })
    items.value = data.items
    total.value = data.total
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '动漫列表加载失败。'
  } finally {
    loading.value = false
  }
}

async function search() {
  page.value = 1
  await loadAnimeList()
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
  await libraryStore.createHistory(animeId)
}

async function toggleFavorite(animeId) {
  if (!isAuthenticated.value) {
    await router.push('/auth')
    return
  }
  if (favoriteIds.value.has(animeId)) {
    await libraryStore.deleteFavorite(animeId)
  } else {
    await libraryStore.createFavorite(animeId)
  }
}

watch(page, loadAnimeList)

onMounted(async () => {
  if (isAuthenticated.value) {
    await Promise.allSettled([libraryStore.loadFavorites(), libraryStore.loadHistory()])
  }
  await loadAnimeList()
})
</script>

<template>
  <section class="catalog-head">
    <div class="hero-panel">
      <p class="eyebrow">Catalog</p>
      <h2>全部动漫</h2>
      <p class="hero-copy">这里汇总了数据库里的全部动漫，可以按关键字搜索、查看详情、加入收藏和历史。</p>
    </div>
    <div class="control-panel">
      <label class="field">
        <span>搜索名称或题材</span>
        <input v-model.trim="keyword" type="text" placeholder="例如：Cowboy、Action、Drama" @keyup.enter="search" />
      </label>
      <button class="primary-button" type="button" @click="search">搜索</button>
      <p v-if="errorMessage" class="status status-error">{{ errorMessage }}</p>
    </div>
  </section>

  <section class="section-head">
    <div>
      <p class="eyebrow">Browse</p>
      <h3>动漫目录</h3>
    </div>
    <p>{{ loading ? '正在加载...' : `共 ${total} 部动漫，当前第 ${page} / ${totalPages} 页` }}</p>
  </section>

  <section class="card-grid">
    <AnimeCard
      v-for="item in items"
      :key="item.anime_id"
      :item="item"
      :favorite-ids="favoriteIds"
      @view-detail="openDetail"
      @add-history="markAsWatched"
      @toggle-favorite="toggleFavorite"
    />
  </section>

  <div class="pagination-bar">
    <button class="ghost-button" type="button" :disabled="page <= 1" @click="page -= 1">上一页</button>
    <span>第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
    <button class="ghost-button" type="button" :disabled="page >= totalPages" @click="page += 1">下一页</button>
  </div>

  <AnimeDetailDrawer
    :open="detailOpen"
    :anime="detailAnime"
    :loading="detailLoading"
    @close="detailOpen = false"
  />
</template>
