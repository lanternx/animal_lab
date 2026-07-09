<template>
<div class="main-content">
    <!-- 标题和操作按钮 -->
    <div class="section">
    <div class="header-with-button">
        <h2>体重数据管理</h2>
    </div>
    
    <!-- 搜索和筛选控件 -->
    <div class="search-controls">
        <div class="filter-group">
        <label>小鼠ID:</label>
        <input v-model="filters.mouse_id" placeholder="小鼠ID" @input="loadWeightRecords">
        
        <button @click="resetFilters" class="reset-btn">
        <i class="material-icons">refresh</i>
        重置
        </button>
        </div>

        <div class="filter-group">
        <label>日期范围:</label>
        <input type="date" v-model="filters.start_date"> 至
        <input type="date" v-model="filters.end_date">
        
        <button @click="loadWeightRecords" class="search-btn">
        <i class="material-icons">search</i>
        搜索
        </button>
        </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
    </div>
    
    <!-- 体重记录表格 -->
    <table class="mouse-table">
        <thead>
        <tr>
            <th @click="sortBy('mouse_id')">
            小鼠ID <i :class="sortIcon('mouse_id')"></i>
            </th>
            <th @click="sortBy('birth_date')">
            生日 <i :class="sortIcon('birth_date')"></i>
            </th>
            <th @click="sortBy('record_livingdays')">
            记录年龄(天) <i :class="sortIcon('record_livingdays')"></i>
            </th>
            <th @click="sortBy('record_date')">
            记录时间 <i :class="sortIcon('record_date')"></i>
            </th>
            <th @click="sortBy('weight')">
            体重(g) <i :class="sortIcon('weight')"></i>
            </th>
            <th>操作</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="record in filteredRecords" :key="record.id">
            <td>{{ record.mouse_info.id }}</td>
            <td>{{ record.mouse_info.birth_date }}</td>
            <td>{{ record.record_livingdays }}</td>
            <td>{{ formatDate(record.record_date) }}</td>
            <td>{{ record.weight }}</td>
            <td>
            <button @click="addRecord(record)" class="add-btn">
                <i class="material-icons">add</i>
            </button>
            <button @click="editRecord(record)" class="edit-btn">
                <i class="material-icons">edit</i>
            </button>
            <button @click="deleteRecord(record.id)" class="delete-btn">
                <i class="material-icons">delete</i>
            </button>
            </td>
        </tr>
        </tbody>
    </table>
    
    <!-- 空状态 -->
    <div v-if="filteredRecords.length === 0 && !loading" class="empty-state">
        <i class="material-icons">monitor_weight</i>
        <p>没有找到体重记录</p>
    </div>
    
    <!-- 分页控件 -->
    <div v-if="totalPages > 1" class="pagination">
        <button @click="prevPage" :disabled="currentPage === 1">
        <i class="material-icons">chevron_left</i>
        </button>
        <span>第 {{ currentPage }} 页，共 {{ totalPages }} 页</span>
        <button @click="nextPage" :disabled="currentPage === totalPages">
        <i class="material-icons">chevron_right</i>
        </button>
    </div>
    </div>
    
    <!-- 添加/编辑体重记录模态框 -->
    <div v-if="showAddModal || editingRecord" class="modal-backdrop" @click.self="closeModal">
    <div class="modal-content">
        <div class="modal-header">
        <h3>{{ editingRecord ? '编辑体重记录' : '添加体重记录' }}</h3>
        <button class="close-btn" @click="closeModal">
            <i class="material-icons">close</i>
        </button>
        </div>
        
        <div class="form-body">
        
        <div class="form-group">
            <label>选中小鼠信息:</label>
            <div class="mouse-info">
            <p>ID: {{ selectedMouse.id }}</p>
            <p>基因型: <span v-html="selectedMouse.genotype"></span></p>
            <p>性别: {{ selectedMouse.sex === 'M' ? '雄性' : '雌性' }}</p>
            <p>生日: {{ formatDate(selectedMouse.birth_date) }}</p>
            </div>
        </div>
        
        <div class="form-group">
            <label>记录日期:</label>
            <input type="date" v-model="newRecord.record_date">
        </div>
        
        <div class="form-group">
            <label>体重(g):</label>
            <input type="number" step="0.01" v-model="newRecord.weight">
        </div>
        </div>
        
        <div class="button-group">
        <button @click="saveRecord" :disabled="saving" class="primary-btn">
            <i class="material-icons">{{ editingRecord ? 'save' : 'add' }}</i>
            <span v-if="saving">保存中...</span>
            <span v-else>{{ editingRecord ? '保存' : '添加' }}</span>
        </button>
        <button @click="closeModal" class="cancel-btn">
            <i class="material-icons">cancel</i>
            取消
        </button>
        </div>
    </div>
    </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import axios from 'axios'

// 状态管理
const weightRecords = ref([])
const filteredRecords = ref([])
const loading = ref(false)
const saving = ref(false)
const showAddModal = ref(false)
const editingRecord = ref(null)
const selectedMouse = ref(null)

// 筛选和排序
const filters = ref({
mouse_id: '',
start_date: '',
end_date: ''
})

const sortField = ref('record_date')
const sortDirection = ref('desc')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalRecords = ref(0)

// 计算属性
const totalPages = computed(() => Math.ceil(totalRecords.value / pageSize.value))

const newRecord = ref({
mouse_id: '',
record_date: new Date().toISOString().split('T')[0],
weight: ''
})

// 生命周期
onMounted(() => {
loadWeightRecords()
})

// 方法
const loadWeightRecords = async () => {
try {
    loading.value = true
    const params = {
    page: currentPage.value,
    limit: pageSize.value,
    ...filters.value
    }
    
    // 移除空值参数
    Object.keys(params).forEach(key => {
    if (params[key] === '' || params[key] === null) {
        delete params[key]
    }
    })
    
    const response = await axios.get('/api/weight_records', { params })
    weightRecords.value = response.data.records
    totalRecords.value = response.data.total
    applySorting()
} catch (error) {
    console.error('加载体重记录失败:', error)
    toast.error('加载体重记录失败')
} finally {
    loading.value = false
}
}

const saveRecord = async () => {
try {
    saving.value = true
    
    if (!newRecord.value.weight || parseFloat(newRecord.value.weight) <= 0) {
    toast.error('请输入有效的体重值')
    return
    }
    if (!newRecord.value.record_date) {
    toast.error('请输入记录时间')
    return
    }
    
    if (editingRecord.value) {
        // 更新记录
        await axios.put(`/api/weight_records/${editingRecord.value.id}`, newRecord.value)
        toast.success('体重记录更新成功')
    } else {
        // 添加新记录
        await axios.post('/api/weight_records', newRecord.value)
        toast.success('体重记录添加成功')
    }
    } catch (error) {
        console.error('保存体重记录失败:', error)
        toast.error('保存体重记录失败')
    } finally {
        saving.value = false
    }
    closeModal()
    loadWeightRecords()
}

const addRecord = (record) => {
newRecord.value = {
    mouse_id: record.mouse_id,
    record_date: new Date(),
    weight: ''
}
selectedMouse.value = record.mouse_info
showAddModal.value = true
}

const editRecord = (record) => {
editingRecord.value = record
newRecord.value = { ...record }
selectedMouse.value = record.mouse_info
showAddModal.value = true
}

const deleteRecord = async (id) => {
if (!confirm('确定要删除这条体重记录吗？')) return

try {
    await axios.delete(`/api/weight_records/${id}`)
    toast.success('体重记录删除成功')
    loadWeightRecords()
} catch (error) {
    console.error('删除体重记录失败:', error)
    toast.error('删除体重记录失败')
}
}

const closeModal = () => {
showAddModal.value = false
editingRecord.value = null
newRecord.value = {
    mouse_id: '',
    record_date: new Date().toISOString().split('T')[0],
    weight: ''
}
selectedMouse.value = null
}

const resetFilters = () => {
filters.value = {
    mouse_id: '',
    start_date: '',
    end_date: ''
}
loadWeightRecords()
}

const sortBy = (field) => {
if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
} else {
    sortField.value = field
    sortDirection.value = 'asc'
}
applySorting()
}

const applySorting = () => {
filteredRecords.value = [...weightRecords.value].sort((a, b) => {
    let modifier = sortDirection.value === 'asc' ? 1 : -1
    
    if (sortField.value === 'record_date') {
    return (new Date(a[sortField.value]) - new Date(b[sortField.value])) * modifier
    }
    
    if (a[sortField.value] < b[sortField.value]) return -1 * modifier
    if (a[sortField.value] > b[sortField.value]) return 1 * modifier
    return 0
})
}

const sortIcon = (field) => {
if (sortField.value !== field) return 'material-icons inactive-icon'
return sortDirection.value === 'asc' 
    ? 'material-icons' 
    : 'material-icons rotated-icon'
}

const formatDate = (dateString) => {
if (!dateString) return ''
const date = new Date(dateString)
return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

const nextPage = () => {
if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadWeightRecords()
}
}

const prevPage = () => {
if (currentPage.value > 1) {
    currentPage.value--
    loadWeightRecords()
}
}

// 监听筛选条件变化
watch(filters, () => {
currentPage.value = 1
loadWeightRecords
}, { deep: true })
</script>

<style scoped>
.mouse-info {
background: #f5f7fa;
padding: 12px;
border-radius: 6px;
margin-top: 8px;
}

.mouse-info p {
margin: 4px 0;
font-size: 14px;
}

.pagination {
display: flex;
justify-content: center;
align-items: center;
margin-top: 20px;
gap: 15px;
}

.pagination button {
padding: 8px 12px;
background: #f8f9fa;
border: 1px solid #dcdfe6;
border-radius: 4px;
cursor: pointer;
}

.pagination button:disabled {
opacity: 0.5;
cursor: not-allowed;
}

.add-btn, .edit-btn, .delete-btn {
padding: 6px;
border: none;
border-radius: 4px;
cursor: pointer;
margin-right: 5px;
}

.add-btn {
background: #23d03d;
color: white;
}

.edit-btn {
background: #1890ff;
color: white;
}

.delete-btn {
background: #f5222d;
color: white;
}

.edit-btn:hover {
background: #40a9ff;
}

.delete-btn:hover {
background: #ff4d4f;
}

@media (max-width: 1200px) {
.search-controls {
    flex-direction: column;
    align-items: flex-start;
}
.filter-group {
    margin-bottom: 10px;
    width: 100%;
}
.filter-group input,
.filter-group select {
    flex-grow: 1;
}
}

@media (max-width: 768px) {
.mouse-table {
    font-size: 14px;
}
}

.mouse-table {
  cursor: pointer;
  position: relative;
  user-select: none;
}

.modal-backdrop {
  backdrop-filter: blur(3px);
}

.modal-content {
  overflow-y: auto;
}

.form-body {
  padding: 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.filter-group {
display: flex;
align-items: center;
margin-right: 15px;
gap: 12px;
}

.filter-group label {
margin-right: 8px;
font-weight: 500;
white-space: nowrap;
}

.filter-group input {
  flex-grow: 1;
  padding: 10px 15px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 1rem;
  min-width: 250px;
  transition: border 0.3s;
}

.filter-group select {
padding: 8px;
border: 1px solid #dcdfe6;
border-radius: 4px;
font-size: 14px;
}

.filter-group input:focus {
  border-color: #4a9bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(74, 155, 255, 0.2);
}
</style>