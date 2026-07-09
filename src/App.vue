<template>
    <div class="app-container">
      <!-- 顶部导航栏 -->
      <header>
            <!-- 添加汉堡菜单按钮 移动端专用-->
          <button class="sidebar-toggle" @click="toggleSidebar">
            <i class="material-icons">{{ sidebarCollapsed ? 'menu' : 'close'  }}</i>
          </button>
          <div class="logo">
              <img src="@/assets/logo.png" alt="鼠管家Logo" class="logo-icon">
              <span class="app-title">MurisPro - 鼠管家</span>
          </div>

      </header>
  
      <!-- 侧边导航栏 -->
      <div class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
        <div class="nav-section">
          <div class="nav-title" v-if="!sidebarCollapsed">核心功能</div>
        <router-link 
          :to="{ name: 'home' }" 
          custom v-slot="{ navigate, isActive }"
        >
          <div 
            class="nav-item" 
            :class="{ 'active': isActive }"
            @click="navigate"
          >
            <i class="material-icons">grid_view</i>
            <span v-if="!sidebarCollapsed">笼位视图</span>
            <div class="tooltip" v-if="sidebarCollapsed">笼位视图</div>
          </div>
        </router-link>
      <router-link 
        :to="{ name: 'mice' }" 
        custom
        v-slot="{ navigate, isActive }"
      >
        <div 
          class="nav-item" 
          :class="{ 'active': isActive }"
          @click="navigate"
        >
          <i class="material-icons">format_list_bulleted</i>
          <span v-if="!sidebarCollapsed">小鼠列表</span>
          <div class="tooltip" v-if="sidebarCollapsed">小鼠列表</div>
        </div>
      </router-link>
      <router-link 
        :to="{ name: 'WeightList' }" 
        custom
        v-slot="{ navigate, isActive }"
      >
        <div 
          class="nav-item" 
          :class="{ 'active': isActive }"
          @click="navigate"
        >
          <i class="material-icons">scale</i>
          <span v-if="!sidebarCollapsed">体重列表</span>
          <div class="tooltip" v-if="sidebarCollapsed">体重列表</div>
        </div>
      </router-link>
        </div>
        
        <div class="nav-section" v-if="experimentStore.showedExperiments.length>0">
          <div class="nav-title" v-if="!sidebarCollapsed">实验记录</div>
          <div v-for="(expr, index) in experimentStore.showedExperiments" :key="index">
            <router-link 
              :to="{ name: 'Experiments', params: { experimentId: expr.id } }" 
              custom v-slot="{ navigate, isActive }"
            >
              <div 
                class="nav-item" 
                :class="{ 'active': isActive }"
                @click="navigate"
              >
                <div class="number-badge">{{ expr.id }}</div>
                <span v-if="!sidebarCollapsed">{{ expr.name }}</span>
                <div class="tooltip" v-if="sidebarCollapsed">{{ expr.name }}</div>
              </div>
            </router-link>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-title" v-if="!sidebarCollapsed">数据分析</div>
          <router-link 
            :to="{ name: 'BodyWeight' }" 
            custom v-slot="{ navigate, isActive }"
          >
            <div 
              class="nav-item" 
              :class="{ 'active': isActive }"
              @click="navigate"
            >
              <i class="material-icons">insights</i>
              <span v-if="!sidebarCollapsed">体重曲线</span>
              <div class="tooltip" v-if="sidebarCollapsed">体重曲线</div>
            </div>
          </router-link>
          <router-link 
            :to="{ name: 'Survivalplot' }" 
            custom
            v-slot="{ navigate, isActive }"
          >
            <div 
              class="nav-item" 
              :class="{ 'active': isActive }"
              @click="navigate"
            >
              <i class="material-icons">trending_down</i>
              <span v-if="!sidebarCollapsed">生存曲线</span>
              <div class="tooltip" v-if="sidebarCollapsed">生存曲线</div>
            </div>
          </router-link>
        </div>
        <div class="nav-section">
          <div class="nav-title" v-if="!sidebarCollapsed">系统设置</div>
          <router-link 
            :to="{ name: 'SystemSettings' }" 
            custom
            v-slot="{ navigate, isActive }"
          >
            <div 
              class="nav-item" 
              :class="{ 'active': isActive }"
              @click="navigate"
            >
              <i class="material-icons">settings</i>
              <span v-if="!sidebarCollapsed">设置</span>
              <div class="tooltip" v-if="sidebarCollapsed">设置</div>
            </div>
          </router-link>
          <router-link 
            :to="{ name: 'InfoPage' }" 
            custom
            v-slot="{ navigate, isActive }"
          >
            <div 
              class="nav-item" 
              :class="{ 'active': isActive }"
              @click="navigate"
            >
              <i class="material-icons">info</i>
              <span v-if="!sidebarCollapsed">宣传页</span>
              <div class="tooltip" v-if="sidebarCollapsed">宣传页</div>
            </div>
          </router-link>
        </div>
        
        <!-- 折叠按钮（在侧边栏底部） -->
        <div class="collapse-btn" @click="toggleSidebar">
          <i class="material-icons">
            {{ sidebarCollapsed ? 'chevron_right' : 'chevron_left' }}
          </i>
          <span v-if="!sidebarCollapsed">折叠侧边栏</span>
        </div>
      </div>
      <main @click="sidebarCollapsed=true">
        <router-view></router-view>
      </main>
  <!-- 页脚 -->
  <footer>
      <div class="status-indicators">
          <div class="status-item">
              <i class="material-icons status-icon online">cloud_done</i>
              <span>当前数据库正常</span>
          </div>
          <div class="status-item">
              <i class="material-icons status-icon">save</i>
              <span>自动保存</span>
          </div>
      </div>
      <div class="version-info">
          版本号: 3.2.1 | 2026-7-9
      </div>
  </footer>
      </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useExperimentStore } from '@/stores'

const experimentStore = useExperimentStore()

// 响应式数据
const sidebarCollapsed = ref(true)

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  // 保存状态到localStorage
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value)
}

// 生命周期
onMounted(() => {
  // 从localStorage加载侧边栏状态
  const savedState = localStorage.getItem('sidebarCollapsed')
  if (savedState !== null) {
    sidebarCollapsed.value = savedState === 'true'
  }
  if (!window.pywebview || !window.pywebview.api) {
    // 定期心跳
    const heartbeatInterval = setInterval(() => {
        fetch('/heartbeat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // 低优先级，不阻塞用户交互
            priority: 'low',
            // 允许在页面卸载时发送
            keepalive: true
        }).catch(() => {});  // 静默失败
    }, 10000);
  }
})

import { useRoute } from 'vue-router'
const route = useRoute()

watch(() => route.path, () => {
  sidebarCollapsed.value = true
})
</script>

<style>
@import '@material-design-icons/font/index.css';
@import url('./views/styles/main.css');
</style>
