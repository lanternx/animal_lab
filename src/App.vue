<template>
    <div class="app-container">
      <!-- 顶部导航栏 -->
      <header>
            <!-- 添加汉堡菜单按钮 移动端专用-->
          <button class="sidebar-toggle" @click="toggleSidebar">
            <i class="material-icons">{{ sidebarCollapsed ? 'menu' : 'close'  }}</i>
          </button>
          <div class="logo">
              <i class="material-icons logo-icon">pets</i>
              <span class="app-title">动物房管理系统</span>
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
        
        <div class="nav-section" v-if="experiments.length>0">
          <div class="nav-title" v-if="!sidebarCollapsed">实验记录</div>
          <div v-for="(expr, index) in experiments" :key="index">
            <router-link 
              :to="{ name: 'Experiments', params: { experimentId: expr.id } }" 
              custom v-slot="{ navigate, isActive }"
            >
              <div 
                class="nav-item" 
                :class="{ 'active': isActive }"
                @click="navigate"
              >
                <div class="number-badge">{{ index+1 }}</div>
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
        </div>
        
        <!-- 折叠按钮（在侧边栏底部） -->
        <div class="collapse-btn" @click="toggleSidebar">
          <i class="material-icons">
            {{ sidebarCollapsed ? 'chevron_right' : 'chevron_left' }}
          </i>
          <span v-if="!sidebarCollapsed">折叠侧边栏</span>
        </div>
      </div>
      <main>
        <router-view></router-view>
      </main>
  <!-- 页脚 -->
  <footer>
      <div class="status-indicators">
          <div class="status-item">
              <i class="material-icons status-icon online">cloud_done</i>
              <span>数据库已连接</span>
          </div>
          <div class="status-item">
              <i class="material-icons status-icon">save</i>
              <span>最后保存: 10:58:23</span>
          </div>
      </div>
      <div class="version-info">
          版本号: 3.1 | 2025-08-15
      </div>
  </footer>
      </div>


</template>

<script>
import axios from 'axios';

export default {
  name: 'AppLayout',
  data() {
    return {
      sidebarCollapsed: true,
      experiments:[]
    };
  },
  methods: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
      // 保存状态到localStorage
      localStorage.setItem('sidebarCollapsed', this.sidebarCollapsed);
    },
    setActiveView(view) {
      this.activeView = view;
    },
    // 实验类型相关方法
    fetchExperiments() {
        axios.get('/api/experiment-types')
        .then(response => {
            this.experiments = response.data;
        })
        .catch(error => {
            console.error('获取实验类型列表失败:', error);
            alert('获取实验类型列表失败');
        });
    }
  },
  mounted() {
    this.fetchExperiments();
    // 从localStorage加载侧边栏状态
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState !== null) {
      this.sidebarCollapsed = savedState === 'true';
    }
    
    // 初始设置活动视图
    this.setActiveView('cage');
    // 定期检查更新
    this.updateInterval = setInterval(() => {
      if (window.experimentTypesUpdated) {
        window.experimentTypesUpdated = false
        this.fetchExperiments()
      }
    }, 1000)
  }
};
</script>

<style>
@import '@material-design-icons/font/index.css';
@import url('./views/styles/main.css');

.material-icons {
  font-family: 'Material Icons';
}

/* 侧边栏可折叠样式 */
.sidebar {
  width: 240px;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

/* 导航项在折叠状态下的样式 */
.sidebar.collapsed .nav-title,
.sidebar.collapsed .nav-item span,
.sidebar.collapsed .collapse-btn span {
  display: none;
}
/* 折叠按钮样式 */

.collapse-btn {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  width: auto;
  max-width: 90%;
  border: 1px solid #e0e0e0;
}
.collapse-btn:hover {
  background-color: #f1f8e9;
  color: #43a047;
}

.collapse-btn i {
  margin-right: 16px;
}

/* 响应式设计 */
@media (max-width: 992px) {
  /* 在平板设备上默认折叠侧边栏 */
  .sidebar {
    width: 60px;
  }
  
  .sidebar:not(.collapsed) {
    width: 240px;
    z-index: 1000;
    box-shadow: 5px 0 15px rgba(0,0,0,0.1);
  }
  
  .main-content {
    margin-left: 60px;
  }
  
  .sidebar:not(.collapsed) + .main-content {
    margin-left: 240px;
  }
  
  .sidebar-toggle {
    display: block;
  }
}

@media (max-width: 768px) {
  /* 在手机上完全隐藏侧边栏 */
  .sidebar.collapsed {
    transform: translateX(-100%);
    width: 240px;
  }
  
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
  
  .main-content {
    margin-left: 0 !important;
  }
  
  .sidebar-toggle {
    display: block;
  }
}

/* 主内容区扩展样式 */
.main-content.expanded {
  margin-left: 60px; /* 与折叠后的侧边栏宽度一致 */
}

/* 导航项工具提示 */
.nav-item {
  position: relative;
}

.tooltip {
  position: absolute;
  left: 60px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  white-space: nowrap;
  z-index: 100;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s;
}

.nav-item:hover .tooltip {
  opacity: 1;
}

/* 汉堡菜单按钮 */
.sidebar-toggle {
  display: none; /* 默认在桌面端隐藏 */
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  margin-right: 15px;
}

/* 添加全局双击提示 */
[data-dblclick-hint] {
  position: relative;
}

[data-dblclick-hint]:after {
  content: "双击查看详情";
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  background: #4285f4;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  opacity: 0;
  transition: opacity 0.3s;
  white-space: nowrap;
}

[data-dblclick-hint]:hover:after {
  opacity: 1;
}

.number-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2c6fbb, #3a8ee0);
  color: white;
  font-weight: 600;
  margin-right: 12px;
  box-shadow: 0 4px 6px rgba(44, 111, 187, 0.2);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.nav-item:hover .number-badge {
  transform: scale(1.1);
  box-shadow: 0 6px 10px rgba(44, 111, 187, 0.3);
}

.sidebar.collapsed .number-badge {
  margin-right: 0;
  margin-left: auto;
  margin-right: auto;
}
</style>
