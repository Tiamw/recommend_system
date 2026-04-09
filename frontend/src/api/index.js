import api from './client'

export function login(payload) {
  return api.post('/auth/login', payload)
}

export function register(payload) {
  return api.post('/auth/register', payload)
}

export function fetchRecommendations(payload) {
  return api.post('/recommend', payload)
}

export function fetchAnimeGenres(params) {
  return api.get('/anime/genres', { params })
}

export function fetchAnimeList(params) {
  return api.get('/anime', { params })
}

export function fetchAnimeDetail(animeId) {
  return api.get(`/anime/${animeId}`)
}

export function fetchHistory() {
  return api.get('/me/history')
}

export function addHistory(payload) {
  return api.post('/me/history', payload)
}

export function fetchFavorites() {
  return api.get('/me/favorites')
}

export function addFavorite(payload) {
  return api.post('/me/favorites', payload)
}

export function removeFavorite(animeId) {
  return api.delete(`/me/favorites/${animeId}`)
}

export function fetchHealth() {
  return api.get('/health')
}
