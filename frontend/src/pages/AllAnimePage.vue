<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AnimeCard from '../components/AnimeCard.vue'
import AnimeDetailDrawer from '../components/AnimeDetailDrawer.vue'
import { fetchAnimeDetail, fetchAnimeGenres, fetchAnimeList } from '../api'
import { useAuthStore } from '../stores/auth'
import { useLibraryStore } from '../stores/library'

const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const router = useRouter()

const keyword = ref('')
const selectedGenre = ref('')
const genreOptions = ref([])
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

async function loadGenreOptions() {
  try {
    const { data } = await fetchAnimeGenres({ limit: 20 })
    genreOptions.value = data.items
  } catch {
    genreOptions.value = []
  }
}

async function loadAnimeList() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await fetchAnimeList({
      page: page.value,
      page_size: pageSize,
      keyword: keyword.value,
      genre: selectedGenre.value,
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

async function selectGenre(genreName) {
  selectedGenre.value = selectedGenre.value === genreName ? '' : genreName
  page.value = 1
  await loadAnimeList()
}

async function resetFilters() {
  keyword.value = ''
  selectedGenre.value = ''
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
  await Promise.all([loadGenreOptions(), loadAnimeList()])
})
</script>

<template>
  <section class="catalog-head">
    <div class="hero-panel">
      <p class="eyebrow">Catalog</p>
      <h2>全部动漫</h2>
      <p class="hero-copy">这里汇总了数据库里的全部动漫。你可以输入名称搜索，也可以直接点下面的题材标签筛选。</p>
    </div>
    <div class="control-panel">
      <label class="field">
        <span>搜索名称</span>
        <input v-model.trim="keyword" type="text" placeholder="例如：Cowboy、Naruto、Gundam" @keyup.enter="search" />
      </label>
      <div class="action-row action-row--tight">
        <button class="primary-button" type="button" @click="search">搜索</button>
        <button class="ghost-button" type="button" @click="resetFilters">重置筛选</button>
      </div>
      <p v-if="errorMessage" class="status status-error">{{ errorMessage }}</p>
    </div>
  </section>

  <section class="genre-panel">
    <div class="section-head section-head--compact">
      <div>
        <p class="eyebrow">Genres</p>
        <h3>题材筛选</h3>
      </div>
      <p>{{ selectedGenre ? `当前题材：${selectedGenre}` : '点击题材标签即可快速筛选' }}</p>
    </div>
    <div class="genre-chip-list">
      <button
        type="button"
        class="genre-chip"
        :class="{ 'genre-chip--active': !selectedGenre }"
        @click="selectGenre('')"
      >
        全部
      </button>
      <button
        v-for="genre in genreOptions"
        :key="genre.name"
        type="button"
        class="genre-chip"
        :class="{ 'genre-chip--active': selectedGenre === genre.name }"
        @click="selectGenre(genre.name)"
      >
        {{ genre.name }}
        <span>{{ genre.count }}</span>
      </button>
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
