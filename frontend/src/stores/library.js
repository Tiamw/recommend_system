import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { addFavorite, addHistory, fetchFavorites, fetchHistory, removeFavorite } from '../api'

export const useLibraryStore = defineStore('library', () => {
  const history = ref([])
  const favorites = ref([])
  const historyLoading = ref(false)
  const favoritesLoading = ref(false)

  const historyIds = computed(() => history.value.map((item) => item.anime_id))
  const favoriteIds = computed(() => new Set(favorites.value.map((item) => item.anime_id)))
  const preferenceIds = computed(() => {
    // 这里把收藏和历史合并成统一偏好序列，供首页推荐流使用。
    const merged = [...favorites.value.map((item) => item.anime_id), ...history.value.map((item) => item.anime_id)]
    return [...new Set(merged)]
  })

  async function loadHistory() {
    historyLoading.value = true
    try {
      const { data } = await fetchHistory()
      history.value = data
    } finally {
      historyLoading.value = false
    }
  }

  async function createHistory(animeId) {
    const { data } = await addHistory({ anime_id: animeId })
    history.value.unshift(data)
    return data
  }

  async function loadFavorites() {
    favoritesLoading.value = true
    try {
      const { data } = await fetchFavorites()
      favorites.value = data
    } finally {
      favoritesLoading.value = false
    }
  }

  async function createFavorite(animeId) {
    const { data } = await addFavorite({ anime_id: animeId })
    favorites.value.unshift(data)
    return data
  }

  async function deleteFavorite(animeId) {
    await removeFavorite(animeId)
    favorites.value = favorites.value.filter((item) => item.anime_id !== animeId)
  }

  function reset() {
    history.value = []
    favorites.value = []
  }

  return {
    history,
    favorites,
    historyLoading,
    favoritesLoading,
    historyIds,
    favoriteIds,
    preferenceIds,
    loadHistory,
    createHistory,
    loadFavorites,
    createFavorite,
    deleteFavorite,
    reset,
  }
})
