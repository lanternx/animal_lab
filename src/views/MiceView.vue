<template>
  <div class="main-content">
    <!-- 标题和小鼠列表 -->
    <div class="section">
      <div class="header-with-button">
        <h2>小鼠管理</h2>
        <button @click="openModal('add')" class="add-button">
          <i class="material-icons">add</i>
          添加新小鼠
        </button>
      </div>
      
      <!-- 搜索控件 -->
      <div class="search-controls" v-if="selectedMice.length === 0">
        <input v-model="searchTerm" placeholder="搜索小鼠ID或基因型" @keyup.enter="loadMice">
        <button @click="loadMice" class="search-btn">
          <i class="material-icons">search</i>
          搜索
        </button>
        <button @click="resetSearch" class="reset-btn">
          <i class="material-icons">refresh</i>
          重置
        </button>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <!-- 选择信息栏 -->
      <div class="selection-info" v-if="selectedMice.length > 0">
          <span>已选择 {{ selectedMice.length }} 只小鼠</span>
            <!-- 下拉选择框 -->
            <div class="custom-select" :class="{ 'is-open': showTestsDoneDropdown }">
              <div class="select-header" @click="toggleTestsDoneDropdown">
                <div class="select-content">
                <!-- 显示已选标签 -->
                <div class="selected-tags">
                  <span v-for="(experiment, index) in batchSelectedTests" :key="experiment.id" class="tag">
                    {{ experiment.name }}
                    <span class="tag-remove" @click="removeTest('batch', index)">×</span>
                  </span>
                </div>
                <span class="placeholder" v-if="batchSelectedTests.length === 0">选择测试...</span>
                </div>
                <div class="select-arrow">▼</div>
              </div>
              
              <div class="select-options" v-if="showTestsDoneDropdown">
                <div 
                  v-for="experiment in experiments" 
                  :key="experiment.id" 
                  class="select-option"
                  @click="selectTest('batch', experiment)"
                >
                  {{ experiment.name }}
                </div>
              </div>
            </div>
          <button @click="batchAddExperiment('计划实验')">批量计划实验</button>
          <button @click="batchAddExperiment('完成实验')">批量完成实验</button>
          <button @click="clearSelection" style="background-color: #95a5a6;">取消选择</button>
      </div>
      
      <!-- 小鼠列表表格 -->
      <table class="mouse-table">
        <thead>
          <tr>
            <th @click="sortBy('id')">
              小鼠ID <i :class="sortIcon('id')"></i>
            </th>
            <th @click="sortBy('genotype')">
              基因型 <i :class="sortIcon('genotype')"></i>
            </th>
            <th @click="sortBy('strain')">
              品系 <i :class="sortIcon('strain')"></i>
            </th>
            <th @click="sortBy('sex')">
              性别 <i :class="sortIcon('sex')"></i>
            </th>
            <th @click="sortBy('birth_date')">
              出生日期 <i :class="sortIcon('birth_date')"></i>
            </th>
            <th @click="sortBy('days_old')">
              日龄 <i :class="sortIcon('days_old')"></i>
            </th>
            <th @click="sortBy('weeks_old')">
              周龄 <i :class="sortIcon('weeks_old')"></i>
            </th>
            <th @click="sortBy('live_status')">
              存活状态 <i :class="sortIcon('live_status')"></i>
            </th>
            <th @click="sortBy('tests_planned')">
              计划实验 <i :class="sortIcon('tests_planned')"></i>
            </th>
            <th @click="sortBy('tests_done')">
              完成实验 <i :class="sortIcon('tests_done')"></i>
            </th>
          </tr>

          <tr class="filter-row">
            <th><input v-model="filters.id" @input="applyFilters" placeholder="筛选ID"></th>
            <th>
              <select v-model="filters.genotype" @change="applyFilters">
                <option value="">全部</option>
                <option v-for="genotype in genotypes" :key="genotype.id" :value="genotype.name">
                  {{ genotype.name }}
                </option>
              </select>
            </th>
            <th><input v-model="filters.strain" @input="applyFilters" placeholder="筛选品系"></th>
            <th>
              <select v-model="filters.sex" @change="applyFilters">
                <option value="">全部</option>
                <option value="M">雄性</option>
                <option value="F">雌性</option>
              </select>
            </th>
            <th><input type="date" v-model="filters.birth_date" @change="applyFilters"></th>
            <th>
              <input v-model.number="filters.days_old_min" @input="applyFilters" placeholder="最小日龄" type="number">
              <input v-model.number="filters.days_old_max" @input="applyFilters" placeholder="最大日龄" type="number">
            </th>
            <th>
              <input v-model.number="filters.weeks_old_min" @input="applyFilters" placeholder="最小周龄" type="number">
              <input v-model.number="filters.weeks_old_max" @input="applyFilters" placeholder="最大周龄" type="number">
            </th>
            <th>
              <select v-model.number="filters.live_status" @change="applyFilters">
                <option value=-1>全部</option>
                <option value=1>存活</option>
                <option value=0>死亡</option>
                <option value=2>解剖</option>
                <option value=3>意外消失</option>
                <option value=4>丢弃</option>
              </select>
            </th>
            <th>
              <input v-model.number="filters.tests_planned" @input="applyFilters" placeholder="实验编号" type="number">
            </th>
            <th>
              <input v-model.number="filters.tests_done" @input="applyFilters" placeholder="实验编号" type="number">
            </th>
          </tr>

        </thead>
        <tbody>
          <tr v-for="(mouse, index) in filteredMice" :key="mouse.tid"
          @click="selectMice(mouse, $event, index)"
          @dblclick="openMouseDetail(mouse.tid)"
          @contextmenu.prevent="showContextMenu($event, mouse)"
          :class="{
              'selected': isSelected(mouse.tid),
              'selected-multiple': selectedMice.length > 1 && isSelected(mouse.tid)
          }">
            <td>{{ mouse.id }}</td>
            <td>{{ mouse.genotype }}</td>
            <td>{{ mouse.strain }}</td>
            <td>
              <div class="mouse-sex" :class="mouse.sex === 'F' ? 'sex-female' : 'sex-male'">
                {{ mouse.sex === 'F' ? '♀' : '♂' }}
              </div>
            </td>
            <td>{{ mouse.birth_date }}</td>
            <td>{{ mouse.days_old }}</td>
            <td>{{ mouse.weeks_old }}</td>
            <td>
              {{ 
                mouse.live_status === 0 ? '死亡' : 
                mouse.live_status === 1 ? '存活' : 
                mouse.live_status === 2 ? '解剖' : 
                mouse.live_status === 3 ? '意外消失' : 
                mouse.live_status === 4 ? '丢弃' : 
                '未知状态' 
              }}
            </td>
            <td>
              {{ mouse.tests_planned.length > 0 ? mouse.tests_planned.join(', ') : '无' }}
            </td>
            <td>
              {{ mouse.tests_done.length > 0 ? mouse.tests_done.join(', ') : '无' }}
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 右键上下文菜单 -->
      <div v-if="contextMenu.visible" 
          class="context-menu" 
          :style="{top: contextMenu.y + 'px', left: contextMenu.x + 'px'}"
          @click.stop>
        <ul>
          <li @click="openMouseDetail(contextMenu.mouse.tid)">
            <i class="material-icons">visibility</i> 查看详情
          </li>
          <li @click="openModal('edit', contextMenu.mouse)">
            <i class="material-icons">edit</i> 编辑信息
          </li>
          <li @click="openModal('template', contextMenu.mouse)">
            <i class="material-icons">playlist_add</i> 以此为模板批量创建小鼠
          </li>
          <li @click="deleteMouse(contextMenu.mouse.tid)" class="danger">
            <i class="material-icons">delete</i> 删除小鼠
          </li>
        </ul>
      </div>
      
      <!-- 空状态 -->
      <div v-if="filteredMice.length === 0 && !loading" class="empty-state">
        <i class="material-icons">pets</i>
        <p>没有找到小鼠记录</p>
        <button @click="openModal('add')">添加新小鼠</button>
      </div>
    </div>
    
    <!-- 添加小鼠详情浮层组件 -->
    <MouseDetailModal 
      v-if="showMouseDetail" 
      :mouse-id="selectedMouseId" 
      @close="showMouseDetail = false" 
    />

    <!-- 统一的小鼠编辑/添加模态框 -->
    <div v-if="showModal" class="modal">
      <div class="modal-overlay" @click.self="closeModal"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ modalTitle }}</h3>
          <button class="close-btn" @click="closeModal">
            <i class="material-icons">close</i>
          </button>
        </div>
        <div class="form-body">
          <!-- 小鼠ID字段（仅在添加模式显示） -->
          <div class="form-group" v-if="modalMode === 'add'">
            <label>小鼠 ID *:</label>
            <input type="text" v-model="formData.id">
          </div>
          <!-- 显示小鼠ID（仅在编辑模式显示） -->
          <div class="form-group" v-if="modalMode === 'edit'">
            <label>小鼠 ID:</label>
            <span>{{ formData.id }}</span>
          </div>          
          <!-- 基因型选择 -->
          <div class="form-group">
            <label>基因型:</label>
            <div class="genotype-select-container">
              <select v-model="formData.genotype">
                <option v-for="genotype in genotypes" :key="genotype.id" :value="genotype.name">
                  {{ genotype.name }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>品系:</label>
            <input type="text" v-model="formData.strain" placeholder="如：C57BL/6J">
          </div>
          
          <div class="form-group">
            <label>性别:</label>
            <select v-model="formData.sex">
              <option value="M">雄性</option>
              <option value="F">雌性</option>
            </select>
          </div>

          <div class="form-group">
            <label>出生日期:</label>
            <input type="date" v-model="formData.birth_date">
          </div>

          <!-- 生存状态（仅在编辑模式显示） -->
          <div class="form-group" v-if="modalMode === 'edit'">
            <label>生存状态:</label>
            <select v-model.number="formData.live_status">
              <option value=1>存活</option>
              <option value=0>死亡</option>
              <option value=2>解剖</option>
              <option value=3>意外消失</option>
              <option value=4>丢弃</option>
            </select>
          </div>
          <!-- 死亡日期（仅在编辑且非存活状态显示） -->
          <div class="form-group" v-if="modalMode === 'edit' && formData.live_status != 1">
            <label>死亡日期:</label>
            <input type="date" v-model="formData.death_date">
          </div>        

          <!-- 父本选择 -->
          <div class="form-group">
            <label>父本 ID:</label>
            <div class="autocomplete">
              <input
                type="text"
                v-model="fatherQuery"
                @input="searchParents('father')"
                placeholder="输入父本ID搜索..."
                @focus="showFatherSuggestions = true"
                @blur="onBlur"
              />
              <ul v-if="showFatherSuggestions && fatherSuggestions.length" class="suggestions">
                <li
                  v-for="mouse in fatherSuggestions"
                  :key="mouse.tid"
                  @click="selectParent('father', mouse)"
                >
                  {{ mouse.id }} ({{ formatDate(mouse.birth_date) }}) - {{ mouse.genotype }}
                </li>
              </ul>
            </div>
            <div class="selected-parents" v-if="selectedFathers.length">
              <div class="selected-parent" v-for="(father, index) in selectedFathers" :key="father.tid">
                <span>{{ father.id }} ({{ formatDate(father.birth_date) }}) - {{ father.genotype }}</span>
                <button type="button" class="remove-btn" @click="removeParent('father', index)">移除</button>
              </div>
            </div>
            <p class="info-text" v-else>未选择父本</p>
          </div>

          <!-- 母本选择 -->
          <div class="form-group">
            <label>母本 ID:</label>
            <div class="autocomplete">
              <input
                type="text"
                v-model="motherQuery"
                @input="searchParents('mother')"
                placeholder="输入母本ID搜索..."
                @focus="showMotherSuggestions = true"
                @blur="onBlur"
              />
              <ul v-if="showMotherSuggestions && motherSuggestions.length" class="suggestions">
                <li
                  v-for="mouse in motherSuggestions"
                  :key="mouse.tid"
                  @click="selectParent('mother', mouse)"
                >
                  {{ mouse.id }} ({{ formatDate(mouse.birth_date) }}) - {{ mouse.genotype }}
                </li>
              </ul>
            </div>
            <div class="selected-parents" v-if="selectedMothers.length">
              <div class="selected-parent" v-for="(mother, index) in selectedMothers" :key="mother.tid">
                <span>{{ mother.id }} ({{ formatDate(mother.birth_date) }}) - {{ mother.genotype }}</span>
                <button type="button" class="remove-btn" @click="removeParent('mother', index)">移除</button>
              </div>
            </div>
            <p class="info-text" v-else>未选择母本</p>
          </div>

        <!-- 已完成测试 -->
        <div class="form-group"  v-if="modalMode === 'edit'">
          <label>已完成测试:</label>
          <div class="tags-input-container">
            <!-- 下拉选择框 -->
            <div class="custom-select" :class="{ 'is-open': showTestsDoneDropdown }">
              <div class="select-header" @click="toggleTestsDoneDropdown">
                <div class="select-content">
                <!-- 显示已选标签 -->
                <div class="selected-tags">
                  <span v-for="(experiment, index) in selectedTestsDone" :key="experiment.id" class="tag">
                    {{ experiment.name }}
                    <span class="tag-remove" @click="removeTest('done', index)">×</span>
                  </span>
                </div>
                <span class="placeholder" v-if="selectedTestsDone.length === 0">选择已完成测试...</span>
                </div>
                <div class="select-arrow">▼</div>
              </div>
              
              <div class="select-options" v-if="showTestsDoneDropdown">
                <div 
                  v-for="experiment in availableTestsDone" 
                  :key="experiment.id" 
                  class="select-option"
                  @click="selectTest('done', experiment)"
                >
                  {{ experiment.name }}
                </div>
                <div v-if="availableTestsDone.length === 0" class="select-option disabled">
                  没有可选的测试
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 计划进行测试 -->
        <div class="form-group">
          <label>计划进行测试:</label>
          <div class="tags-input-container">
            <!-- 下拉选择框 -->
            <div class="custom-select" :class="{ 'is-open': showTestsPlanDropdown }">
              <div class="select-header" @click="toggleTestsPlanDropdown">
                <div class="select-content">
                <!-- 显示已选标签 -->
                <div class="selected-tags">
                  <span v-for="(experiment, index) in selectedTestsPlanned" :key="experiment.id" class="tag">
                    {{ experiment.name }}
                    <span class="tag-remove" @click="removeTest('plan', index)">×</span>
                  </span>
                </div>
                <span class="placeholder" v-if="selectedTestsPlanned.length === 0">选择计划测试...</span>                
                </div>
                <div class="select-arrow">▼</div>
              </div>
              
              <div class="select-options" v-if="showTestsPlanDropdown">
                <div 
                  v-for="experiment in availableTestsPlan" 
                  :key="experiment.id" 
                  class="select-option"
                  @click="selectTest('plan', experiment)"
                >
                  {{ experiment.name }}
                </div>
                <div v-if="availableTestsPlan.length === 0" class="select-option disabled">
                  没有可选的测试
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="button-group">
          <button @click="saveMouse" :disabled="saving" class="primary-btn">
            <i class="material-icons">{{ modalMode === 'add' ? 'add' : 'save' }}</i>
            <span v-if="saving">{{ modalMode === 'add' ? '添加中...' : '保存中...' }}</span>
            <span v-else>{{ modalMode === 'add' ? '添加' : '保存' }}</span>
          </button>
          <button @click="closeModal" class="cancel-btn">
            <i class="material-icons">cancel</i>
            取消
          </button>
        </div>
        </div>
      </div>
    </div>

    <!-- 批量添加小鼠模态框 -->
    <div v-if="modalMode === 'template' && templateMouse" class="modal">
      <div class="modal-overlay" @click.self="closeModal"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>基于模板批量创建小鼠</h3>
          <button class="close-btn" @click="closeModal">
            <i class="material-icons">close</i>
          </button>
        </div>
        <div class="form-body">
        <div class="template-info">
          <h3><i class="material-icons">pets</i> 模板小鼠信息</h3>
          <div class="template-details">
            <div class="detail-item">
              <span class="detail-label">小鼠ID</span>
              <span class="detail-value">{{ templateMouse.id }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">基因型</span>
              <span class="detail-value">{{ templateMouse.genotype }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">品系</span>
              <span class="detail-value">{{ templateMouse.strain }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">性别</span>
              <span class="detail-value">{{ templateMouse.sex }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">出生日期</span>
              <span class="detail-value">{{ formatDate(templateMouse.birth_date) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">存活状态</span>
              <span class="detail-value">{{ templateMouse.live_status }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">父本</span>
              <span class="detail-value" v-for="(father) in templateMouse.father" :key="father.tid">{{ father.id }} </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">母本</span>
              <span class="detail-value" v-for="(mother) in templateMouse.mother" :key="mother.tid">{{ mother.id }} </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">已完成测试</span>
              <span class="detail-value" v-for="(test_done) in templateMouse.tests_done" :key="tests_done">{{ experiments.find(e => e.id === test_done).name }} </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">计划测试</span>
              <span class="detail-value" v-for="(test_planned) in templateMouse.tests_planned" :key="tests_planned">{{ experiments.find(e => e.id === test_planned).name }} </span>
            </div>
          </div>
        </div>

        <div class="form-group">
          <span>创建数量：{{ newMice.length }}</span>
          <button @click="addInputField" >
            <i class="material-icons">add</i>
          </button>
        </div>
        <div v-for="(m, index) in newMice" :key="index" class="input-row">
          <input v-model="m.id" placeholder="ID">
          <select v-model="m.sex">
            <option value="M">雄性</option>
            <option value="F">雌性</option>
          </select>
          <button type="button" class="remove-btn" @click="removeField(index)">移除</button>
        </div>

        <div class="button-group">
          <button @click="saveTemplateMice" :disabled="saving" class="primary-btn">
            <i class="material-icons">save</i>
            <span v-if="saving">保存中...</span>
            <span v-else>保存</span>
          </button>
          <button @click="closeModal" class="cancel-btn">
            <i class="material-icons">cancel</i>
            取消
          </button>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'
import MouseDetailModal from './MouseDetailView.vue'

// 响应式数据
const mice = ref([])
const filteredMice = ref([])
const searchTerm = ref('')
const loading = ref(false)
const saving = ref(false)
const showMouseDetail = ref(false)
const selectedMouseId = ref(null)
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  mouse: null
})
const selectedMice = ref([])
const lastSelectedIndex = ref(-1)
const batchSelectedTests = ref([])

// 模态框相关
const showModal = ref(false)
const modalMode = ref('') // 'add', 'edit', 'template'
const templateMouse = ref(null)
const newMice = ref([])

let clickTimer = ref(null);
const delay = 250;

// 表单数据
const formData = reactive({
  id: '',
  genotype: '',
  sex: 'M',
  birth_date: '',
  death_date: '',
  days_old: null,
  weeks_old: null,
  father: [],
  mother: [],
  live_status: null,
  strain: '',
  tests_done: [],
  tests_planned: []
})

// 筛选和排序
const sortField = ref(null)
const sortDirection = ref('asc')
const filters = reactive({
  id: '',
  genotype: '',
  strain: '',
  sex: '',
  birth_date: '',
  days_old_min: null,
  days_old_max: null,
  weeks_old_min: null,
  weeks_old_max: null,
  live_status: 1,
  tests_done: null,
  tests_planned: null
})

// 父本母本选择
const fatherQuery = ref('')
const motherQuery = ref('')
const showFatherSuggestions = ref(false)
const showMotherSuggestions = ref(false)
const fatherSuggestions = ref([])
const motherSuggestions = ref([])
const selectedFathers = ref([])
const selectedMothers = ref([])

// 控制下拉框显示
const showTestsDoneDropdown = ref(false)
const showTestsPlanDropdown = ref(false)

const selectedTestsDone = ref([])
const selectedTestsPlanned = ref([])

// 计算可用的测试（过滤掉已选的计划测试和已完成测试）
const availableTestsPlan = computed(() => {
  return experiments.value.filter(exp => 
    !selectedTestsPlanned.value.some(selected => selected.id === exp.id) &&
    !selectedTestsDone.value.some(selected => selected.id === exp.id)
  )
})

// 计算可用的完成测试（过滤掉已选的）
const availableTestsDone = computed(() => {
  return selectedTestsPlanned.value.filter(exp => 
    !selectedTestsDone.value.some(selected => selected.id === exp.id)
  )
})

// 数据列表
const genotypes = ref([])
const experiments = ref([])

// 计算属性
const modalTitle = computed(() => {
  switch (modalMode.value) {
    case 'add': return '添加新小鼠'
    case 'edit': return '编辑小鼠信息'
    case 'template': return '基于模板批量创建小鼠'
    default: return ''
  }
})

// 方法
const createAxiosInstance = () => {
  return axios.create({
    baseURL: '/api',
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
}

const calculateAge = (birthDate, calDate) => {
  if (!birthDate || !calDate) return { days: null, weeks: null }

  const cal = new Date(calDate)
  const birth = new Date(birthDate)
  const diffTime = Math.abs(cal - birth)
  const daysOld = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  const weeksOld = Math.floor(daysOld / 7)
  
  return { days: daysOld, weeks: weeksOld }
}

const loadMice = async () => {
  loading.value = true
  try {
    const api = createAxiosInstance()
    const response = await api.get('/mice')
    mice.value = response.data.map(mouse => {
      let days = null
      let weeks = null
      if (mouse.birth_date) {
        if (mouse.live_status !== 1 && mouse.death_date) {
          ({ days, weeks } = calculateAge(mouse.birth_date, mouse.death_date))
        } else {
          ({ days, weeks } = calculateAge(mouse.birth_date, new Date()))
        }
      }
      return {
        ...mouse,
        days_old: days,
        weeks_old: weeks
      }
    })
    applyFilters()
  } catch (error) {
    console.error('加载小鼠失败:', error)
    toast.error(`加载小鼠数据失败: ${error.message || '请检查网络连接'}`)
  } finally {
    loading.value = false
  }
}

const loadGenotypes = async () => {
  try {
    const api = createAxiosInstance()
    const response = await api.get('/genotypes')
    genotypes.value = response.data
  } catch (error) {
    console.error('加载基因型失败:', error)
    toast.error(`加载基因型失败: ${error.message || '请检查网络连接'}`)
  }
}

const loadExperiments = async () => {
  try {
    const api = createAxiosInstance()
    const response = await api.get('/experiment-types')
    experiments.value = response.data
  } catch (error) {
    console.error('加载实验失败:', error)
    toast.error(`加载实验失败: ${error.message || '请检查网络连接'}`)
  }
}

const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  applyFilters()
}

const resetSearch = () => {
  searchTerm.value = ''
  Object.assign(filters, {
    id: '',
    genotype: '',
    sex: '',
    birth_date: '',
    days_old_min: null,
    days_old_max: null,
    weeks_old_min: null,
    weeks_old_max: null,
    live_status: -1,
    tests_done: null,
    tests_planned: null
  })
  applyFilters()
}

const sortIcon = (field) => {
  if (sortField.value !== field) return 'material-icons inactive-icon'
  return sortDirection.value === 'asc' 
    ? 'material-icons' 
    : 'material-icons rotated-icon'
}

const applyFilters = () => {
  let result = [...mice.value]
  
  // 应用文本筛选
  if (searchTerm.value) {
    const lowerTerm = searchTerm.value.toLowerCase()
    result = result.filter(mouse => 
      (mouse.id && String(mouse.id).toLowerCase().includes(lowerTerm)) || 
      (mouse.genotype && mouse.genotype.toLowerCase().includes(lowerTerm))
    )
  }
  
  // 应用列筛选
  if (filters.id) {
    result = result.filter(m => m.id.includes(filters.id))
  }
  if (filters.genotype) {
    result = result.filter(m => m.genotype === filters.genotype)
  }
  if (filters.strain) {
    result = result.filter(m => (m.strain || '').includes(filters.strain))
  }
  if (filters.sex) {
    result = result.filter(m => m.sex === filters.sex)
  }
  if (filters.birth_date) {
    result = result.filter(m => m.birth_date === filters.birth_date)
  }
  if (filters.days_old_min) {
    result = result.filter(m => m.days_old >= filters.days_old_min)
  }
  if (filters.days_old_max) {
    result = result.filter(m => m.days_old <= filters.days_old_max)
  }
  if (filters.weeks_old_min) {
    result = result.filter(m => m.weeks_old >= filters.weeks_old_min)
  }
  if (filters.weeks_old_max) {
    result = result.filter(m => m.weeks_old <= filters.weeks_old_max)
  }
  if (filters.live_status >= 0) {
    result = result.filter(m => m.live_status === filters.live_status)
  }
  if (filters.tests_done) {
    result = result.filter(m => m.tests_done.includes(filters.tests_done))
  }
  if (filters.tests_planned) {
    result = result.filter(m => m.tests_planned.includes(filters.tests_planned))
  }
  
  // 应用排序
  result.sort((a, b) => {
    let modifier = sortDirection.value === 'asc' ? 1 : -1
    
    // 处理日期排序
    if (sortField.value === 'birth_date') {
      const dateA = a.birth_date ? new Date(a.birth_date) : 0
      const dateB = b.birth_date ? new Date(b.birth_date) : 0
      return (dateA - dateB) * modifier
    }
    
    // 处理数字排序
    if (['days_old', 'weeks_old'].includes(sortField.value)) {
      return ((a[sortField.value] || 0) - (b[sortField.value] || 0)) * modifier
    }
    
    // 默认排序
    if (a[sortField.value] < b[sortField.value]) return -1 * modifier
    if (a[sortField.value] > b[sortField.value]) return 1 * modifier
    return 0
  })
  filteredMice.value = result
}

const selectMice = (mouse, event, index) => {
  clearTimeout(clickTimer.value);
  if (!clickTimer.value) {
    clickTimer.value = setTimeout(() => {
      // 执行单击逻辑
      if (event.ctrlKey || event.metaKey) {
        // Ctrl+点击：切换选中状态
        toggleMouseSelection(mouse.tid);
        lastSelectedIndex.value = index;
      } else if (event.shiftKey && lastSelectedIndex.value !== -1) {
          // Shift+点击：选择范围
          selectRange(lastSelectedIndex.value, index);
      } else {
        if (selectedMice.value.length === 1 && selectedMice.value[0] === mouse.tid) {
          // 点击已选中的小鼠：取消选择
          selectedMice.value = [];
          lastSelectedIndex.value = -1;
        } else {
          // 普通点击：选中当前，取消其他
          selectedMice.value = [mouse.tid];
          lastSelectedIndex.value = index;
        }
      }
      clickTimer.value = null;
    }, delay);
  } else {
    clearTimeout(clickTimer.value);
    clickTimer.value = null;
  }

}

// 切换小鼠选中状态
const toggleMouseSelection = (tid) => {
    const index = selectedMice.value.indexOf(tid);
    if (index === -1) {
        selectedMice.value.push(tid);
    } else {
        selectedMice.value.splice(index, 1);
    }
}

// 选择范围
const selectRange = (startIndex, endIndex) => {
    const start = Math.min(startIndex, endIndex);
    const end = Math.max(startIndex, endIndex);
    
    const rangeTids = filteredMice.value
        .slice(start, end + 1)
        .map(mouse => mouse.tid);
    
    // 添加范围内的所有小鼠
    selectedMice.value = [...new Set([...selectedMice.value, ...rangeTids])];
}

// 检查是否选中
const isSelected = (tid) => {
    return selectedMice.value.includes(tid);
}

// 清除选择
const clearSelection = () => {
    selectedMice.value = [];
    lastSelectedIndex.value = -1;
    batchSelectedTests.value = [];
    loadMice()
}

const batchAddExperiment = async (batchTest) => {
  try {
    if (!confirm(`确认要为选中的 ${selectedMice.value.length} 只小鼠批量修改实验 ${batchTest} 吗？注意，未选择的实验会被清除！对应小鼠在其中的数据也会被清除！`)) {
      return
    }
    const api = createAxiosInstance()
    await api.put('/mice/experiments', {
      batchTest: batchTest,
      miceIds: selectedMice.value,
      testIds: batchSelectedTests.value.map(e => e.id)
    })
    toast.success("批量修改" + batchTest +"成功")
  } catch (error) {
    console.error('批量修改实验小鼠失败:', error)
  } finally {
    clearSelection()
  }
}

const validateMouse = (mouse) => {
  if (!mouse.id && modalMode.value === 'add') {
    toast.warning('小鼠编号不能为空')
    return false
  }
  return true
}

const openModal = (mode, mouse = null) => {
  modalMode.value = mode
  if (mode === 'template' && mouse) {
    templateMouse.value = { ...mouse }
    newMice.value = [{ id: '', sex: mouse.sex }]
    return
  }
  
  showModal.value = true
  
  // 重置表单数据
  Object.assign(formData, {
    id: '',
    genotype: '',
    sex: 'M',
    birth_date: '',
    death_date: '',
    days_old: null,
    weeks_old: null,
    father: [],
    mother: [],
    live_status: null,
    strain: '',
    tests_done: [],
    tests_planned: []
  })
  
  selectedFathers.value = []
  selectedMothers.value = []
  selectedTestsDone.value = []
  selectedTestsPlanned.value = []
  
  if (mode === 'edit' && mouse) {
    // 填充编辑数据
    Object.assign(formData, { ...mouse })
    
    // 设置父本母本
    if (mouse.father && mouse.father.length > 0) {
      selectedFathers.value = mouse.father.map(tid => mice.value.find(m => m.tid === tid)).filter(Boolean)
    }
    if (mouse.mother && mouse.mother.length > 0) {
      selectedMothers.value = mouse.mother.map(tid => mice.value.find(m => m.tid === tid)).filter(Boolean)
    }
    
    // 设置测试
    if (mouse.tests_done && mouse.tests_done.length > 0) {
      selectedTestsDone.value = mouse.tests_done.map(id => experiments.value.find(e => e.id === id)).filter(Boolean)
    }
    if (mouse.tests_planned && mouse.tests_planned.length > 0) {
      selectedTestsPlanned.value = mouse.tests_planned.map(id => experiments.value.find(e => e.id === id)).filter(Boolean)
    }
  }
}

const closeModal = () => {
  showModal.value = false
  modalMode.value = ''
  templateMouse.value = null
  newMice.value = []
  fatherQuery.value = ''
  motherQuery.value = ''
}

const saveMouse = async () => {
  if (!validateMouse(formData)) return
  
  // 准备提交数据
  const submitData = {
    ...formData,
    father: selectedFathers.value.map(t => t.tid),
    mother: selectedMothers.value.map(t => t.tid),
    tests_done: selectedTestsDone.value.map(e => e.id),
    tests_planned: selectedTestsPlanned.value.map(e => e.id)
  }
  
  saving.value = true
  try {
    const api = createAxiosInstance()
    
    if (modalMode.value === 'add') {
      await api.post('/mice', submitData)
      toast.success(`小鼠 ${submitData.id} 添加成功！`)
    } else if (modalMode.value === 'edit') {
      await api.put(`/mice/${formData.tid}`, submitData)
      toast.success(`小鼠 ${formData.id} 信息已更新！`)
    }
    
    await loadMice()
    closeModal()
  } catch (error) {
    console.error('保存小鼠失败:', error)
    
    if (error.response) {
      if (error.response.status === 400) {
        toast.error(`请求格式错误: ${error.response.data.error || '请检查输入数据'}`)
      } else if (error.response.status === 500) {
        toast.error('服务器内部错误，请稍后再试')
      } else {
        toast.error(`保存失败: ${error.response.data.error || '未知错误'}`)
      }
    } else {
      toast.error(`保存失败: ${error.message || '网络错误'}`)
    }
  } finally {
    saving.value = false
  }
}

const openMouseDetail = (mouseId) => {
  selectedMouseId.value = mouseId
  showMouseDetail.value = true
  closeContextMenu()
}

const deleteMouse = async (mouseId) => {
  try {
    const api = createAxiosInstance()
    await api.delete(`/mice/${mouseId}`)
    
    // 更新本地数据
    const index = mice.value.findIndex(m => m.tid === mouseId)
    if (index !== -1) {
      toast.success(`小鼠 ${mice.value[index].id} 已删除！`)
      mice.value.splice(index, 1)
      applyFilters()
    }
    closeContextMenu()
  } catch (error) {
    console.error('删除小鼠失败:', error)
    
    if (error.response) {
      if (error.response.status === 404) {
        toast.error('未找到该小鼠记录')
      } else {
        toast.error(`删除失败: ${error.response.data.error || '服务器错误'}`)
      }
    } else {
      toast.error(`删除失败: ${error.message || '网络错误'}`)
    }
  }
}

const showContextMenu = (event, mouse) => {
  contextMenu.visible = true
  contextMenu.x = event.pageX
  contextMenu.y = event.pageY
  contextMenu.mouse = mouse
}

const closeContextMenu = () => {
  contextMenu.visible = false
}

const searchParents = (type) => {
  const query = type === 'father' ? fatherQuery.value : motherQuery.value
  if (query.length < 1) {
    if (type === 'father') fatherSuggestions.value = []
    else motherSuggestions.value = []
    return
  }
  
  const lowerQuery = query.toLowerCase()
  let suggestions = mice.value.filter(mouse =>
    mouse.sex === (type === 'father' ? 'M' : 'F') &&
    mouse.id.toLowerCase().includes(lowerQuery))
  
  if (modalMode.value === 'edit'){
    suggestions.filter(mouse => {
        let flag = false;
        if (formData.tid) {
          if (mouse.tid !== formData.tid) flag=true;
        }
        if (type === 'father') {
          if (mouse.father) return flag && !mouse.father.includes(formData.tid);
          else return flag;
        } else {
          if (mouse.mother) return flag && !mouse.mother.includes(formData.tid);
          else return flag;
        }
    })
  }

  if (type === 'father') fatherSuggestions.value = suggestions.slice(0, 10)
  else motherSuggestions.value = suggestions.slice(0, 10)
}

const selectParent = (type, mouse) => {
  if (type === 'father') {
    selectedFathers.value.push(mouse)
    fatherQuery.value = ''
    showFatherSuggestions.value = false
  } else {
    selectedMothers.value.push(mouse)
    motherQuery.value = ''
    showMotherSuggestions.value = false
  }
}

const removeParent = (type, index) => {
  if (type === 'father') selectedFathers.value.splice(index, 1)
  else selectedMothers.value.splice(index, 1)
}

// 切换下拉框显示
const toggleTestsDoneDropdown = () => {
  showTestsDoneDropdown.value = !showTestsDoneDropdown.value
}
const toggleTestsPlanDropdown = () => {
  showTestsPlanDropdown.value = !showTestsPlanDropdown.value
}


const selectTest = (type, experiment) => {
  if (type === 'done') {
    selectedTestsDone.value.push(experiment)
    const index = selectedTestsPlanned.value.findIndex(p => p.id === experiment.id)
    if (index !== -1) {
      selectedTestsPlanned.value.splice(index, 1)
    }
    showTestsDoneDropdown.value = false
  } else if (type === 'plan') {
    selectedTestsPlanned.value.push(experiment)
    const index = selectedTestsDone.value.findIndex(p => p.id === experiment.id)
    if (index !== -1) {
      selectedTestsDone.value.splice(index, 1)
    }
    showTestsPlanDropdown.value = false
  } else if (type === 'batch') {
    const index = batchSelectedTests.value.findIndex(p => p.id === experiment.id)
    if (index !== -1) {
      toast.info("请勿选择重复实验")
      return
    }
    batchSelectedTests.value.push(experiment)
    showTestsDoneDropdown.value = false
  }
}

// 监听selectedTestsDone的变化，确保与selectedTestsPlanned互斥
watch(selectedTestsDone, (newTestsDone) => {
  // 从计划测试中移除所有已完成的测试
  selectedTestsPlanned.value = selectedTestsPlanned.value.filter(
    plannedTest => !newTestsDone.some(doneTest => doneTest.id === plannedTest.id)
  )
})

const removeTest = (type, index) => {
  if (type === 'done') {selectedTestsDone.value.splice(index, 1)}
  else if (type === 'plan') {selectedTestsPlanned.value.splice(index, 1)}
  else if (type === 'batch') {batchSelectedTests.value.splice(index, 1)}
}

// 点击外部关闭下拉框
const handleClickOutside = (event) => {
  if (!event.target.closest('.custom-select')) {
    showTestsDoneDropdown.value = false
    showTestsPlanDropdown.value = false
  }
}

const onBlur = () => {
  setTimeout(() => {
    showFatherSuggestions.value = false
    showMotherSuggestions.value = false
  }, 200)
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

const addInputField = () => {
  newMice.value.push({ id: '', sex: templateMouse.value.sex })
}

const removeField = (index) => {
  newMice.value.splice(index, 1)
}

const saveTemplateMice = async () => {
  // 检查是否存在ID为空的小鼠
  const hasEmptyId = newMice.value.some(mouse => {
    return mouse.id === null || mouse.id === undefined || mouse.id === ''
  })

  if (hasEmptyId) {
    toast.error("存在ID为空的小鼠")
    return
  }
  
  saving.value = true
  try {
    const api = createAxiosInstance()
    await api.post(`/mice/${templateMouse.value.tid}`, newMice.value)
    
    toast.success(`添加${newMice.value.length}只小鼠！`)
    await loadMice()
    closeModal()
  } catch (error) {
    console.error('批量添加小鼠失败:', error)
    
    if (error.response) {
      if (error.response.status === 404) {
        toast.error('未找到该小鼠记录')
      } else if (error.response.status === 400) {
        toast.error(`请求格式错误: ${error.response.data.error || '请检查输入数据'}`)
      } else {
        toast.error(`添加失败: ${error.response.data.error || '服务器错误'}`)
      }
    } else {
      toast.error(`添加失败: ${error.message || '网络错误'}`)
    }
  } finally {
    saving.value = false
  }
}

// 监听器
watch(searchTerm, (newVal) => {
  if (!newVal) applyFilters()
})

// 生命周期
onMounted(async () => {
  await loadMice()
  await loadGenotypes()
  await loadExperiments()
  document.addEventListener('click', closeContextMenu)
  document.addEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.section {
  margin-bottom: 30px;
  padding: 25px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

/* 头部按钮 */
.header-with-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 15px;
}

.header-with-button h2 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.add-button {
  padding: 10px 20px;
  background: #4a9bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.3s;
}

.add-button:hover {
  background: #3a8beb;
  transform: translateY(-2px);
}

/* 搜索控件 */
.search-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 25px;
  flex-wrap: wrap;
  align-items: center;
}

.search-controls input {
  flex-grow: 1;
  padding: 10px 15px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 1rem;
  min-width: 250px;
  transition: border 0.3s;
}

.search-controls input:focus {
  border-color: #4a9bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(74, 155, 255, 0.2);
}

.search-btn, .reset-btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  transition: all 0.3s;
}

.search-btn {
  background: #f5f7fa;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.search-btn:hover {
  background: #e4e7ed;
  color: #4a9bff;
}

.reset-btn {
  background: #f8f9fa;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.reset-btn:hover {
  background: #e2e8f0;
}

/* 表格样式 */
.mouse-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  position: relative;
  user-select: none;
}

.mouse-table th {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  text-align: left;
  padding: 14px 12px;
  border-bottom: 2px solid #e2e8f0;
  min-width: 90px;
}

.mouse-table th i {
  font-size: 18px;
  vertical-align: middle;
  transition: transform 0.3s;
}

.mouse-table th .inactive-icon {
  color: #c0c4cc;
}

.mouse-table th .rotated-icon {
  transform: rotate(180deg);
}

.mouse-table td {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
  overflow: auto;
  max-width: 200px;
}

.mouse-table tr:nth-child(even) {
  background-color: #f9fafc;
}

.mouse-table tr:hover {
  background-color: #f1f5ff;
}

/* 添加悬停效果 */
.mouse-table tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.mouse-table tr:hover {
  background-color: #f1f5ff !important;
}

.mouse-table tbody tr.selected {
    background-color: #d4e6f1;
}
.mouse-table tbody tr.selected-multiple {
    background-color: #d1ecf1;
}
        
/* 选中行悬停样式 */
.mouse-table tbody tr.selected:hover {
    background-color: #c2d9e9 !important;
}

.mouse-table tbody tr.selected-multiple:hover {
    background-color: #bde1e6 !important;
}

/* 模态框样式 */
.modal {
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

.modal-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(3px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  overflow: hidden; 
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0; /* 防止头部被压缩 */
  padding: 20px;
  border-bottom: 1px solid #eaeaea; /* 可选：添加分隔线 */
  background: white; /* 确保背景色一致 */
  position: sticky; /* 粘性定位 */
  top: 0; /* 粘在顶部 */
  z-index: 11;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.4rem;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #718096;
  padding: 5px;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f8f9fa;
  color: #4a5568;
}

.form-body {
  overflow-y: auto;
  padding: 20px;
  flex-grow: 1;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #4a5568;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #4a9bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(74, 155, 255, 0.2);
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #f1f5f9;
}

.primary-btn {
  padding: 10px 20px;
  background: #4a9bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.3s;
}

.primary-btn:hover:not(:disabled) {
  background: #3a8beb;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f8fafc;
  color: #4a5568;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.3s;
}

.cancel-btn:hover {
  background: #e2e8f0;
}

/* 加载状态 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #4a9bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 50px 20px;
  color: #718096;
}

.empty-state .material-icons {
  font-size: 60px;
  color: #cbd5e0;
  margin-bottom: 15px;
}

.empty-state p {
  font-size: 1.1rem;
  margin-bottom: 20px;
}

.empty-state button {
  padding: 10px 20px;
  background: #4a9bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.filter-row th {
  padding: 5px;
}

.filter-row input, .filter-row select {
  width: 90%;
  padding: 5px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 0.9rem;
}

.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.context-menu ul {
  list-style: none;
  margin: 0;
  padding: 5px 0;
  min-width: 150px;
}

.context-menu li {
  padding: 8px 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.context-menu li:hover {
  background-color: #f5f7fa;
}

.context-menu li.danger {
  color: #f56c6c;
}

.context-menu li i {
  font-size: 18px;
}

.genotype-select-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.genotype-select-container select {
  flex: 1;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.3s;
  background-color: white;
}

.genotype-select-container select:focus {
  border-color: #4a9bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(74, 155, 255, 0.2);
}

.add-genotype-btn {
  padding: 8px 12px;
  background: #4a9bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.add-genotype-btn:hover {
  background: #3a8beb;
}

/* 父本母本选择样式 */
.autocomplete {
  position: relative;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.suggestions li {
  padding: 10px;
  cursor: pointer;
}

.suggestions li:hover {
  background-color: #f1f5ff;
}

.selected-parents {
  margin-top: 10px;
}

.selected-parent {
  background: #f1f5ff;
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.remove-btn {
  background: none;
  border: none;
  color: #f56c6c;
  cursor: pointer;
  padding: 4px;
}

.remove-btn:hover {
  color: #f00;
}

.info-text {
  color: #718096;
  font-size: 0.9rem;
  margin: 5px 0 0;
}

.template-info {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #4a9bff;
}

.template-info h3 {
  font-size: 1.1rem;
  color: #4a5568;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-label {
  font-size: 0.85rem;
  color: #718096;
  margin-bottom: 3px;
}

.detail-value {
  font-weight: 500;
  font-size: 0.95rem;
  color: #2d3748;
}

.form-group button {
  background: #4a9bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.form-group button:hover {
  background: #3a8bef;
}

.input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  align-items: center;
}

.input-row input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 1rem;
}

.input-row select {
  width: 120px;
  padding: 10px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  background: white;
}

.tags-input-container {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px;
  background: white;
  min-height: 42px;
}

.select-content {
  flex-grow: 1;
  margin-right: 8px;
  overflow-x: auto​;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.tag {
  display: inline-flex;
  align-items: center;
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 14px;
  color: #1890ff;
}

.tag-remove {
  margin-left: 6px;
  cursor: pointer;
  font-weight: bold;
  color: #1890ff;
}

.tag-remove:hover {
  color: #ff4d4f;
}

.custom-select {
  position: relative;
}

.select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  cursor: pointer;
  background: white;
  min-height: 42px;
}

.select-header:hover {
  border-color: #c0c4cc;
}

.placeholder {
  color: #c0c4cc;
}

.select-arrow {
  transition: transform 0.3s;
  flex-shrink: 0;
}

.is-open .select-arrow {
  transform: rotate(180deg);
}

.select-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.select-option {
  padding: 8px 12px;
  cursor: pointer;
}

.select-option:hover {
  background-color: #f5f7fa;
}

.select-option.disabled {
  color: #c0c4cc;
  cursor: not-allowed;
}

.select-option.disabled:hover {
  background-color: transparent;
}

.selection-info {
    margin: 10px 0;
    padding: 10px;
    background-color: #e8f4fc;
    border-radius: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.selection-info button {
    padding: 5px 10px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-left: 10px; 
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
  flex-shrink: 0; /* 防止在flex容器中缩小 */
  overflow: hidden; /* 防止内容溢出导致变形 */
  box-sizing: border-box; /* 确保内边距不影响尺寸 */
}

.sex-female {
  background-color: #ff4081;
}

.sex-male {
  background-color: #2196f3;
}

</style>