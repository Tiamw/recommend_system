import { createRouter, createWebHistory } from 'vue-router'

import AllAnimePage from '../pages/AllAnimePage.vue'
import AuthPage from '../pages/AuthPage.vue'
import HomePage from '../pages/HomePage.vue'
import ProfilePage from '../pages/ProfilePage.vue'

const routes = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/anime', name: 'anime-list', component: AllAnimePage },
  { path: '/auth', name: 'auth', component: AuthPage },
  { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const token = localStorage.getItem('anime-rec-token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'auth', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
