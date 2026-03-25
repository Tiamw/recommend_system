<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  open: Boolean,
  anime: {
    type: Object,
    default: null,
  },
  loading: Boolean,
})

const emit = defineEmits(['close'])

const title = computed(() => props.anime?.name || '动漫详情')

watch(
  () => props.open,
  (value) => {
    document.body.style.overflow = value ? 'hidden' : ''
  },
)
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="detail-overlay" @click.self="emit('close')">
      <aside class="detail-drawer">
        <button class="detail-close" type="button" @click="emit('close')">关闭</button>
        <div v-if="loading" class="detail-state">正在加载详情...</div>
        <div v-else-if="anime" class="detail-body">
          <p class="detail-kicker">Anime Detail</p>
          <h2>{{ title }}</h2>
          <dl class="detail-grid">
            <div>
              <dt>ID</dt>
              <dd>{{ anime.anime_id }}</dd>
            </div>
            <div>
              <dt>类型</dt>
              <dd>{{ anime.type || '未知' }}</dd>
            </div>
            <div>
              <dt>评分</dt>
              <dd>{{ anime.rating ?? '暂无' }}</dd>
            </div>
            <div>
              <dt>集数</dt>
              <dd>{{ anime.episodes ?? '未知' }}</dd>
            </div>
            <div>
              <dt>热度</dt>
              <dd>{{ anime.members ?? '暂无' }}</dd>
            </div>
          </dl>
          <section>
            <h3>题材</h3>
            <p>{{ anime.genre || '暂无题材说明' }}</p>
          </section>
        </div>
        <div v-else class="detail-state">请选择一部动漫查看详情。</div>
      </aside>
    </div>
  </teleport>
</template>
