<template>
  <div class="main-content">
    <!-- 标题和小鼠列表 -->
    <div class="section">
      <div class="header-with-button">
        <h2>小鼠管理</h2>
        <button @click="showAddModal = true" class="add-button">
          <i class="material-icons">add</i>
          添加新小鼠
        </button>
      </div>
      
      <!-- 搜索控件 -->
      <div class="search-controls">
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
          </tr>

        </thead>
        <tbody>
          <tr v-for="mouse in filteredMice" :key="mouse.tid"
          @dblclick="openMouseDetail(mouse.tid)"
          @contextmenu.prevent="showContextMenu($event, mouse)">
            <td>{{ mouse.id }}</td>
            <td>{{ mouse.genotype }}</td>
            <td>{{ mouse.sex === 'M' ? '雄性' : '雌性' }}</td>
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
          <li @click="editMouse(contextMenu.mouse)">
            <i class="material-icons">edit</i> 编辑信息
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
        <button @click="showAddModal = true">添加新小鼠</button>
      </div>
    </div>
    
    <!-- 添加小鼠详情浮层组件 -->
    <MouseDetailModal 
      v-if="showMouseDetail" 
      :mouse-id="selectedMouseId" 
      @close="showMouseDetail = false" 
    />

    <!-- 添加小鼠模态框 -->
    <div v-if="showAddModal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加新小鼠</h3>
          <button class="close-btn" @click="showAddModal = false">
            <i class="material-icons">close</i>
          </button>
        </div>
          <div class="form-body">
          <div class="form-group">
            <label>小鼠 ID:</label>
            <input type="text" v-model="newMouse.id">
          </div>
          <!-- 基因型选择 -->
          <div class="form-group">
            <label>基因型:</label>
            <div class="genotype-select-container">
              <select v-model="newMouse.genotype">
                <option v-for="genotype in genotypes" :key="genotype.id" :value="genotype.name">
                  {{ genotype.name }}
                </option>
              </select>
            </div>
          </div>
          
          <div class="form-group">
            <label>性别:</label>
            <select v-model="newMouse.sex">
              <option value="M">雄性</option>
              <option value="F">雌性</option>
            </select>
          </div>
          <div class="form-group">
            <label>出生日期:</label>
            <input type="date" v-model="newMouse.birth_date">
          </div>
        <!-- 父本选择 -->
        <div class="form-group">
        <label>父本 ID:</label>
        <div class="autocomplete">
        <input
          type="text"
          v-model="fatherQuery"
          @input="searchFathers"
          placeholder="输入父本ID搜索..."
          @focus="showFatherSuggestions = true"
          @blur="onBlur"
        />
        <ul v-if="showFatherSuggestions && fatherSuggestions.length" class="suggestions">
        <li
          v-for="mouse in fatherSuggestions"
          :key="mouse.tid"
          @click="selectFather(mouse)"
          >
        {{ mouse.id }} ({{ formatDate(mouse.birth_date) }}) - {{ mouse.genotype }}
        </li>
        </ul>
        </div>
        <div class="selected-parents" v-if="selectedFathers.length">
          <div class="selected-parent" v-for="(father, index) in selectedFathers" :key="father.tid">
            <span>{{ father.id }} ({{ formatDate(father.birth_date) }})</span>
            <button type="button" class="remove-btn" @click="removeFather(index)">移除</button>
          </div>
        </div>
        <p class="info-text" v-else>未选择父本</p>
        </div>
        <!-- 母本选择 -->
        <div class="form-group">
        <label>母本 ID:</label>
        <div class="autocomplete">
        <input
          v-model="motherQuery"
          @input="searchMothers"
          placeholder="输入母本ID搜索..."
          @focus="showMotherSuggestions = true"
          @blur="onBlur"
          >
        <ul v-if="showMotherSuggestions && motherSuggestions.length" class="suggestions">
        <li
          v-for="mouse in motherSuggestions"
          :key="mouse.tid"
          @click="selectMother(mouse)"
          >
        {{ mouse.id }} ({{ formatDate(mouse.birth_date) }}) - {{ mouse.genotype }}
        </li>
        </ul>
        </div>
        <div class="selected-parents" v-if="selectedMothers.length">
          <div class="selected-parent" v-for="(mother, index) in selectedMothers" :key="mother.tid">
            <span>{{ mother.id }} ({{ formatDate(mother.birth_date) }})</span>
            <button type="button" class="remove-btn" @click="removeMother(index)">移除</button>
          </div>
        </div>
        <p class="info-text" v-else>未选择母本</p>
        </div>
        
        <div class="button-group">
          <button @click="addMouse" :disabled="adding" class="primary-btn">
            <i class="material-icons">add</i>
            <span v-if="adding">添加中...</span>
            <span v-else>添加</span>
          </button>
          <button @click="showAddModal = false" class="cancel-btn">
            <i class="material-icons">cancel</i>
            取消
          </button>
        </div>
        </div>
      </div>
    </div>
    
    <!-- 编辑小鼠模态框 -->
    <div v-if="editingMouse" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑小鼠信息</h3>
          <button class="close-btn" @click="cancelEdit">
            <i class="material-icons">close</i>
          </button>
        </div>
        
        <div class="form-body">
          <div class="form-group">
            <label>小鼠 ID:</label>
            <span>{{ editingMouse.id }}</span>
          </div>
          <!-- 基因型选择 -->
          <div class="form-group">
            <label>基因型:</label>
            <div class="genotype-select-container">
              <select v-model="editingMouse.genotype">
                <option v-for="genotype in genotypes" :key="genotype.id" :value="genotype.name">
                  {{ genotype.name }}
                </option>
              </select>
            </div>
          </div>
          
          <div class="form-group">
            <label>性别:</label>
            <select v-model="editingMouse.sex">
              <option value="M">雄性</option>
              <option value="F">雌性</option>
            </select>
          </div>
          <div class="form-group">
            <label>出生日期:</label>
            <input type="date" v-model="editingMouse.birth_date">
          </div>
          <div class="form-group">
            <label>生存状态:</label>
            <select v-model.number="editingMouse.live_status">
              <option value=1>存活</option>
              <option value=0>死亡</option>
              <option value=2>解剖</option>
              <option value=3>意外消失</option>
              <option value=4>丢弃</option>
            </select>
          </div>
          <div class="form-group" v-if="editingMouse.live_status != 1">
            <label>死亡日期:</label>
            <input type="date" v-model="editingMouse.death_date">
          </div>

        <!-- 父本选择 -->
        <div class="form-group">
        <label>父本 ID:</label>
        <div class="autocomplete">
        <input
          type="text"
          v-model="fatherQuery"
          @input="searchFathers"
          placeholder="输入父本ID搜索..."
          @focus="showFatherSuggestions = true"
          @blur="onBlur"
        />
        <ul v-if="showFatherSuggestions && fatherSuggestions.length" class="suggestions">
        <li
          v-for="mouse in fatherSuggestions"
          :key="mouse.tid"
          @click="selectEditFather(mouse)"
          >
        {{ mouse.id }} ({{ formatDate(mouse.birth_date) }}) - {{ mouse.genotype }}
        </li>
        </ul>
        </div>
        <div class="selected-parents" v-if="editFather.length">
          <div class="selected-parent" v-for="(father, index) in editFather" :key="father.tid">
            <span>{{ father.id }} ({{ formatDate(father.birth_date) }})</span>
            <button type="button" class="remove-btn" @click="removeEditFather(index)">移除</button>
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
          @input="searchMothers"
          placeholder="输入母本ID搜索..."
          @focus="showMotherSuggestions = true"
          @blur="onBlur"
        />
        <ul v-if="showMotherSuggestions && motherSuggestions.length" class="suggestions">
        <li
          v-for="mouse in motherSuggestions"
          :key="mouse.tid"
          @click="selectEditMother(mouse)"
          >
        {{ mouse.id }} ({{ formatDate(mouse.birth_date) }}) - {{ mouse.genotype }}
        </li>
        </ul>
        </div>
        <div class="selected-parents" v-if="editMother.length">
          <div class="selected-parent" v-for="(mother, index) in editMother" :key="mother.tid">
            <span>{{ mother.id }} ({{ formatDate(mother.birth_date) }})</span>
            <button type="button" class="remove-btn" @click="removeEditMother(index)">移除</button>
          </div>
        </div>
        <p class="info-text" v-else>未选择母本</p>
        </div>
        </div>
        
        <div class="button-group">
          <button @click="saveMouse" :disabled="saving" class="primary-btn">
            <i class="material-icons">save</i>
            <span v-if="saving">保存中...</span>
            <span v-else>保存</span>
          </button>
          <button @click="cancelEdit" class="cancel-btn">
            <i class="material-icons">cancel</i>
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import MouseDetailModal from './MouseDetailView.vue';

export default {
  name: 'MiceView',
  components: {
    MouseDetailModal
  },
  data() {
    return {
      mice: [],
      filteredMice: [],
      newMouse: {
        id: '',
        genotype: '',
        sex: 'M',
        birth_date: '',
        death_date: '',
        days_old: null,
        weeks_old: null,
        father: [],
        mother: [],
        live_status: null
      },
      searchTerm: '',
      editingMouse: null,
      showAddModal: false,
      loading: false,
      adding: false,
      saving: false,
      showMouseDetail: false,
      selectedMouseId: null,

      // 排序和筛选状态
      sortField: 'id',
      sortDirection: 'asc',
      filters: {
        id: '',
        genotype: '',
        sex: '',
        birth_date: '',
        days_old_min: null,
        days_old_max: null,
        weeks_old_min: null,
        weeks_old_max: null,
        live_status: -1
      },

      // 右键菜单状态
      contextMenu: {
        visible: false,
        x: 0,
        y: 0,
        mouse: null
      },
      // 添加模态框的父本母本相关状态
      fatherQuery: '',
      motherQuery: '',
      showFatherSuggestions: false,
      showMotherSuggestions: false,
      fatherSuggestions: [],
      motherSuggestions: [],
      selectedFathers: [],
      selectedMothers: [],

      editFather: [],
      editMother: [],

      // 基因型相关状态
      genotypes: []
    };
  },
  async mounted() {
    await this.loadMice();
    await this.loadGenotypes();
    document.addEventListener('click', this.closeContextMenu);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeContextMenu);
  },
  watch: {
    searchTerm(newVal) {
      this.filterMice(newVal);
    }
  },
  methods: {
    // 创建配置好的 Axios 实例
    createAxiosInstance() {
      return axios.create({
        baseURL: '/api',
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
    },
    
    calculateAge(birthDate, CalDate) {
      if (!birthDate || !CalDate) return { days: null, weeks: null };

      const cal = new Date(CalDate);
      const birth = new Date(birthDate);
      const diffTime = Math.abs(cal - birth);
      const daysOld = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      const weeksOld = Math.floor(daysOld / 7);
      
      return { days: daysOld, weeks: weeksOld };
    },

    // 加载小鼠列表
    async loadMice() {
      this.loading = true;
      try {
        const api = this.createAxiosInstance();
        const response = await api.get('/mice');
        this.mice = response.data.map(mouse => {
          let days = null;
          let weeks = null;
          if(mouse.birth_date) {
            if(mouse.live_status !== 1 && mouse.death_date) {
              ({ days, weeks } = this.calculateAge(mouse.birth_date, mouse.death_date));
            } else {
              ({ days, weeks } = this.calculateAge(mouse.birth_date, new Date()));
            }
          }
          return {
            ...mouse,
            days_old: days,
            weeks_old: weeks
          };
        });
        this.applyFilters();
        toast.success('小鼠数据加载成功');
      } catch (error) {
        console.error('加载小鼠失败:', error);
        toast.error(`加载小鼠数据失败: ${error.message || '请检查网络连接'}`);
      } finally {
        this.loading = false;
      }
    },

    // 加载基因型列表
    async loadGenotypes() {
      try {
        const api = this.createAxiosInstance();
        const response = await api.get('/genotypes');
        this.genotypes = response.data;
      } catch (error) {
        console.error('加载基因型失败:', error);
        toast.error(`加载基因型失败: ${error.message || '请检查网络连接'}`);
      }
    },
    
    // 排序方法
    sortBy(field) {
      if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortField = field;
        this.sortDirection = 'asc';
      }
      this.applyFilters();
    },
    
    // 重置搜索
    resetSearch() {
      this.searchTerm = '';
      this.filters = {
        id: '',
        genotype: '',
        sex: '',
        birth_date: '',
        days_old_min: null,
        days_old_max: null,
        weeks_old_min: null,
        weeks_old_max: null,
        live_status: -1
      };
      this.applyFilters();
    },

    // 获取排序图标
    sortIcon(field) {
      if (this.sortField !== field) return 'material-icons inactive-icon';
      return this.sortDirection === 'asc' 
        ? 'material-icons' 
        : 'material-icons rotated-icon';
    },

    // 应用筛选和排序
    applyFilters() {
      let result = [...this.mice];
      
      // 应用文本筛选
      if (this.searchTerm) {
        const lowerTerm = this.searchTerm.toLowerCase();
        result = result.filter(mouse => 
          (mouse.id && String(mouse.id).toLowerCase().includes(lowerTerm)) || 
          (mouse.genotype && mouse.genotype.toLowerCase().includes(lowerTerm))
        );
      }
      
      // 应用列筛选
      if (this.filters.id) {
        result = result.filter(m => m.id.includes(this.filters.id));
      }
      if (this.filters.genotype) {
        result = result.filter(m => m.genotype === this.filters.genotype);
      }
      if (this.filters.sex) {
        result = result.filter(m => m.sex === this.filters.sex);
      }
      if (this.filters.birth_date) {
        result = result.filter(m => m.birth_date === this.filters.birth_date);
      }
      if (this.filters.days_old_min) {
        result = result.filter(m => m.days_old >= this.filters.days_old_min);
      }
      if (this.filters.days_old_max) {
        result = result.filter(m => m.days_old <= this.filters.days_old_max);
      }
      if (this.filters.weeks_old_min) {
        result = result.filter(m => m.weeks_old >= this.filters.weeks_old_min);
      }
      if (this.filters.weeks_old_max) {
        result = result.filter(m => m.weeks_old <= this.filters.weeks_old_max);
      }
      if (this.filters.live_status >= 0) {
        result = result.filter(m => m.live_status === this.filters.live_status);
      }
      
      // 应用排序
      result.sort((a, b) => {
        let modifier = this.sortDirection === 'asc' ? 1 : -1;
        
        // 处理日期排序
        if (this.sortField === 'birth_date') {
          const dateA = a.birth_date ? new Date(a.birth_date) : 0;
          const dateB = b.birth_date ? new Date(b.birth_date) : 0;
          return (dateA - dateB) * modifier;
        }
        
        // 处理数字排序
        if (['days_old', 'weeks_old'].includes(this.sortField)) {
          return ((a[this.sortField] || 0) - (b[this.sortField] || 0)) * modifier;
        }
        
        // 默认排序
        if (a[this.sortField] < b[this.sortField]) return -1 * modifier;
        if (a[this.sortField] > b[this.sortField]) return 1 * modifier;
        return 0;
      });
      
      this.filteredMice = result;
    },

    // 验证小鼠数据
    validateMouse(mouse) {
      if (!mouse.id) {
        toast.warning('小鼠编号不能为空');
        return false;
      }
      return true;
    },
    
    // 添加新小鼠
    async addMouse() {
      if (!this.validateMouse(this.newMouse)) return;
      this.newMouse.father = this.selectFathers.map(t => t.tid);
      this.newMouse.mother = this.selectMothers.map(t => t.tid);
      this.adding = true;
      try {
        const api = this.createAxiosInstance();
        const response = await api.post('/mice', this.newMouse);
        
        toast.success(`小鼠 ${response.data.id} 添加成功！`);
        await this.loadMice();
        this.filterMice(this.searchTerm);
        
        // 重置表单
        this.newMouse = {
          id: '',
          genotype: '',
          sex: 'M',
          birth_date: '',
          death_date: '',
          days_old: null,
          weeks_old: null,
          father: [],
          mother: [],
          live_status: null
        };
        
        this.showAddModal = false;
      } catch (error) {
        console.error('添加小鼠失败:', error);
        
        // 更详细的错误处理
        if (error.response) {
          if (error.response.status === 400) {
            toast.error(`请求格式错误: ${error.response.data.error || '请检查输入数据'}`);
          } else if (error.response.status === 500) {
            toast.error('服务器内部错误，请稍后再试');
          } else {
            toast.error(`添加失败: ${error.response.data.error || '未知错误'}`);
          }
        } else {
          toast.error(`添加失败: ${error.message || '网络错误'}`);
        }
      } finally {
        this.adding = false;
      }
    },
    
    // 过滤小鼠列表
    filterMice(term) {
      if (!term) {
        this.filteredMice = [...this.mice];
        return;
      }
      const lowerTerm = term.toLowerCase();
      this.filteredMice = this.mice.filter(mouse => 
        (mouse.id && String(mouse.id).toLowerCase().includes(lowerTerm)) || 
        (mouse.genotype && mouse.genotype.toLowerCase().includes(lowerTerm))
      );
    },

    // 编辑小鼠
    editMouse(mouse) {
      this.editingMouse = { ...mouse };
      // 查找并设置已选的父本母本
      if (mouse.father.length > 0) {
        const father = mouse.father.map(tid => this.mice.find(m => m.tid === tid)).filter(Boolean);
        this.editFather.push(...father);
      }
      if (mouse.mother.length > 0) {
        const mother = mouse.mother.map(tid => this.mice.find(m => m.tid === tid)).filter(Boolean);
        this.editMother.push(...mother);
      }
    },
    
    // 取消编辑
    cancelEdit() {
      this.editingMouse = null;
      this.editFather = [];
      this.editMother = [];
      this.fatherQuery = '';
      this.motherQuery = '';
    },
    
    // 保存小鼠修改
    async saveMouse() {
      if (!this.validateMouse(this.editingMouse)) return;
      this.editingMouse.father = this.editFather.map(t => t.tid);
      this.editingMouse.mother = this.editMother.map(t => t.tid);
      this.saving = true;
      try {
        const api = this.createAxiosInstance();
        await api.put(`/mice/${this.editingMouse.tid}`, this.editingMouse);
        
        toast.success(`小鼠 ${this.editingMouse.id} 信息已更新！`);
        
        // 更新本地数据
        await this.loadMice();
        
        this.editingMouse = null;
        this.editFather = [];
        this.editMother = [];
        this.fatherQuery = '';
        this.motherQuery = '';
      } catch (error) {
        console.error('更新小鼠失败:', error);
        
        if (error.response) {
          if (error.response.status === 404) {
            toast.error('未找到该小鼠记录');
          } else if (error.response.status === 400) {
            toast.error(`请求格式错误: ${error.response.data.error || '请检查输入数据'}`);
          } else {
            toast.error(`更新失败: ${error.response.data.error || '服务器错误'}`);
          }
        } else {
          toast.error(`更新失败: ${error.message || '网络错误'}`);
        }
      } finally {
        this.saving = false;
      }
    },
    
    // 打开小鼠详情
    openMouseDetail(mouseId) {
      this.selectedMouseId = mouseId;
      this.showMouseDetail = true;
      this.closeContextMenu();
    },
    
    // 删除小鼠
    async deleteMouse(mouseId) {
      try {
        const api = this.createAxiosInstance();
        await api.delete(`/mice/${mouseId}`);
        
        toast.success(`小鼠 ${mouseId} 已删除！`);
        
        // 更新本地数据
        const index = this.mice.findIndex(m => m.id === mouseId);
        if (index !== -1) {
          this.mice.splice(index, 1);
          this.filterMice(this.searchTerm);
        }
        this.closeContextMenu();
      } catch (error) {
        console.error('删除小鼠失败:', error);
        
        if (error.response) {
          if (error.response.status === 404) {
            toast.error('未找到该小鼠记录');
          } else {
            toast.error(`删除失败: ${error.response.data.error || '服务器错误'}`);
          }
        } else {
          toast.error(`删除失败: ${error.message || '网络错误'}`);
        }
      }
    },

    // 右键菜单功能
    showContextMenu(event, mouse) {
      this.contextMenu = {
        visible: true,
        x: event.pageX,
        y: event.pageY,
        mouse: mouse
      };
    },
    
    closeContextMenu() {
      this.contextMenu.visible = false;
    },

    // 搜索父本（前端筛选）
    searchFathers() {
      if (this.fatherQuery.length < 2) {
      this.fatherSuggestions = [];
      return;
      }
      const query = this.fatherQuery.toLowerCase();
      this.fatherSuggestions = this.mice.filter(mouse =>
      mouse.sex === 'M' &&
      mouse.id.toLowerCase().includes(query) &&
      mouse.id !== this.editingMouse.tid
      ).slice(0, 10);
    },

     // 搜索母本（前端筛选）
    searchMothers() {
      if (this.motherQuery.length < 2) {
      this.motherSuggestions = [];
      return;
      }
      const query = this.motherQuery.toLowerCase();
      this.motherSuggestions = this.mice.filter(mouse =>
      mouse.sex === 'F' &&
      mouse.id.toLowerCase().includes(query)
      ).slice(0, 10);
    },

    // 选择父本（添加模态框）
    selectFather(mouse) {
      this.selectedFathers.push(mouse);
      this.fatherQuery = '';
      this.showFatherSuggestions = false;
    },

    selectEditFather(mouse) {
      this.editFather.push(mouse);
      this.fatherQuery = '';
      this.showFatherSuggestions = false;
    },

    removeFather(index) {
      this.selectedFathers.splice(index, 1);
    },

    removeEditFather(index) {
      this.editFather.splice(index, 1);
    },

    // 选择母本（添加模态框）
    selectMother(mouse) {
      this.selectedMother.push(mouse);
      this.motherQuery = '';
      this.showMotherSuggestions = false;
    },

    selectEditMother(mouse){
      this.editMother.push(mouse);
      this.motherQuery = '';
      this.showMotherSuggestions = false;
    },

    removeMother(index) {
      this.selectedMothers.splice(index, 1);
    },

    removeEditMother(index) {
      this.editMother.splice(index, 1);
    },

    onBlur() {
      setTimeout(() => {
        this.showFatherSuggestions = false;
        this.showMotherSuggestions = false;
      }, 200);
    },

    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
    }
  }
};
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

/* 模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(3px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eaeaea;
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
  padding: 20px;
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
</style>