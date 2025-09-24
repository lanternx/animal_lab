<template>
<div class="main-content">
    <div class="content-header">
    <h1 class="page-title">实验数据管理 - {{ experiment.name }}</h1>
    </div>
    <div class="action-buttons">
        <button class="btn btn-primary" @click="showGroupModal = true">
            <i class="material-icons">group</i>
            修改分组
        </button>
        <button class="btn btn-primary" @click="generateChart">
            <i class="material-icons">bar_chart</i>
            生成图表
        </button>
        <button class="btn btn-primary" @click="showRecordModal = true">
            <i class="material-icons">note_add</i>
            录入数据
        </button>
    </div>

    <!-- 数据展示区域 -->
    <div class="data-display">
        <!-- 图表展示区域 -->
        <div v-if="hasData" class="chart-container">
            <canvas id="experimentChart"></canvas>
        </div>
        
        <!-- 无数据提示 -->
        <div v-else class="no-data">
            <i class="material-icons">bar_chart</i>
            <p>暂无数据，请点击"生成图表"按钮查看可视化结果</p>
        </div>
    </div>

    <!-- 修改分组模态框 -->
    <div v-if="showGroupModal" class="modal-backdrop" @click.self="showGroupModal = false">
    <div class="modal-container">
        <div class="modal-header">
        <h5 class="modal-title">修改分组</h5>
        <button type="button" class="btn-close" @click="showGroupModal = false">
            <i class="material-icons">close</i>
        </button>
        </div>
        <div class="modal-body">
        <div class="group-management">
            <div class="d-flex justify-content-between mb-4">
            <button class="btn btn-primary me-2" @click="fetchGroups">
                <i class="material-icons btn-icon">refresh</i>
                刷新分组
            </button>
            <button class="btn btn-danger" @click="clearAllGroups">
                <i class="material-icons btn-icon">delete</i>
                清除所有分组
            </button>
            </div>
            
            <!-- 候选小鼠 -->
            <div class="mb-4">
            <h5>候选小鼠 ({{ candidateMice.length }})</h5>
            <div class="candidate-list">
                <div v-for="mouse in candidateMice" :key="mouse.tid" class="candidate-item">
                <div class="mouse-info">
                    {{ mouse.id }} ({{ mouse.genotype }}, {{ mouse.sex }})
                </div>
                <select class="form-select-sm" @change="addMouseToGroup(mouse.tid, $event.target.value)">
                    <option value="">选择分组</option>
                    <option v-for="group in availableGroups" :key="group" :value="group">
                    分组 {{ groupLetters[group-1] }}
                    </option>
                </select>
                </div>
            </div>
            </div>
            
            <!-- 分组展示 -->
            <div class="groups-container">
            <div v-for="(group, groupId) in groupedMice" :key="groupId" class="group-card">
                <div class="group-header">
                <span>分组 {{ groupLetters[groupId-1] }} ({{ group.length }})</span>
                <button class="btn btn-sm btn-danger" @click="deleteGroup(groupId)">
                    <i class="material-icons">delete</i>
                </button>
                </div>
                <div class="group-body">
                <div v-for="mouse in group" :key="mouse.mouse_id" class="mouse-item">
                    <div class="mouse-info">
                    {{ mouse.mouse_info.id }} ({{ mouse.mouse_info.genotype }}, {{ mouse.mouse_info.sex }})
                    </div>
                    <button class="btn btn-sm btn-danger" @click="removeMouseFromGroup(groupId, mouse.mouse_id)">
                    <i class="material-icons">close</i>
                    </button>
                </div>
                </div>
            </div>
            
            <div v-if="availableGroups.length < 5" class="group-card add-group" @click="addNewGroup">
                <i class="material-icons">add</i>
                <span>添加分组</span>
            </div>
            </div>
        </div>
        </div>
    </div>
    </div>

    <!-- 录入数据模态框 -->
    <div v-if="showRecordModal" class="modal-backdrop" @click.self="showRecordModal = false">
    <div class="modal-container">
        <div class="modal-header">
        <h5 class="modal-title">录入实验数据</h5>
        <button type="button" class="btn-close" @click="showRecordModal = false">
            <i class="material-icons">close</i>
        </button>
        </div>
        <div class="modal-body">
        <div class="row mb-3">
            <div class="col-md-6">
            <div class="form-group">
                <label for="recordDate" class="form-label">记录日期</label>
                <input type="date" class="form-control" id="recordDate" v-model="recordDate">
            </div>
            </div>
            <div class="col-md-6">
            <div class="form-group">
                <label for="researcher" class="form-label">实验人员</label>
                <input type="text" class="form-control" id="researcher" v-model="researcher">
            </div>
            </div>
        </div>
        
        <div class="form-group mb-3">
            <label for="selectedMouse" class="form-label">选择小鼠</label>
            <select class="form-select" id="selectedMouse" v-model="selectedMouseId">
            <option v-for="mouse in lived_mice" :key="mouse.tid" :value="mouse.tid">
                {{ mouse.id }} ({{ mouse.genotype }}, {{ mouse.sex }})
            </option>
            </select>
        </div>
        
        <div class="field-inputs" v-if="fieldDefinitions.length > 0">
            <h6 class="mb-3">实验数据</h6>
            <div class="row">
            <div 
                class="col-md-6 mb-3" 
                v-for="field in fieldDefinitions" 
                :key="field.id"
            >
                <div class="form-group">
                <label :for="'field'+field.id" class="form-label">
                    {{ field.field_name }}
                    <span class="text-muted" v-if="field.unit">({{ field.unit }})</span>
                    <span class="text-danger" v-if="field.is_required">*</span>
                </label>
                
                <input 
                    v-if="field.data_type === 'INTEGER' || field.data_type === 'REAL'"
                    type="number" 
                    class="form-control" 
                    :id="'field'+field.id"
                    :step="field.data_type === 'REAL' ? '0.01' : '1'"
                    v-model="fieldValues[field.id]"
                >
                
                <input 
                    v-else-if="field.data_type === 'TEXT'"
                    type="text" 
                    class="form-control" 
                    :id="'field'+field.id"
                    v-model="fieldValues[field.id]"
                >
                
                <input 
                    v-else-if="field.data_type === 'DATE'"
                    type="date" 
                    class="form-control" 
                    :id="'field'+field.id"
                    v-model="fieldValues[field.id]"
                >
                
                <select 
                    v-else-if="field.data_type === 'BOOLEAN'"
                    class="form-select" 
                    :id="'field'+field.id"
                    v-model="fieldValues[field.id]"
                >
                    <option :value="null">请选择</option>
                    <option value="true">是</option>
                    <option value="false">否</option>
                </select>
                </div>
            </div>
            </div>
        </div>
        
        <div class="form-group mb-3">
            <label for="notes" class="form-label">备注</label>
            <textarea class="form-control" id="notes" v-model="notes" rows="3"></textarea>
        </div>
        
        <div class="d-grid mt-3">
            <button class="btn btn-primary" @click="saveExperimentRecord">
            <i class="material-icons">save</i> 保存记录
            </button>
        </div>
        </div>
    </div>
    </div>
</div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

// 实验ID
const route = useRoute();
const experimentId = ref(route.params.experimentId);
const experimentName = ref('');

// 数据状态
const lived_mice = ref([]);
const candidateMice = ref([]);
const groupedMice = ref({});
const availableGroups = ref([]);
const groupLetters = ['A', 'B', 'C', 'D', 'E'];
const experimentData = ref([]);
const fieldDefinitions = ref([]);

// 模态框控制
const showGroupModal = ref(false);
const showRecordModal = ref(false);
const recordDate = ref(new Date().toISOString().split('T')[0]);
const researcher = ref('');
const notes = ref('');
const selectedMouseId = ref(null);
const fieldValues = ref({});

// 图表相关
const hasData = ref(false);
let experimentChart = null;

// 初始化
const init = async () => {
try {
    // 获取实验类型信息
    const expResponse = await axios.get(`/api/experiment/${experimentId.value}`);
    experimentName.value = expResponse.data;
    
    // 获取候选小鼠
    await fetchCandidateMice();
    
    // 获取分组情况
    await fetchGroups();

    // 获取数据
    await fetchData();
} catch (error) {
    console.error('初始化失败:', error);
    toast.error('初始化失败: ' + error.message);
}
};

// 获取候选小鼠
const fetchCandidateMice = async () => {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/candidate_mice`);
    candidateMice.value = response.data;
} catch (error) {
    console.error('获取候选小鼠失败:', error);
    toast.error('获取候选小鼠失败: ' + error.message);
}
};

// 获取分组
const fetchGroups = async () => {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/groups`);
    groupedMice.value = response.data;
    
    // 更新可用分组
    availableGroups.value = Object.keys(groupedMice.value).map(Number);
    if (availableGroups.value.length === 0) {
    availableGroups.value = [1];
    } else if (availableGroups.value.length < 5) {
    availableGroups.value.push(Math.max(...availableGroups.value) + 1);
    }
} catch (error) {
    console.error('获取分组失败:', error);
    toast.error('获取分组失败: ' + error.message);
}
};

// 获取数据
const fetchData = async () => {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/data`);
    experimentData.value = response.data;
} catch (error) {
    console.error('获取数据:', error);
    toast.error('获取数据: ' + error.message);
}
};

// 添加小鼠到分组
const addMouseToGroup = async (mouseId, groupId) => {
if (!groupId) return;

try {
    await axios.post(`/api/experiment/${experimentId.value}/groups`, {
    mouse_id: mouseId,
    class_id: parseInt(groupId)
    });
    
    // 更新本地数据
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('添加小鼠到分组失败:', error);
    toast.error('添加小鼠到分组失败: ' + error.message);
}
};

// 从分组移除小鼠
const removeMouseFromGroup = async (groupId, mouseId) => {
try {
    await axios.delete(`/api/experiment/${experimentId.value}/groups/${groupId}/mice/${mouseId}`);
    
    // 更新本地数据
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('从分组移除小鼠失败:', error);
    toast.error('从分组移除小鼠失败: ' + error.message);
}
};

// 删除分组
const deleteGroup = async (groupId) => {
try {
    await axios.delete(`/api/experiment/${experimentId.value}/groups/${groupId}`);
    
    // 更新本地数据
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('删除分组失败:', error);
    toast.error('删除分组失败: ' + error.message);
}
};

// 清除所有分组
const clearAllGroups = async () => {
if (!confirm('确定要清除所有分组吗？此操作不可恢复。')) return;

try {
    await axios.delete(`/api/experiment/${experimentId.value}/groups/clear`);
    
    // 更新本地数据
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('清除所有分组失败:', error);
    toast.error('清除所有分组失败: ' + error.message);
}
};

// 添加新分组
const addNewGroup = () => {
if (availableGroups.value.length >= 5) {
    toast.error('最多只能添加5个分组');
    return;
}

const newGroupId = Math.max(...availableGroups.value) + 1;
availableGroups.value.push(newGroupId);
};

// 生成图表
const generateChart = async () => {

if (!hasData.value) {
    toast.error('暂无实验数据，无法生成图表');
    return;
}

nextTick(() => {
    // 这里实现图表生成逻辑
    // 根据字段的visualize_type属性(x/y/column)动态生成相应图表
    const ctx = document.getElementById('experimentChart');
    if (!ctx) return;
    
    // 销毁现有图表
    if (experimentChart) {
    experimentChart.destroy();
    }
    
    // 获取需要可视化的字段
    const xFields = fieldDefinitions.value.filter(f => f.visualize_type === 'x');
    const yFields = fieldDefinitions.value.filter(f => f.visualize_type === 'y');
    const columnFields = fieldDefinitions.value.filter(f => f.visualize_type === 'column');
    
    // 根据字段类型生成不同的图表
    if (xFields.length > 0 && yFields.length > 0) {
    createXYChart(ctx, xFields, yFields);
    } else if (columnFields.length > 0) {
    createColumnChart(ctx, columnFields);
    } else if (yFields.length > 0 && xFields.length === 0) {
    console.log('只有Y字段，不绘制图表');
    }
});
};

// 创建XY图表（散点图/折线图）
const createXYChart = (ctx, xFields, yFields) => {
// 实现XY图表生成逻辑
console.log('创建XY图表', xFields, yFields);
};

// 创建柱状图
const createColumnChart = (ctx, columnFields) => {
// 实现柱状图生成逻辑
console.log('创建柱状图', columnFields);
};

// 保存实验记录
const saveExperimentRecord = async () => {
try {
    // 验证必填字段
    for (const field of fieldDefinitions.value) {
    if (field.is_required && !fieldValues.value[field.id]) {
        toast.info(`请填写必填字段: ${field.field_name}`);
        return;
    }
    }
    
    if (!selectedMouseId.value) {
    toast.info('请选择小鼠');
    return;
    }
    
    // 构建实验记录对象
    const experimentRecord = {
    mouse_id: selectedMouseId.value,
    experiment_type_id: experimentId.value,
    researcher: researcher.value,
    date: recordDate.value,
    notes: notes.value,
    values: []
    };
    
    // 添加字段值
    for (const field of fieldDefinitions.value) {
    if (fieldValues.value[field.id] !== undefined && fieldValues.value[field.id] !== null) {
        let valueObj = {
        field_definition_id: field.id
        };
        
        switch (field.data_type) {
        case 'INTEGER':
            valueObj.value_int = parseInt(fieldValues.value[field.id]);
            break;
        case 'REAL':
            valueObj.value_real = parseFloat(fieldValues.value[field.id]);
            break;
        case 'TEXT':
            valueObj.value_text = fieldValues.value[field.id];
            break;
        case 'BOOLEAN':
            valueObj.value_bool = fieldValues.value[field.id] === 'true';
            break;
        case 'DATE':
            valueObj.value_date = fieldValues.value[field.id];
            break;
        }
        
        experimentRecord.values.push(valueObj);
    }
    }
    
    // 发送请求
    await axios.post('/api/experiments', experimentRecord);
    toast.success('实验记录保存成功！');
    
    // 重置表单
    showRecordModal.value = false;
    fieldValues.value = {};
    notes.value = '';
    
    // 刷新数据
    await fetchData();
} catch (error) {
    console.error('保存实验记录失败:', error);
    toast.error('保存失败: ' + (error.response?.data?.error || error.message));
}
};

// 组件挂载时初始化
onMounted(() => {
init();
});
</script>

<style scoped>
.experiment-display {
padding: 20px;
}

.action-buttons {
display: flex;
gap: 10px;
margin-bottom: 20px;
}

.action-buttons .btn {
display: flex;
align-items: center;
gap: 5px;
}

.data-display {
background: white;
border-radius: 8px;
padding: 20px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chart-container {
position: relative;
height: 400px;
width: 100%;
}

.no-data {
text-align: center;
padding: 40px 0;
color: #6c757d;
}

.no-data i {
font-size: 3rem;
margin-bottom: 10px;
}

/* 模态框样式 */
.modal-backdrop {
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background-color: rgba(0, 0, 0, 0.5);
z-index: 1000;
display: flex;
align-items: center;
justify-content: center;
}

.modal-container {
background-color: white;
border-radius: 8px;
width: 90%;
max-width: 800px;
max-height: 90vh;
overflow: auto;
}

.modal-header {
padding: 1rem;
background-color: #3498db;
color: white;
border-radius: 8px 8px 0 0;
display: flex;
justify-content: space-between;
align-items: center;
}

.modal-title {
margin: 0;
font-size: 1.25rem;
}

.btn-close {
background: none;
border: none;
color: white;
cursor: pointer;
display: flex;
align-items: center;
justify-content: center;
padding: 0.5rem;
}

.modal-body {
padding: 1.5rem;
}

/* 分组管理样式 */
.group-management {
padding: 10px;
}

.candidate-list {
max-height: 200px;
overflow-y: auto;
border: 1px solid #dee2e6;
border-radius: 4px;
padding: 10px;
}

.candidate-item {
display: flex;
justify-content: space-between;
align-items: center;
padding: 8px;
border-bottom: 1px solid #f1f1f1;
}

.candidate-item:last-child {
border-bottom: none;
}

.groups-container {
display: grid;
grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
gap: 15px;
margin-top: 15px;
}

.group-card {
border-radius: 8px;
overflow: hidden;
box-shadow: 0 2px 4px rgba(0,0,0,0.05);
background: white;
}

.group-header {
display: flex;
justify-content: space-between;
align-items: center;
padding: 0.5rem 1rem;
background-color: #f8f9fa;
border-bottom: 1px solid #e9ecef;
font-weight: 600;
}

.group-body {
padding: 1rem;
max-height: 300px;
overflow-y: auto;
}

.mouse-item {
display: flex;
justify-content: space-between;
align-items: center;
padding: 0.5rem;
border-bottom: 1px solid #f1f1f1;
}

.mouse-item:last-child {
border-bottom: none;
}

.add-group {
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
background-color: #f8f9fa;
border: 2px dashed #ced4da;
cursor: pointer;
min-height: 150px;
}

.add-group:hover {
background-color: #e9ecef;
border-color: #adb5bd;
}

/* 表单样式 */
.form-group {
margin-bottom: 1rem;
}

.form-label {
display: block;
margin-bottom: 0.5rem;
font-weight: 500;
}

.form-control, .form-select {
display: block;
width: 100%;
padding: 0.5rem;
font-size: 1rem;
line-height: 1.5;
color: #495057;
background-color: #fff;
border: 1px solid #ced4da;
border-radius: 4px;
}

.form-select-sm {
width: auto;
padding: 0.25rem 0.5rem;
font-size: 0.875rem;
}

.btn {
padding: 8px 16px;
border-radius: 4px;
border: none;
cursor: pointer;
display: flex;
align-items: center;
font-size: 14px;
transition: all 0.2s;
}

.btn-primary {
background-color: #3498db;
color: white;
}

.btn-danger {
background-color: #e74c3c;
color: white;
}

.btn-sm {
padding: 6px 12px;
font-size: 0.875rem;
}

.d-flex {
display: flex;
}

.justify-content-between {
justify-content: space-between;
}

.mb-4 {
margin-bottom: 1.5rem;
}

.me-2 {
margin-right: 0.5rem;
}

.mt-3 {
margin-top: 1rem;
}

.text-muted {
color: #6c757d;
}

.text-danger {
color: #e74c3c;
}

.d-grid {
display: grid;
}
</style>
