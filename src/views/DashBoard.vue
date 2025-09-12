<template>
  <div class="main-content">
    <div class="content-header" id="contentHeader">
      <h1 class="page-title">笼位视图</h1>
      <div class="action-buttons">
        <button class="btn btn-outline">
          <i class="material-icons btn-icon">filter_list</i>
          筛选
        </button>
        <button class="btn btn-primary" @click="addCageDialog">
          <i class="material-icons btn-icon">add</i>
          添加笼位
        </button>
      </div>
    </div>
    
    <!-- Section标签页导航 -->
    <div class="section-tabs">
      <div 
        v-for="section in availableSections" 
        :key="section" 
        class="tab-item"
        :class="{ active: activeSection === section }"
        @click="activeSection = section"
      >
        {{ section }}
      </div>
    </div>
    
    <div class="cage-view-container">
      <!-- 笼位网格区域 -->
      <div class="cage-grid" id="cageGrid">
        <div 
          v-for="cage in filteredCages" 
          :key="cage.id" 
          class="cage-card" 
          :class="{'breeding': cage.cage_type === 'breeding'}"
          @dragover.prevent
          @drop="handleDrop($event, cage.id)"
          @contextmenu.prevent="openCageContextMenu($event, cage)"
        >
          <div class="cage-id">{{ cage.cage_id }}</div>
          <div class="cage-location">{{ cage.location }}</div>
          <div class="cage-mice-container">
            <template v-if="cage.mice && cage.mice.length > 0">
              <div 
                v-for="mouse in cage.mice" 
                :key="mouse.tid" 
                class="cage-mouse" 
                draggable="true"
                @dragstart="handleDragStart($event, mouse.tid, cage.id)"
                @dblclick="openMouseDetail(mouse.tid)"
              >
                <div class="mouse-sex" :class="mouse.sex === 'F' ? 'sex-female' : 'sex-male'">
                  {{ mouse.sex === 'F' ? '♀' : '♂' }}
                </div>
                <div class="mouse-info">
                  <div class="mouse-id">{{ mouse.id }}</div>
                  <div class="mouse-genotype">{{ mouse.genotype }}</div>
                </div>
              </div>
            </template>
            <div v-else class="empty-cage">空笼位</div>
        </div>
        </div>
      </div>
      
      <!-- 临时存放区（右侧） -->
      <div class="temporary-area">
        <div class="temporary-header">
          <h2 class="temporary-title">临时区</h2>
          <span class="counter">{{ temporaryMice.length }}只</span>
        </div>
        
        <div 
          class="mouse-list"
          @dragover.prevent
          @drop="handleDrop($event, '-1')"
        >
          <div 
            v-for="mouse in temporaryMice" 
            :key="mouse.id" 
            class="mouse-card"
            draggable="true"
            @dragstart="handleDragStart($event, mouse.tid, '-1')"
            @dblclick="openMouseDetail(mouse.tid)"
          >
            <div class="mouse-sex" :class="mouse.sex === 'F' ? 'sex-female' : 'sex-male'">
              {{ mouse.sex === 'F' ? '♀' : '♂' }}
            </div>
            <div class="mouse-info">
              <div class="mouse-id">{{ mouse.id }}</div>
              <div class="mouse-genotype">{{ mouse.genotype }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加笼位对话框 -->
    <div v-if="addCageDialogVisible" class="dialog-overlay">
      <div class="dialog-container">
        <h2>添加新笼位</h2>
        <div class="form-group">
          <label>笼位ID</label>
          <input type="text" v-model="newCage.cage_id" placeholder="输入笼位ID">
        </div>
        <div class="form-group">
          <label>位置</label>
          <input type="text" v-model="newCage.location" placeholder="输入位置">
        </div>
        <div class="form-group">
          <label>区域</label>
          <select v-model="newCage.section">
            <option v-for="section in availableSections" :key="section" :value="section">
              {{ section }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>笼位类型</label>
          <select v-model="newCage.cage_type">
            <option value="normal">普通笼</option>
            <option value="breeding">繁殖笼</option>
          </select>
        </div>
        <div class="dialog-buttons">
          <button class="btn btn-outline" @click="addCageDialogVisible = false">取消</button>
          <button class="btn btn-primary" @click="addNewCage">确定</button>
        </div>
      </div>
    </div>
    
    <!-- 小鼠详细视图 -->
    <MouseDetailModal 
      v-if="showMouseDetail" 
      :mouse-id="selectedMouseId" 
      @close="showMouseDetail = false" 
    />
  </div>

    <!-- 笼位右键菜单 -->
  <div v-if="cageContextMenu.visible" 
      class="context-menu"
      :style="{ top: cageContextMenu.y + 'px', left: cageContextMenu.x + 'px' }">
    <div class="menu-item" @click="openEditCageDialog(cageContextMenu.cage)">修改笼位</div>
    <div class="menu-item" @click="deleteCage(cageContextMenu.cage)">删除笼位</div>
  </div>

  <!-- 编辑笼位对话框 -->
  <div v-if="editCageDialogVisible" class="dialog-overlay">
    <div class="dialog-container">
      <h2>修改笼位信息</h2>
      <div class="form-group">
        <label>ID</label>
        <input type="text" v-model="editingCage.cage_id" placeholder="输入笼位ID">
      </div>
      <div class="form-group">
        <label>位置</label>
        <input type="text" v-model="editingCage.location" placeholder="输入位置">
      </div>
      <div class="form-group">
        <label>区域 (Section)</label>
        <select v-model="editingCage.section">
          <option v-for="section in availableSections" :key="section" :value="section">
            {{ section }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label>笼位类型</label>
        <select v-model="editingCage.cage_type">
          <option value="normal">普通笼</option>
          <option value="breeding">繁殖笼</option>
        </select>
      </div>
      <div class="dialog-buttons">
        <button class="btn btn-outline" @click="editCageDialogVisible = false">取消</button>
        <button class="btn btn-primary" @click="updateCage">确定</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import MouseDetailModal from './MouseDetailView.vue';

export default {
  name: 'AnimalLabDashboard',
  components: {
    MouseDetailModal
  },
  data() {
    return {
      cages: [],
      temporaryMice: [],
      dragData: null,
      showMouseDetail: false,
      selectedMouseId: null,
      addCageDialogVisible: false,
      newCage: {
        id: '',
        cage_id: '',
        location: '',
        section: '',
        cage_type: 'normal'
      },
      cageContextMenu: {
        visible: false,
        x: 0,
        y: 0,
        cage: null
      },
      editCageDialogVisible: false,
      editingCage: {
        id: '',
        cage_id: '',
        location: '',
        section: '',
        cage_type: 'normal'
      },
      activeSection: '', // 当前选中的section
      availableSections: [], // 所有可用的section
      section_key: false
    };
  },
  computed: {
    // 根据当前选中的section过滤笼位
    filteredCages() {
      if (!this.activeSection) return this.cages;
      return this.cages.filter(cage => cage.section === this.activeSection);
    }
  },
  mounted() {
    this.section_key = true;
    this.fetchCages();
    this.fetchTemporaryMice();
  },
  methods: {
    // 获取所有笼位数据
    async fetchCages() {
      try {
        const lresponse = await axios.get('/api/locations');
        this.availableSections = lresponse.data.map(location => location.identifier);
        const response = await axios.get('/api/cages');
        this.cages = response.data;
        
        // 设置默认选中的section为第一个
        if (this.availableSections.length > 0 && this.section_key) {
          this.activeSection = this.availableSections[0];
          this.newCage.section = this.availableSections[0];
          this.section_key = false
        }
      } catch (error) {
        console.error('获取笼位信息失败:', error);
        alert('无法获取笼位信息，请检查网络连接');
      }
    },
    
    // 获取临时区小鼠数据
    async fetchTemporaryMice() {
      try {
        const response = await axios.get('/api/cages/-1');
        this.temporaryMice = response.data.map(mouse => ({
          ...mouse
        }));
      } catch (error) {
        console.error('获取临时区小鼠信息失败:', error);
      }
    },
    
    // 拖动功能实现
    handleDragStart(event, mouseId, sourceCageId) {
      this.dragData = {
        mouseId,
        sourceCageId
      };
      event.dataTransfer.setData('text/plain', mouseId);
    },
    
    async handleDrop(event, targetCageId) {
      event.preventDefault();
      if (this.dragData) {
        const { mouseId, sourceCageId } = this.dragData;
        
        try {
          // 更新数据库
          await axios.put(`/api/cage/${targetCageId || '-1'}`, {
            mouse_id: mouseId
          });
          // 更新本地数据
          const mouse = this.removeMouseFromSource(mouseId, sourceCageId);
          this.addMouseToTarget(mouse, targetCageId);
        } catch (error) {
          console.error('移动小鼠失败:', error);
          alert('移动小鼠失败，请重试');
        }
        
        this.dragData = null;
      }
    },
    
    // 更新本地数据：从源位置移除小鼠
    removeMouseFromSource(mouseId, sourceCageId) {
      // 从临时区移除
      if (sourceCageId === '-1') {
        const mouse = this.temporaryMice.find(mouse => mouse.tid === mouseId);
        this.temporaryMice = this.temporaryMice.filter(mouse => mouse.tid !== mouseId);
        return mouse;
      }
      // 从笼位中移除
      const cageIndex = this.cages.findIndex(cage => cage.id === sourceCageId);
      if (cageIndex !== -1) {
        const mouse = this.cages[cageIndex].mice.find(mouse => mouse.tid === mouseId);
        this.cages[cageIndex].mice = this.cages[cageIndex].mice.filter(mouse => mouse.tid !== mouseId);
        return mouse
      }
    },
    
    // 更新本地数据：添加到目标位置
    async addMouseToTarget(mouse, targetCageId) {
      try {
        if (targetCageId === '-1') {
          // 添加到临时区
          if (!this.temporaryMice) this.temporaryMice = [];
          this.temporaryMice.push({...mouse});
        } else {
          // 添加到笼位
          const cage = this.cages.find(cage => cage.id === targetCageId);
          if (cage) {
            if (!cage.mice) cage.mice = [];
            cage.mice.push({...mouse});
          }
        }
      } catch (error) {
        console.error('获取小鼠详情失败:', error);
      }
    },
    
    openMouseDetail(mouseId) {
      this.selectedMouseId = mouseId;
      this.showMouseDetail = true;
    },
    
    async addCageDialog() {
      this.addNewCage.section = this.activeSection;
      this.addCageDialogVisible = true;
    },

    // 添加新笼位
    async addNewCage() {
      if (!this.newCage.cage_id || !this.newCage.section) {
        alert('请填写笼位ID和区域');
        return;
      }
      
      try {
        await axios.post('/api/cages', this.newCage);
        this.fetchCages(); // 刷新笼位列表
        this.addCageDialogVisible = false;
        this.newCage = { id: '', cage_id: '', location: '', section: '', cage_type: 'normal' };
      } catch (error) {
        console.error('添加笼位失败:', error);
        alert('添加笼位失败，请重试');
      }
    },

    openCageContextMenu(event, cage) {
      this.cageContextMenu = {
        visible: true,
        x: event.clientX,
        y: event.clientY,
        cage: cage
      };
      // 点击其他地方关闭菜单
      document.addEventListener('click', this.closeContextMenu);
    },
    
    closeContextMenu() {
      this.cageContextMenu.visible = false;
      document.removeEventListener('click', this.closeContextMenu);
    },
    
    openEditCageDialog(cage) {
      this.editingCage = { ...cage };
      this.editCageDialogVisible = true;
      this.closeContextMenu();
    },
    
    async updateCage() {
      try {
        await axios.put(`/api/cages/${this.editingCage.id}`, {
          cage_id: this.editingCage.cage_id,
          location: this.editingCage.location,
          section: this.editingCage.section,
          cage_type: this.editingCage.cage_type
        });
        // 更新本地数据
        const index = this.cages.findIndex(c => c.id === this.editingCage.id);
        if (index !== -1) {
          this.cages[index].cage_id = this.editingCage.cage_id;
          this.cages[index].location = this.editingCage.location;
          this.cages[index].section = this.editingCage.section;
          this.cages[index].cage_type = this.editingCage.cage_type;
        }
        this.editCageDialogVisible = false;
      } catch (error) {
        console.error('修改笼位失败:', error);
        alert('修改笼位失败，请重试');
      }
    },
    
    async deleteCage(cage) {
      if (!confirm(`确定要删除笼位 ${cage.cage_id} 吗？`)) return;
      
      try {
        await axios.delete(`/api/cages/${cage.id}`);
        // 更新本地数据
        this.cages = this.cages.filter(c => c.id !== cage.id);
        this.closeContextMenu();
      } catch (error) {
        console.error('删除笼位失败:', error);
        alert('删除笼位失败，请重试');
      }
    },
  }
};
</script>

<style scoped>
@import '@material-design-icons/font/index.css';
@import url('./styles/main.css');

/* 主容器布局 */
.cage-view-container {
  display: flex;
  gap: 15px;
  height: calc(100vh - var(--header-height) - var(--footer-height) - 100px);
  overflow: hidden;
}

/* 笼位网格容器 */
.cage-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  grid-auto-rows: minmax(150px, 250px);
  gap: 15px;
  padding: 10px;
  overflow-y: auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

/* 临时存放区容器 */
.temporary-area {
  width: 220px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  padding: 15px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Section标签页样式 */
.section-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 15px;
  padding: 0 10px;
}

.tab-item {
  padding: 8px 16px;
  cursor: pointer;
  margin-right: 5px;
  border-radius: 5px 5px 0 0;
  font-weight: 500;
  color: #666;
  transition: all 0.2s ease;
}

.tab-item:hover {
  background-color: #f5f5f5;
}

.tab-item.active {
  color: var(--primary);
  background-color: rgba(25, 118, 210, 0.08);
  border-bottom: 2px solid var(--primary);
}

/* 调整临时区标题布局 */
.temporary-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 10px;
}

.temporary-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 5px;
}

.counter {
  background-color: var(--warning);
  color: white;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 0.85rem;
}

/* 调整临时区鼠标卡片布局 */
.mouse-list {
  flex-grow: 1;
  overflow-y: auto;
  min-height: 100px;
  padding: 5px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px dashed #ccc;
}

.mouse-card {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 6px;
  background-color: #fff8e1;
  margin-bottom: 8px;
  border: 1px solid #ffe082;
  transition: all 0.3s;
  cursor: pointer;
}

@keyframes pulse-alert {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}


/* 保持其他样式不变 */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-outline {
  background-color: transparent;
  border: 1px solid var(--primary);
  color: var(--primary);
}

.btn-icon {
  margin-right: 5px;
}

/* 笼位卡片样式 */
.cage-card {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 15px;
  background-color: white;
  transition: all 0.2s;
  cursor: pointer;
  min-height: 250px;
  max-height: 250px;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.cage-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.cage-card.breeding {
  background-color: rgba(255, 182, 193, 0.2);
  border-left: 4px solid pink;
}

.cage-card.temporary {
  background-color: rgba(255, 255, 0, 0.1);
  border-left: 4px solid var(--warning);
}

.cage-id {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 5px;
}

.cage-location {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 10px;
}

.cage-mouse {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding: 5px;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.mouse-sex {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  font-size: 12px;
  color: white;
  font-weight: bold;
}

.sex-female {
  background-color: #ff4081;
}

.sex-male {
  background-color: #2196f3;
}

.mouse-info {
  flex-grow: 1;
}

.mouse-id {
  font-weight: 600;
  font-size: 0.9rem;
}

.mouse-genotype {
  font-size: 0.8rem;
  color: #666;
}

/* 添加悬停效果 */
.cage-mouse {
  cursor: pointer;
  transition: transform 0.2s;
}

.cage-mouse:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-container {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.dialog-container h2 {
  margin-top: 0;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input, .form-group select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.empty-cage {
  color: #999;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
}

.cage-mice-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 5px;
  max-height: calc(250px - 60px);
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  z-index: 1000;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
}

.menu-item:hover {
  background-color: #f5f5f5;
}
</style>