<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  favoriteIds: {
    type: Object,
    default: () => new Set(),
  },
})

const emit = defineEmits(['view-detail', 'add-history', 'toggle-favorite'])

const isFavorite = computed(() => props.favoriteIds.has?.(props.item.anime_id))
</script>

<template>
  <article class="anime-card">
    <div class="anime-card__meta">
      <span class="pill">#{{ item.anime_id }}</span>
      <span class="pill pill-accent">{{ item.type || '未知类型' }}</span>
    </div>
    <h3>{{ item.name }}</h3>
    <p class="anime-card__genre">{{ item.genre || '题材信息缺失' }}</p>
    <div class="anime-card__footer">
      <strong>评分 {{ item.rating ?? '暂无' }}</strong>
      <div class="anime-card__actions">
        <button class="ghost-button" type="button" @click="$emit('view-detail', item.anime_id)">详情</button>
        <button class="ghost-button" type="button" @click="$emit('add-history', item.anime_id)">记为已看</button>
        <button class="primary-button compact" type="button" @click="$emit('toggle-favorite', item.anime_id)">
          {{ isFavorite ? '取消收藏' : '加入收藏' }}
        </button>
      </div>
    </div>
  </article>
</template>
