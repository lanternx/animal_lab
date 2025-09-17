<template>
  <div class="main-content">
    <div class="content-header" id="contentHeader">
      <h1 class="page-title">笼位视图</h1>
      <div class="action-buttons">
        <button class="btn btn-outline" @click="fetchCages">
          <i class="material-icons btn-icon">refresh</i>
          刷新数据
        </button>
        <button class="btn btn-outline" v-if="!showTemporaryArea && temporaryMice.length === 0" @click="showTemporaryArea=true">
          <i class="material-icons btn-icon">view_sidebar</i>
          打开临时区
        </button>
        <button class="btn btn-outline" @click="exportToPDF">
          <i class="material-icons btn-icon">picture_as_pdf</i>
          当前位置导出pdf
        </button>
        <button class="btn btn-primary" @click="addCageDialog">
          <i class="material-icons btn-icon">add</i>
          添加笼位
        </button>
      </div>
    </div>
    
    <!-- Section标签页导航 -->
  <draggable 
    v-model="sortedSections" 
    item-key="id"
    handle=".drag-handle"
    @end="onDragEnd"
    class="section-tabs"
  >
    <template #item="{element}">
      <div 
        class="tab-item"
        :class="{ active: activeSection === element.identifier }"
        @click="activeSection = element.identifier"
      >
        <span class="drag-handle">
          <i class="material-icons">drag_handle</i>
        </span>
        {{ element.identifier }}
      </div>
    </template>
  </draggable>
    
    <div class="cage-view-container">
      <!-- 笼位网格区域 -->
      <div class="cage-grid" id="cageGrid">
        <div 
          v-for="cage in filteredCages" 
          :key="cage.id" 
          class="cage-card" 
          :class="{
            'breeding': cage.cage_type === 'breeding',
            'swap-source': cage.id === sourceCage?.id,
            'swap-target': cage.id === targetCage?.id
            }"
          @dragover.prevent
          @drop="handleDrop($event, cage.id)"
          @contextmenu.prevent="openCageContextMenu($event, cage)"
          @click="handleCageClick(cage)"
        >
          <div class="cage-id">{{ cage.cage_id }}</div>
          <div class="cage-location">{{ cage.location }}</div>
          <div class="cage-meta">
            <div class="cage-meta-row" v-if="cage.cage_card_number">
              <span class="meta-label">笼卡:</span>
              <span class="meta-value">{{ cage.cage_card_number }}</span>
            </div>
            <div class="cage-meta-row" v-if="cage.mice_birth_date">
              <span class="meta-label">DOB:</span>
              <span class="meta-value">{{ cage.mice_birth_date }}</span>
            </div>
            <div class="cage-meta-row" v-if="cage.mice_count || cage.mice_sex">
              <span class="meta-label">数量/性别:</span>
              <span class="meta-value">{{ cage.mice_count || 'NA' }} / {{ cage.mice_sex || 'NA' }}</span>
            </div>
            <div class="cage-meta-row" v-if="cage.mice_genotype">
              <span class="meta-label">基因型:</span>
              <span class="meta-value">{{ cage.mice_genotype }}</span>
            </div>
          </div>
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
                <div class="mouse-info">
                  <div class="mouse-days">{{ !mouse.days || mouse.days === 'none' ? 'NA天数' : `当前${mouse.days}天` }}</div>
                </div>
              </div>
            </template>
            <div v-else class="empty-cage">空笼位</div>
        </div>
        </div>
      </div>
      
      <!-- 临时存放区（右侧） -->
      <div class="temporary-area" v-if="temporaryMice.length !== 0 || showTemporaryArea">
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
            <div class="mouse-info">
              <div class="mouse-days">{{ !mouse.days || mouse.days === 'none' ? 'NA天数' : `当前${mouse.days}天` }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加笼位对话框 -->
    <div v-if="addCageDialogVisible" class="dialog-overlay">
      <div class="modal-backdrop" @click="addCageDialogVisible = false"></div>
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
            <option v-for="section in availableSections" :key="section" :value="section.identifier">
              {{ section.identifier }}
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
        <div class="form-group">
          <label>笼卡号</label>
          <input type="text" v-model="newCage.cage_card_number" placeholder="输入笼卡号">
        </div>
        <div class="form-group">
          <label>笼内小鼠出生日期</label>
          <input type="date" v-model="newCage.mice_birth_date">
        </div>
        <div class="form-group">
          <label>笼内小鼠数量</label>
          <input type="number" v-model.number="newCage.mice_count" min="0">
        </div>
        <div class="form-group">
          <label>笼内小鼠性别</label>
          <select v-model="newCage.mice_sex">
            <option value="M">雄性</option>
            <option value="F">雌性</option>
            <option value="Mixed">混合</option>
          </select>
        </div>
        <div class="form-group">
          <label>笼内小鼠基因型</label>
          <input type="text" v-model="newCage.mice_genotype" placeholder="如: WT/KO/其他">
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
      <ul>
          <li @click="openEditCageDialog(cageContextMenu.cage)">
              <i class="material-icons">edit</i> 编辑笼位信息
          </li>
          <li @click="exchangeCage(cageContextMenu.cage)">
              <i class="material-icons">swap_horiz</i> 笼位排序互换
          </li>
          <li @click="deleteCage(cageContextMenu.cage)">
              <i class="material-icons">delete</i> 删除笼位
          </li>
      </ul>
  </div>

  <!-- 编辑笼位对话框 -->
  <div v-if="editCageDialogVisible" class="dialog-overlay">
  <div class="modal-backdrop" @click="editCageDialogVisible = false"></div>
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
        <label>区域</label>
        <select v-model="editingCage.section">
          <option v-for="section in availableSections" :key="section" :value="section.identifier">
            {{ section.identifier }}
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
      <div class="form-group">
        <label>笼卡号</label>
        <input type="text" v-model="editingCage.cage_card_number" placeholder="输入笼卡号">
      </div>
      <div class="form-group">
        <label>笼内小鼠出生日期</label>
        <input type="date" v-model="editingCage.mice_birth_date">
      </div>
      <div class="form-group">
        <label>笼内小鼠数量</label>
        <input type="number" v-model.number="editingCage.mice_count" min="0">
      </div>
      <div class="form-group">
        <label>笼内小鼠性别</label>
        <select v-model="editingCage.mice_sex">
          <option value="M">雄性</option>
          <option value="F">雌性</option>
          <option value="Mixed">混合</option>
        </select>
      </div>
      <div class="form-group">
        <label>笼内小鼠基因型</label>
        <input type="text" v-model="editingCage.mice_genotype" placeholder="如: WT/KO/其他">
      </div>
      <div class="dialog-buttons">
        <button class="btn btn-outline" @click="editCageDialogVisible = false">取消</button>
        <button class="btn btn-primary" @click="updateCage">确定</button>
      </div>
    </div>
  </div>
  
  <!-- 在组件模板中添加弹窗 -->
  <div v-if="swapStatus === 'select-target'" class="swap-modal">
  <div class="modal-backdrop" @click="cancelSwap"></div>
    <!-- 内容区 -->
    <div class="modal-body">    
      <div class="status-message">
        <p>确认交换以下笼位顺序：</p>
        <div class="cage-pair">
          <div class="selected-cage">
            <i class="material-icons">cage</i>
            <div class="cage-info">
              <div class="cage-id">{{ sourceCage.cage_id }}</div>
              <div class="cage-location">{{ sourceCage.location }}</div>
            </div>
          </div>
          
          <div class="swap-icon">
            <i class="material-icons">swap_horiz</i>
          </div>
          
          <div class="selected-cage">
            <i class="material-icons">cage</i>
            <div class="cage-info">
              <div class="cage-id">{{ targetCage.cage_id }}</div>
              <div class="cage-location">{{ targetCage.location }}</div>
            </div>
          </div>
        </div>

          <!-- 底部按钮 -->
        <div class="modal-footer" v-if="swapStatus === 'select-target'">
          <button @click="cancelSwap" class="btn btn-outline">
            <i class="material-icons">cancel</i> 取消
          </button>
          <button @click="confirmSwap" class="btn btn-primary">
            <i class="material-icons">check</i> 确认
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- PDF渲染区域（隐藏） -->
  <div id="pdf-render-area" class="hidden-pdf-area"></div>
  
  <!-- 加载遮罩 -->
  <div class="loading-overlay" v-if="isGeneratingPDF">
    <div class="spinner"></div>
    <p>正在生成PDF，请稍候...</p>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, computed, onMounted } from 'vue'
import axios from 'axios'
import MouseDetailModal from './MouseDetailView.vue'
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import draggable from 'vuedraggable'
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

// 设置组件名称
defineOptions({
  name: 'AnimalLabDashboard'
})

// 响应式状态
const cages = ref([])
const temporaryMice = ref([])
const dragData = ref(null)
const showMouseDetail = ref(false)
const selectedMouseId = ref(null)
const addCageDialogVisible = ref(false)
const newCage = reactive({
  id: '',
  cage_id: '',
  location: '',
  section: '',
  cage_type: 'normal',
  cage_card_number: '',
  mice_birth_date: '',
  mice_count: null,
  mice_sex: '',
  mice_genotype: ''
})
const cageContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  cage: null
})
const editCageDialogVisible = ref(false)
const editingCage = reactive({
  id: '',
  cage_id: '',
  location: '',
  section: '',
  cage_type: 'normal',
  cage_card_number: '',
  mice_birth_date: '',
  mice_count: null,
  mice_sex: '',
  mice_genotype: ''
})
const activeSection = ref('')
const availableSections = ref([])
const section_key = ref(false)

// 交换状态
const swapStatus = ref(null)
const sourceCage = ref(null)
const targetCage = ref(null)

const showTemporaryArea = ref(false)

// 计算属性 - 过滤笼位
const filteredCages = computed(() => {
  if (!activeSection.value) return cages.value
  return cages.value.filter(cage => cage.section === activeSection.value)
})

// 计算属性 - 按 order 排序后的部分
const sortedSections = computed({
  get: () => [...availableSections.value],
  set: (value) => {
    // 更新本地顺序（不直接修改原始数据）
    const updated = value.map((section, index) => ({
      ...section,
      order: index
    }))
    availableSections.value = updated
  }
})

// 生命周期钩子
onMounted(async () => {
  console.log('DashBoard组件已挂载，开始初始化...')
  console.log('当前URL:', window.location.href)
  console.log('User Agent:', navigator.userAgent)
  
  section_key.value = true
  
  // 延迟1秒再开始加载，确保所有依赖都准备好
  setTimeout(async () => {
    console.log('开始延迟加载数据...')
    await fetchCages()
    await fetchTemporaryMice()
  }, 1000)
  
  // 监听窗口焦点事件，当用户切换回窗口时刷新数据
  window.addEventListener('focus', () => {
    console.log('窗口获得焦点，刷新数据...')
    fetchCages()
    fetchTemporaryMice()
  })
  
  console.log('DashBoard组件初始化完成')
})

// 获取所有笼位数据
async function fetchCages() {
  try {
    console.log('开始获取笼位数据...')
    
    // 强制不使用缓存的axios配置
    const axiosConfig = {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      },
      timeout: 10000
    }
    
    const lresponse = await axios.get('/api/locations', axiosConfig)
    console.log('获取到locations数据:', lresponse.data)
    availableSections.value = lresponse.data
    
    const response = await axios.get('/api/cages', axiosConfig)
    console.log('获取到cages数据:', response.data)
    cages.value = response.data
    
    // 设置默认选中的section为第一个
    if (availableSections.value.length > 0 && section_key.value) {
      activeSection.value = availableSections.value[0].identifier
      newCage.section = availableSections.value[0].identifier
      section_key.value = false
      console.log('设置默认section为:', activeSection.value)
    }
    console.log('笼位数据获取完成')
  } catch (error) {
    console.error('获取笼位信息失败:', error)
    console.log('尝试重新连接...')
    // 延迟重试
    setTimeout(() => {
      fetchCages()
    }, 2000)
  }
}

// 获取临时区小鼠数据
async function fetchTemporaryMice() {
  try {
    const response = await axios.get('/api/cages/-1')
    temporaryMice.value = response.data.map(mouse => ({ ...mouse }))
  } catch (error) {
    console.error('获取临时区小鼠信息失败:', error)
  }
}

// 拖动开始
function handleDragStart(event, mouseId, sourceCageId) {
  dragData.value = {
    mouseId,
    sourceCageId
  }
  event.dataTransfer.setData('text/plain', mouseId)
}

// 放置处理
async function handleDrop(event, targetCageId) {
  event.preventDefault()
  if (dragData.value) {
    const { mouseId, sourceCageId } = dragData.value
    
    try {
      // 更新数据库
      await axios.put(`/api/cage/${targetCageId || '-1'}`, {
        mouse_id: mouseId
      })
      // 更新本地数据
      const mouse = removeMouseFromSource(mouseId, sourceCageId)
      addMouseToTarget(mouse, targetCageId)
    } catch (error) {
      console.error('移动小鼠失败:', error)
      alert('移动小鼠失败，请重试')
    }
    
    dragData.value = null
  }
}

// 更新本地数据：从源位置移除小鼠
function removeMouseFromSource(mouseId, sourceCageId) {
  // 从临时区移除
  if (sourceCageId === '-1') {
    const mouse = temporaryMice.value.find(mouse => mouse.tid === mouseId)
    temporaryMice.value = temporaryMice.value.filter(mouse => mouse.tid !== mouseId)
    return mouse
  }
  // 从笼位中移除
  const cageIndex = cages.value.findIndex(cage => cage.id === sourceCageId)
  if (cageIndex !== -1) {
    const mouse = cages.value[cageIndex].mice.find(mouse => mouse.tid === mouseId)
    cages.value[cageIndex].mice = cages.value[cageIndex].mice.filter(mouse => mouse.tid !== mouseId)
    return mouse
  }
}

// 更新本地数据：添加到目标位置
function addMouseToTarget(mouse, targetCageId) {
  try {
    if (targetCageId === '-1') {
      // 添加到临时区
      if (!temporaryMice.value) temporaryMice.value = []
      temporaryMice.value.push({...mouse})
    } else {
      // 添加到笼位
      const cage = cages.value.find(cage => cage.id === targetCageId)
      if (cage) {
        if (!cage.mice) cage.mice = []
        cage.mice.push({...mouse})
      }
    }
  } catch (error) {
    console.error('获取小鼠详情失败:', error)
  }
}

// 打开小鼠详情
function openMouseDetail(mouseId) {
  selectedMouseId.value = mouseId
  showMouseDetail.value = true
}

// 添加新笼位对话框
function addCageDialog() {
  newCage.section = activeSection.value
  addCageDialogVisible.value = true
}

// 添加新笼位
async function addNewCage() {
  if (!newCage.cage_id || !newCage.section) {
    alert('请填写笼位ID和区域')
    return
  }
  
  try {
    await axios.post('/api/cages', newCage)
    await fetchCages() // 刷新笼位列表
    addCageDialogVisible.value = false
    Object.assign(newCage, { id: '', cage_id: '', location: '', section: '', cage_type: 'normal', cage_card_number: '', mice_birth_date: '', mice_count: null, mice_sex: '', mice_genotype: '' })
  } catch (error) {
    console.error('添加笼位失败:', error)
    alert('添加笼位失败，请重试')
  }
}

// 打开笼位上下文菜单
function openCageContextMenu(event, cage) {
  cageContextMenu.visible = true
  cageContextMenu.x = event.clientX
  cageContextMenu.y = event.clientY
  cageContextMenu.cage = cage
  // 点击其他地方关闭菜单
  document.addEventListener('click', closeContextMenu)
}

// 关闭上下文菜单
function closeContextMenu() {
  cageContextMenu.visible = false
  document.removeEventListener('click', closeContextMenu)
}

// 打开编辑笼位对话框
function openEditCageDialog(cage) {
  Object.assign(editingCage, { ...cage })
  editCageDialogVisible.value = true
  closeContextMenu()
}

// 更新笼位信息
async function updateCage() {
  try {
    await axios.put(`/api/cages/${editingCage.id}`, {
      cage_id: editingCage.cage_id,
      location: editingCage.location,
      section: editingCage.section,
      cage_type: editingCage.cage_type,
      cage_card_number: editingCage.cage_card_number,
      mice_birth_date: editingCage.mice_birth_date,
      mice_count: editingCage.mice_count,
      mice_sex: editingCage.mice_sex,
      mice_genotype: editingCage.mice_genotype
    })
    // 更新本地数据
    const index = cages.value.findIndex(c => c.id === editingCage.id)
    if (index !== -1) {
      cages.value[index].cage_id = editingCage.cage_id
      cages.value[index].location = editingCage.location
      cages.value[index].section = editingCage.section
      cages.value[index].cage_type = editingCage.cage_type
      cages.value[index].cage_card_number = editingCage.cage_card_number
      cages.value[index].mice_birth_date = editingCage.mice_birth_date
      cages.value[index].mice_count = editingCage.mice_count
      cages.value[index].mice_sex = editingCage.mice_sex
      cages.value[index].mice_genotype = editingCage.mice_genotype
    }
    editCageDialogVisible.value = false
  } catch (error) {
    console.error('修改笼位失败:', error)
    alert('修改笼位失败，请重试')
  }
}

// 删除笼位
async function deleteCage(cage) {
  if (!confirm(`确定要删除笼位 ${cage.cage_id} 吗？`)) return
  
  try {
    await axios.delete(`/api/cages/${cage.id}`)
    // 更新本地数据
    cages.value = cages.value.filter(c => c.id !== cage.id)
    closeContextMenu()
  } catch (error) {
    console.error('删除笼位失败:', error)
    alert('删除笼位失败，请重试')
  }
}

// 开始笼位互换
async function exchangeCage(cage) {
  sourceCage.value = cage
  swapStatus.value = "select-source"
  closeContextMenu()
}

// 处理笼位点击
function handleCageClick(cage) {
  if (swapStatus.value === "select-source") {
    if (sourceCage.value.id === cage.id) {
      toast.warning("不能选择同一个笼位进行互换")
      return
    }
    
    targetCage.value = cage
    swapStatus.value = "select-target"
  }
}

// 确认互换操作
function confirmSwap() {
  if (!sourceCage.value || !targetCage.value) return
  
  // 更新笼位列表（在实际应用中应调用API更新数据库）
  updateCageOrder(sourceCage.value.id, targetCage.value.id)
  
  toast.success(`笼位 ${sourceCage.value.cage_id} 和 ${targetCage.value.cage_id} 位置已互换`)
  
  // 重置状态
  resetSwapState()
}

// 取消互换操作
function cancelSwap() {
  toast.error("已取消笼位互换操作")
  resetSwapState()
}

// 重置互换状态
function resetSwapState() {
  swapStatus.value = null
  sourceCage.value = null
  targetCage.value = null
}

// API更新笼位排序
async function updateCageOrder(cage_from_id, cage_to_id) {
  await axios.put('/api/cages/order', {id_from: cage_from_id, id_to: cage_to_id})
  await fetchCages() // 刷新笼位列表
}

// 拖动结束事件
async function onDragEnd() {
  // 获取更新后的顺序
  const newOrder = sortedSections.value.map(section => ({
    id: section.id,
    order: section.order
  })) 
  // 发送更新请求
  try {
    await axios.put('/api/locations/order', { order: newOrder })
    toast.success("位置顺序更新成功")
    console.log('部分顺序更新成功')
  } catch (error) {
    console.error('更新顺序失败:', error)
  }
}

const isGeneratingPDF = ref(false);
const today = new Date();
const today_formatted = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;


// PDF导出函数
const exportToPDF = async () => {
  isGeneratingPDF.value = true;
  
  try {
    // 获取当前区域的笼位数据
    const sectionCages = cages.value.filter(
      cage => cage.section === activeSection.value
    );
    
    // 渲染PDF内容
    renderPDFContent(sectionCages, activeSection.value);
    
    // 等待DOM更新
    await nextTick();
    
    // 生成PDF文件并保存
    const arrayBuffer = await generatePDFAsArrayBuffer();

    // 转换为Uint8Array和普通数组
    const uint8array = new Uint8Array(arrayBuffer);
    const dataArray = Array.from(uint8array);

    const filename = `${today_formatted} ${activeSection.value}.pdf`;

    // 通过PyWebview保存文件
    window.pywebview.api.save_file_dialog(dataArray, filename).then(() => {
      toast.success('PDF保存成功');
    }).catch(error => {
      toast.error('保存失败: ' + error);
    });

    toast.success('PDF导出成功');
  } catch (error) {
    console.error('导出PDF失败:', error);
    toast.error('导出PDF失败，请重试');
  } finally {
    isGeneratingPDF.value = false;
  }
};

// 渲染PDF内容到隐藏区域
const renderPDFContent = (cages, sectionName) => {
  const pdfRenderArea = document.getElementById('pdf-render-area');
  pdfRenderArea.innerHTML = '';
  
  // 按每页20个笼位分页
  const cagesPerPage = 12;
  const pageCount = Math.ceil(cages.length / cagesPerPage);
  
  // 创建分页
  for (let page = 0; page < pageCount; page++) {
    const pageDiv = document.createElement('div');
    pageDiv.className = 'pdf-page';
    
    // 添加页眉
    const header = document.createElement('div');
    header.className = 'pdf-header';
    header.innerHTML = `<h2>${today_formatted} -- ${sectionName}</h2><p>第${page + 1}页，共${pageCount}页</p>`;
    pageDiv.appendChild(header);
    
    // 创建笼位网格
    const grid = document.createElement('div');
    grid.className = 'pdf-cage-grid';
    
    // 获取当前页的笼位
    const startIdx = page * cagesPerPage;
    const endIdx = Math.min(startIdx + cagesPerPage, cages.length);
    const pageCages = cages.slice(startIdx, endIdx);
    
    // 填充笼位
    pageCages.forEach(cage => {
      const cageCard = document.createElement('div');
      cageCard.className = `pdf-cage-card ${cage.cage_type === 'breeding' ? 'breeding' : ''}`;
      
      // 笼位ID和位置
      const cageId = document.createElement('div');
      cageId.className = 'pdf-cage-id';
      cageId.textContent = cage.cage_id + " " + cage.location;
      
      cageCard.appendChild(cageId);
      
      // 小鼠列表
      const miceContainer = document.createElement('div');
      miceContainer.className = 'pdf-cage-mice';
      
      if (cage.mice && cage.mice.length > 0) {
        cage.mice.forEach(mouse => {
          const mouseItem = document.createElement('div');
          mouseItem.className = 'pdf-mouse-item';
          
          const mouseSex = document.createElement('div');
          mouseSex.className = `pdf-mouse-sex ${mouse.sex === 'F' ? 'sex-female' : 'sex-male'}`;
          mouseSex.textContent = mouse.sex === 'F' ? '♀' : '♂';
          
          const mouseInfo = document.createElement('div');
          mouseInfo.className = 'pdf-mouse-info';
          
          const mouseId = document.createElement('div');
          mouseId.className = 'pdf-mouse-id';
          mouseId.textContent = mouse.id;
          
          const mouseGenotype = document.createElement('div');
          mouseGenotype.className = 'pdf-mouse-genotype';
          mouseGenotype.textContent = mouse.genotype;
          
          mouseInfo.appendChild(mouseId);
          mouseInfo.appendChild(mouseGenotype);

          const mouseDays = document.createElement('div');
          mouseDays.className = 'pdf-mouse-days';
          
          if (!mouse.days || mouse.days === 'none') {
            mouseDays.textContent = 'NA';
          } else {
            mouseDays.textContent = `${mouse.days}天`;
          }
          
          mouseItem.appendChild(mouseSex);
          mouseItem.appendChild(mouseInfo);
          mouseItem.appendChild(mouseDays);
          
          miceContainer.appendChild(mouseItem);
        });
      } else {
        const emptyText = document.createElement('div');
        emptyText.className = 'pdf-empty-cage';
        emptyText.textContent = '空笼位';
        miceContainer.appendChild(emptyText);
      }
      
      cageCard.appendChild(miceContainer);
      grid.appendChild(cageCard);
    });
    
    pageDiv.appendChild(grid);
    pdfRenderArea.appendChild(pageDiv);
  }
};

// 生成PDF文件并返回ArrayBuffer
const generatePDFAsArrayBuffer = () => {
  return new Promise((resolve, reject) => {
    const pdfRenderArea = document.getElementById('pdf-render-area');
    
    html2canvas(pdfRenderArea, {
      scale: 2,
      useCORS: true,
      logging: false
    }).then(canvas => {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgData = canvas.toDataURL('image/jpeg', 1.0);
      const imgWidth = 210; // A4宽度（毫米）
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      let position = 0;
      
      // 添加第一页
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
      
      // 如果内容超过一页，添加额外页面
      if (imgHeight > 297) {
        let remainingHeight = imgHeight;
        
        while (remainingHeight > 297) {
          position -= 297;
          pdf.addPage();
          pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
          remainingHeight -= 297;
        }
      }
      
      // 获取PDF文件的ArrayBuffer
      const blob = pdf.output('blob');
      const reader = new FileReader();
      
      reader.onload = function() {
        resolve(reader.result);
      };
      
      reader.onerror = function() {
        reject(new Error('无法读取PDF文件'));
      };
      
      reader.readAsArrayBuffer(blob);
      
      // 清空渲染区域
      pdfRenderArea.innerHTML = '';
    }).catch(reject);
  });
};
</script>

<style scoped>
@import '@material-design-icons/font/index.css';
@import url('./styles/main.css');

/* 主容器布局 */
.cage-view-container {
  display: flex;
  gap: 15px;
  height: calc(100vh - var(--header-height) - var(--footer-height) - 140px);
  overflow: hidden;
}

/* 笼位网格容器 */
.cage-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  grid-auto-rows: 255px;
  gap: 15px;
  padding: 10px;
  overflow-y: auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  align-content: start;
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

.drag-handle {
  cursor: grab;
  margin-right: 8px;
  opacity: 0.5;
  transition: opacity 0.3s;
}

.tab-item:hover .drag-handle {
  opacity: 1;
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

.cage-meta {
  font-size: 12px;
  color: #444;
  margin-bottom: 6px;
}

.cage-meta-row {
  display: flex;
  gap: 6px;
}

.meta-label {
  color: #666;
}

.meta-value {
  color: #111;
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

.mouse-days {
  font-size: 1rem;
  color: #0a0a0a;
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
  z-index: 2;
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  max-height: 80vh;
  overflow-y: auto;
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
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    min-width: 180px;
}

.context-menu ul {
    list-style: none;
    margin: 0;
    padding: 5px 0;
}

.context-menu li {
    padding: 8px 15px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background 0.2s;
}

.context-menu li:hover {
    background-color: #f1f5ff;
}

.context-menu li i {
    font-size: 18px;
    color: #4a9bff;
}

.cage-card.swap-source {
    border-color: #4a9bff;
    animation: pulse 1.5s infinite;
}

.cage-card.swap-target {
    border-color: #10b981;
    animation: pulse-green 1.5s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(74, 155, 255, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(74, 155, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(74, 155, 255, 0); }
}

@keyframes pulse-green {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* 弹窗样式 */
.swap-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-backdrop {
  position: absolute;
  z-index: 1;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-body {
  z-index: 2;
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  padding: 25px;
}

.status-message {
  text-align: center;
  margin-bottom: 20px;
}

.status-message p {
  font-size: 1.1rem;
  margin-bottom: 15px;
  color: #444;
}

.cage-pair {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.selected-cage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.swap-icon {
  padding: 0 20px;
}

.swap-icon i {
  font-size: 36px;
  color: #4a9bff;
}

.cage-info {
  margin-top: 10px;
  text-align: center;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  padding: 15px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}
</style>

/* PDF渲染 - 默认隐藏 */
<style>
    .hidden-pdf-area {
      position: absolute;
      left: -9999px;
      top: -9999px;
      width: 794px; /* A4宽度(像素) */
      background: white;
      padding: 20px;
    }
    
    .pdf-page {
      width: 100%;
      padding: 15px;
      margin-bottom: 20px;
      background: white;
      box-shadow: 0 0 5px rgba(0,0,0,0.1);
    }
    
    .pdf-header {
      text-align: center;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid #2c3e50;
    }
    
    .pdf-cage-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(4, 1fr);
      gap: 12px;
    }
    
    .pdf-cage-card {
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 8px;
      width: 220px;
      height: 240px;
      display: flex;
      flex-direction: column;
      page-break-inside: avoid;
    }
    
    .pdf-cage-id {
      font-weight: bold;
      text-align: center;
      font-size: 14px;
      margin-bottom: 5px;
      border-bottom: 1px solid #eee;
      padding-bottom: 3px;
    }
    
    .pdf-cage-mice {
      flex-grow: 1;
      overflow: hidden;
    }
    
    .pdf-mouse-item {
      display: flex;
      align-items: center;
      margin: 0;
      gap: 1px;
      font-size: 11px;
      box-sizing: border-box;
      background-color: #f8f9fa; /* 添加底纹 */
      border: 1px solid #e9ecef;
    }

    /* 添加斑马条纹效果 */
.pdf-mouse-item:nth-child(odd) {
  background-color: #f8f9fa;
}

.pdf-mouse-item:nth-child(even) {
  background-color: #f1f3f5;
}
    
    .pdf-mouse-sex {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 5px;
      font-size: 10px;
      color: #121111;
      flex-shrink: 0;
    }
    
    .pdf-mouse-info {
      overflow: hidden;
    }

    .pdf-mouse-days {
      text-align: right;
    }
    
    .pdf-mouse-id {
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .pdf-mouse-genotype {
      color: #666;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .pdf-empty-cage {
      text-align: center;
      color: #999;
      font-style: italic;
      margin-top: 20px;
    }
    
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(255, 255, 255, 0.8);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      flex-direction: column;
    }
    
    .spinner {
      width: 50px;
      height: 50px;
      border: 5px solid #f3f3f3;
      border-top: 5px solid #3498db;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 15px;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    </style>