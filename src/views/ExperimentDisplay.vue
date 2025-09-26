<template>
<div class="main-content">
    <div class="content-header">
    <h1 class="page-title">实验数据管理 - {{ experimentName }}</h1>
    </div>

    <!-- 标签页导航 -->
    <div class="tabs">
    <button 
        class="tab-button" 
        :class="{ active: activeTab === 'visualization' }"
        @click="activeTab = 'visualization'"
    >
        <i class="material-icons">bar_chart</i>
        可视化
    </button>
    <button 
        class="tab-button" 
        :class="{ active: activeTab === 'data' }"
        @click="activeTab = 'data'"
    >
        <i class="material-icons">table_chart</i>
        数据列表
    </button>
    </div>

    <!-- 可视化标签页 -->
    <div v-if="activeTab === 'visualization'" class="tab-content">
    <div class="action-buttons">
        <button class="btn btn-primary" @click="showGroupModal = true">
        <i class="material-icons">group</i>
        修改分组
        </button>
        <button class="btn btn-primary" @click="generateChart">
        <i class="material-icons">bar_chart</i>
        生成图表
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
    </div>

    <!-- 数据列表标签页 -->
    <div v-if="activeTab === 'data'" class="tab-content">
    <div class="action-buttons">
        <button class="btn btn-primary" @click="openRecordModal">
        <i class="material-icons">note_add</i>
        录入数据
        </button>
        <button class="btn btn-primary" @click="exportData">
        <i class="material-icons">download</i>
        导出数据
        </button>
    </div>
    
    <!-- 数据表格 -->
    <div class="data-table-container">
        <!-- 搜索和筛选控件 -->
        <div class="table-controls">
        <div class="search-controls">
            <input v-model="searchTerm" placeholder="搜索小鼠编号或数据..." @input="onSearchChange">
            <button @click="resetFilters" class="reset-btn">
            <i class="material-icons">refresh</i>
            </button>
        </div>
        
        <!-- 列筛选 -->
        <div class="column-filters">
            <select v-model="groupFilter" @change="onGroupFilterChange">
            <option value="">所有分组</option>
                <option v-for="group in availableGroups" :key="group" :value="group">
                    {{ group }}
                </option>
            </select>
        </div>
        </div>
        
        <!-- Tabulator 数据表格 -->
        <div ref="tabulatorRef" class="tabulator-table"></div>

        <!-- 右键菜单 -->
        <div v-if="contextMenu.visible" 
        class="context-menu" 
        :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }">
        <div class="menu-item" @click="editRecord">
            <i class="material-icons">edit</i> 编辑记录
        </div>
        <div class="menu-item danger" @click="deleteRecord">
            <i class="material-icons">delete</i> 删除记录
        </div>
        </div>
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
            <button class="btn btn-danger" @click="clearSelection">
                <i class="material-icons btn-icon">clear</i>
                取消选择
            </button>
            <button class="btn btn-danger" @click="clearAllGroups">
                <i class="material-icons btn-icon">delete</i>
                清除所有分组
            </button>
            </div>
            
            <!-- 候选小鼠 -->
            <div class="mb-4">
            <h5>候选小鼠 ({{ candidateMice.length }})</h5>
            <div class="candidate-list" @dragover.prevent @drop="onDrop($event, null)">
                <div v-for="mouse in candidateMice" :key="mouse.tid" class="candidate-item"
                draggable="true" @dragstart="onDragStart($event, null)">
                <div class="mouse-info" @click="toggleCandidateSelection(mouse.tid)">
                    {{ mouse.id }} ({{ mouse.genotype }}, {{ mouse.sex }}, {{ mouse.birth_date }})
                </div>
                </div>
            </div>
            </div>
            
            <!-- 分组展示 -->
            <div class="groups-container">
            <div v-for="(group, groupId) in groupedMice" :key="groupId" class="group-card" @dragover.prevent @drop="onDrop($event, groupId)">
                <div class="group-header">
                <div class="group-name-container">
                    <span
                    v-if="!editingGroups[groupId]" 
                    @dblclick="startEditingGroup(groupId)"
                    class="group-name-display"
                    >{{ groupId }}</span>
                    <input
                    v-else
                    type="text"
                    v-model="editingGroupNames[groupId]"
                    @blur="saveGroupName(groupId)"
                    @keyup.enter="saveGroupName(groupId)"
                    @keyup.escape="cancelEditingGroup(groupId)"
                    ref="groupNameInputs"
                    class="group-name-input"
                    />
                    <button class="btn btn-sm" @click="saveGroupName(groupId)">
                    <i class="material-icons">edit</i>
                    </button>
                </div>
                <button class="btn btn-sm btn-danger" @click="clearSelection">
                    <i class="material-icons">clear</i>
                </button>
                <button class="btn btn-sm btn-danger" @click="deleteGroup(groupId)">
                    <i class="material-icons">delete</i>
                </button>
                </div>
                <div class="group-body">
                <div v-for="mouse in group" :key="mouse.mouse_id" class="mouse-item"
                    draggable="true" @dragstart="onDragStart($event, groupId)">
                    <div class="mouse-info" @click="toggleCandidateSelection(mouse.tid)">
                    {{ mouse.mouse_info.id }} ({{ mouse.mouse_info.genotype }}, {{ mouse.mouse_info.sex }}, {{ mouse.birth_date }})
                    </div>
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
    <div v-if="showRecordModal" class="modal-backdrop" @click.self="closeRecordModal">
    <div class="modal-container">
        <div class="modal-header">
        <h5 class="modal-title">录入实验数据</h5>
        <button type="button" class="btn-close" @click="closeRecordModal">
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
        
        <!-- 录入数据表格 -->
        <div ref="recordTabulatorRef" class="tabulator-table" style="height: 400px;"></div>
        
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
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue';
import { useRoute, onBeforeRouteUpdate } from 'vue-router';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import { TabulatorFull as Tabulator } from 'tabulator-tables';
import 'tabulator-tables/dist/css/tabulator.min.css';

//切换实验时
onBeforeRouteUpdate((to, from) => {
    if (to.params.experimentId !== from.params.experimentId) {
        experimentId.value = to.params.experimentId;
        init();
    }
});

// 路由和实验信息
const route = useRoute();
const experimentId = ref(route.params.experimentId);
const experimentName = ref('');

// 标签页状态
const activeTab = ref('visualization');

// 数据状态
const experimentData = ref([]);
const fieldDefinitions = ref([]);
const hasData = ref(false);
let experimentChart = null;

// 分组管理状态
const candidateMice = ref([]);
const groupedMice = reactive({});
const availableGroups = ref([]);
const selectedCandidates = ref([]);
const editingGroups = ref({});
const editingGroupNames = ref({});
const groupNameInputs = ref([]);
const showGroupModal = ref(false);

// 数据列表状态
const searchTerm = ref('');
const groupFilter = ref('');
const tabulatorInstance = ref(null);
const tabulatorRef = ref(null);
const contextMenu = reactive({
visible: false,
x: 0,
y: 0,
rowData: null
});

// 录入数据状态
const showRecordModal = ref(false);
const recordDate = ref(new Date().toISOString().split('T')[0]);
const researcher = ref('');
const recordTabulatorRef = ref(null);
const recordTabulatorInstance = ref(null);
const recordRowData = ref([]);

// 计算属性
const processedData = computed(() => {
const data = [];
Object.entries(groupedMice).forEach(([groupName, groupArray]) => {
    groupArray.forEach(mouseData => {
    const mouse = mouseData.mouse_info;
    const rowData = {
        id: mouse.id,
        group: groupName,
        mouse_tid: mouse.tid,
    };

    fieldDefinitions.value.forEach(field => {
        const value = getCellValue(mouse.tid, field.id);
        rowData[`field_${field.id}`] = value;
    });

    data.push(rowData);
    });
});
return data;
});

const columnDefs = computed(() => {
const baseColumns = [
    {
    title: '小鼠ID',
    field: 'id',
    width: 150,
    headerHozAlign: 'left',
    frozen: true,
    },
    { 
    title: '分组', 
    field: 'group',
    width: 120,
    }
];

const fieldColumns = fieldDefinitions.value.map(field => ({
    title: field.field_name + (field.unit ? `(${field.unit})` : ''),
    field: `field_${field.id}`,
    width: 120,
    hozAlign: field.data_type === 'INTEGER' || field.data_type === 'REAL' ? 'right' : 'left',
    formatter: (cell) => {
        const value = cell.getValue();
        return value === null || value === undefined ? '-' : value;
    }
}));

return [...baseColumns, ...fieldColumns];
});

const recordColumnDefs = computed(() => {
const columns = [
    {
    title: '分组',
    field: 'group',
    width: 120
    },
    {
    title: '小鼠ID',
    field: 'mouse_id',
    width: 120,
    }
];

fieldDefinitions.value.forEach(field => {
    columns.push({
    title: `${field.field_name}${field.unit ? `(${field.unit})` : ''}${field.is_required ? '*' : ''}`,
    field: `field_${field.id}`,
    editor: field.data_type === 'BOOLEAN' ? 'select' : 'input',
    editorParams: field.data_type === 'BOOLEAN' ? { values: ['是', '否'] } : {},
    width: 150,
    hozAlign: field.data_type === 'INTEGER' || field.data_type === 'REAL' ? 'right' : 'left',
    formatter: (cell) => {
        const value = cell.getValue();
        return value === null || value === undefined || value === '' ? '-' : value;
    },
    validator: field.is_required ? ['required'] : []
    });
});

columns.push({
    title: '备注',
    field: 'notes',
    editor: 'input',
    width: 150
});

return columns;
});

// 生命周期钩子
onMounted(() => {
init();
document.addEventListener('click', () => {
    contextMenu.visible = false;
});
});

// 监听器
watch(processedData, (newData) => {
if (tabulatorInstance.value) {
    tabulatorInstance.value.setData(newData);
}
});

// 方法
async function init() {
try {
    const expResponse = await axios.get(`/api/experiment/${experimentId.value}`);
    experimentName.value = expResponse.data.name;
    fieldDefinitions.value = expResponse.data.fields;
    
    await fetchCandidateMice();
    await fetchGroups();
    await fetchData();
    
    // 初始化 Tabulator
    initTabulator();
} catch (error) {
    console.error('初始化失败:', error);
    toast.error('初始化失败: ' + error.message);
}
}

function initTabulator() {
if (!tabulatorRef.value) return;
    
tabulatorInstance.value = new Tabulator(tabulatorRef.value, {
    data: processedData.value,
    columns: columnDefs.value,
    layout: 'fitColumns',
    height: '85vh',
    selectable: true,
    selectableRange: true,
    clipboard: true,
    clipboardCopyConfig: {
        columnHeaders: true,
        columnGroups: true,
        rowGroups: true,
        columnCalcs: true,
        dataTree: true,
    },
    rowContextMenu: [
        {
            label: "编辑记录",
            action: (e, row) => {
                contextMenu.rowData = row.getData();
                editRecord();
            }
        },
        {
            label: "删除记录",
            action: (e, row) => {
                contextMenu.rowData = row.getData();
                deleteRecord();
            }
        }
    ],
    groupBy: 'group',
    groupHeader: (value, count, data) => {
        return `${value} <span style='color:#666;'>(${count} 条记录)</span>`;
    }
});
}

function initRecordTabulator() {
if (!recordTabulatorRef.value) return;
    
recordTabulatorInstance.value = new Tabulator(recordTabulatorRef.value, {
    data: recordRowData.value,
    columns: recordColumnDefs.value,
    layout: 'fitColumns',
    height: '400px',
    selectable: true,
    clipboard: true,
    groupBy: 'group',
    groupHeader: (value, count, data) => {
        return `${value} <span style='color:#666;'>(${count} 条记录)</span>`;
    }
});
}

function getCellValue(mouseTid, fieldId) {
const mouseData = experimentData.value.find(item => item.mouse_id === mouseTid);
if (!mouseData) return null;

const fieldDef = fieldDefinitions.value.find(f => f.id === fieldId);
if (!fieldDef) return null;

return mouseData[fieldDef.field_name] || null;
}

function onSearchChange() {
    if (tabulatorInstance.value) {
        // 多字段搜索 - 使用 OR 逻辑
        tabulatorInstance.value.setFilter([
        {field: "id", type: "like", value: searchTerm.value},
        {field: "group", type: "like", value: searchTerm.value}
        ]);
    }
}

function onGroupFilterChange() {
    if (tabulatorInstance.value) {
        if (groupFilter.value) {
        // 单字段精确筛选
        tabulatorInstance.value.setFilter("group", "=", groupFilter.value);
        } else {
        tabulatorInstance.value.clearFilter();
        }
    }
}

function resetFilters() {
    searchTerm.value = '';
    groupFilter.value = '';
    if (tabulatorInstance.value) {
        tabulatorInstance.value.clearFilter();
        tabulatorInstance.value.clearSort();
    }
}

function exportData() {
    if (tabulatorInstance.value) {
        // 支持多种格式导出
        tabulatorInstance.value.download("csv", `${experimentName.value}_数据.csv`, {
        bom: true,
        delimiter: ",",
        });
        
        // 也可以导出其他格式
        // tabulatorInstance.value.download("xlsx", `${experimentName.value}_数据.xlsx`);
        // tabulatorInstance.value.download("pdf", `${experimentName.value}_数据.pdf`);
    }
}

async function fetchCandidateMice() {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/candidate_mice`);
    candidateMice.value = response.data;
} catch (error) {
    console.error('获取候选小鼠失败:', error);
    toast.error('获取候选小鼠失败: ' + error.message);
}
}

async function fetchGroups() {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/groups`);
    Object.assign(groupedMice, response.data);
    availableGroups.value = Object.keys(groupedMice);
} catch (error) {
    console.error('获取分组失败:', error);
    toast.error('获取分组失败: ' + error.message);
}
}

async function fetchData() {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/data`);
    experimentData.value = response.data;
    hasData.value = experimentData.value.length > 0;
} catch (error) {
    console.error('获取数据:', error);
    toast.error('获取数据: ' + error.message);
}
}

function toggleCandidateSelection(tid) {
const index = selectedCandidates.value.indexOf(tid);
if (index > -1) {
    selectedCandidates.value.splice(index, 1);
} else {
    selectedCandidates.value.push(tid);
}
}

function onDragStart(event, groupId) {
const ids = selectedCandidates.value.join(',');
event.dataTransfer.setData('mouseIds', ids);
event.dataTransfer.setData('groupId', groupId);
}

function onDrop(event, toGroupId) {
const mouseIds = event.dataTransfer.getData('mouseIds').split(',');
const fromGroupId = event.dataTransfer.getData('groupId');

mouseIds.forEach(id => {
    changeMouseGroup(id, toGroupId, fromGroupId);
});
}

async function changeMouseGroup(mouseId, groupId, newGroupId) {
try {
    await axios.post(`/api/experiment/${experimentId.value}/class_change`, {
    mouse_id: mouseId,
    class_id: groupId,
    class_new_id: newGroupId
    });
    
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('添加小鼠到分组失败:', error);
    toast.error('添加小鼠到分组失败: ' + error.message);
}
}

async function deleteGroup(groupId) {
try {
    await axios.delete(`/api/experiment/${experimentId.value}/groups/${groupId}`);
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('删除分组失败:', error);
    toast.error('删除分组失败: ' + error.message);
}
}

async function clearAllGroups() {
if (!confirm('确定要清除所有分组吗？此操作不可恢复。')) return;

try {
    await axios.delete(`/api/experiment/${experimentId.value}/groups/clear`);
    await fetchCandidateMice();
    await fetchGroups();
} catch (error) {
    console.error('清除所有分组失败:', error);
    toast.error('清除所有分组失败: ' + error.message);
}
}

function clearSelection() {
selectedCandidates.value = [];
}

function addNewGroup() {
    if (availableGroups.value.length >= 5) {
        toast.error('最多只能添加5个分组');
        return;
    }
    const newGroupId = prompt('请输入新分组的名称:');
    if (newGroupId && newGroupId.trim() !== '') {
        groupedMice[newGroupId] = [];
        availableGroups.value.push(newGroupId);
    }
}

function startEditingGroup(groupId) {
editingGroups.value[groupId] = true;
editingGroupNames.value[groupId] = groupId;

nextTick(() => {
    const input = groupNameInputs.value.find(el => el.dataset.groupId === groupId);
    if (input) {
    input.focus();
    input.select();
    }
});
}

async function saveGroupName(oldGroupId) {
    const newGroupId = editingGroupNames.value[oldGroupId].trim();

    if (!newGroupId) {
        alert('分组名称不能为空');
        return;
    }

    if (newGroupId === oldGroupId) {
        cancelEditingGroup(oldGroupId);
        return;
    }

    if (availableGroups.value.includes(newGroupId)) {
        alert('分组名称已存在，请使用其他名称');
        return;
    }

    try {
        const response = await axios.put(`/api/experiment/${experimentId.value}/groups/${oldGroupId}`, {
            new_group_name: newGroupId
            });
        
        if (response.data.success) {
            groupedMice[newGroupId] = groupedMice[oldGroupId];
            delete groupedMice[oldGroupId];
            
            const index = availableGroups.value.indexOf(oldGroupId);
            if (index !== -1) {
                availableGroups.value.splice(index, 1, newGroupId);
            }
            
            editingGroups.value[oldGroupId] = false;
            delete editingGroupNames.value[oldGroupId];
            
            toast.success('分组名称修改成功');
        } else {
            toast.error('分组名称修改失败: ' + response.data.message);
        }
    } catch (error) {
        console.error('修改分组名称失败:', error);
        toast.error('修改分组名称失败: ' + error.message);
    }
}

function cancelEditingGroup(groupId) {
editingGroups.value[groupId] = false;
delete editingGroupNames.value[groupId];
}

async function generateChart() {
if (!hasData.value) {
    toast.error('暂无实验数据，无法生成图表');
    return;
}

nextTick(() => {
    const ctx = document.getElementById('experimentChart');
    if (!ctx) return;
    
    if (experimentChart) {
    experimentChart.destroy();
    }
    
    const xFields = fieldDefinitions.value.filter(f => f.visualize_type === 'x');
    const yFields = fieldDefinitions.value.filter(f => f.visualize_type === 'y');
    const columnFields = fieldDefinitions.value.filter(f => f.visualize_type === 'column');
    
    if (xFields.length > 0 && yFields.length > 0) {
    createXYChart(ctx, xFields, yFields);
    } else if (columnFields.length > 0) {
    createColumnChart(ctx, columnFields);
    } else if (yFields.length > 0 && xFields.length === 0) {
    console.log('只有Y字段，不绘制图表');
    }
});
}

function createXYChart(ctx, xFields, yFields) {
console.log('创建XY图表', xFields, yFields);
}

function createColumnChart(ctx, columnFields) {
console.log('创建柱状图', columnFields);
}

function initRecordData() {
    const rowData = [];

    Object.entries(groupedMice).forEach(([groupName, group]) => {
        group.forEach(mouseData => {
        const mouse = mouseData.mouse_info;
        const row = {
            group: groupName,
            mouse_id: mouse.id,
            mouse_tid: mouse.tid,
            notes: ''
        };
        
        fieldDefinitions.value.forEach(field => {
            row[`field_${field.id}`] = null;
        });
        
        rowData.push(row);
        });
});

recordRowData.value = rowData;
}

async function openRecordModal() {
try {
    initRecordData();
    showRecordModal.value = true;
    
    nextTick(() => {
    initRecordTabulator();
    });
} catch (error) {
    console.error('打开录入模态框失败:', error);
    toast.error('打开录入模态框失败: ' + error.message);
}
}

function closeRecordModal() {
showRecordModal.value = false;
}

function editRecord() {
if (!contextMenu.rowData) return;
console.log('编辑记录:', contextMenu.rowData);
contextMenu.visible = false;
}

async function deleteRecord() {
if (!contextMenu.rowData) return;
if (!confirm('确定要删除这条记录吗？')) return;
try {
    await axios.delete(`/api/experiments/${contextMenu.rowData.id}`);
    toast.success('记录删除成功');
    await fetchData();
} catch (error) {
    console.error('删除记录失败:', error);
    toast.error('删除失败: ' + (error.response?.data?.error || error.message));
}
contextMenu.visible = false;
}

async function saveExperimentRecord() {
try {
    if (!recordTabulatorInstance.value) {
    toast.error('表格未初始化');
    return;
    }
    
    const allRows = recordTabulatorInstance.value.getData();
    
    for (const row of allRows) {
        for (const field of fieldDefinitions.value) {
            if (field.is_required && (row[`field_${field.id}`] === null || row[`field_${field.id}`] === undefined || row[`field_${field.id}`] === '')) {
            toast.error(`小鼠 ${row.mouse_id} 的字段 ${field.field_name} 是必填的`);
            return;
            }
        }
    }
    
    const records = allRows.map(row => {
        const values = {};
        fieldDefinitions.value.forEach(field => {
            values[field.id] = row[`field_${field.id}`];
        });
        
        return {
            mouse_id: row.mouse_tid,
            researcher: researcher.value,
            date: recordDate.value,
            notes: row.notes,
            values: values
        };
    });
    
    const requestData = {
        experiment_type_id: experimentId.value,
        records: records
    };
    
    const response = await axios.post('/api/experiments', requestData);
    toast.success(response.data.message);
    
    showRecordModal.value = false;
    await fetchData();
} catch (error) {
    console.error('保存实验记录失败:', error);
    toast.error('保存失败: ' + (error.response?.data?.error || error.message));
}
}
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

.tabs {
display: flex;
border-bottom: 1px solid #e0e0e0;
margin-bottom: 20px;
}

.tab-button {
padding: 12px 24px;
background: none;
border: none;
cursor: pointer;
display: flex;
align-items: center;
gap: 8px;
font-size: 16px;
color: #666;
border-bottom: 3px solid transparent;
transition: all 0.3s;
}

.tab-button:hover {
color: #3498db;
}

.tab-button.active {
color: #3498db;
border-bottom-color: #3498db;
font-weight: 500;
}

.tab-content {
padding: 10px 0;
}

.data-table-container {
background: white;
border-radius: 8px;
padding: 20px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.table-controls {
display: flex;
justify-content: space-between;
margin-bottom: 20px;
gap: 15px;
}

.search-controls {
display: flex;
gap: 10px;
flex-grow: 1;
max-width: 400px;
}

.search-controls input {
flex-grow: 1;
padding: 8px 12px;
border: 1px solid #dcdfe6;
border-radius: 4px;
font-size: 14px;
}

.search-btn, .reset-btn {
padding: 8px 12px;
border: 1px solid #dcdfe6;
border-radius: 4px;
background: #f5f7fa;
cursor: pointer;
display: flex;
align-items: center;
}

.column-filters select {
padding: 8px 12px;
border: 1px solid #dcdfe6;
border-radius: 4px;
background: white;
}

.group-name-container {
flex-grow: 1;
margin-right: 10px;
}

.group-name-display {
cursor: pointer;
padding: 4px 8px;
border-radius: 4px;
transition: background-color 0.2s;
}

.group-name-display:hover {
background-color: #f0f0f0;
}

.group-name-input {
width: 100%;
padding: 4px 8px;
border: 1px solid #3498db;
border-radius: 4px;
font-size: 1em;
}

.group-actions {
display: flex;
gap: 4px;
}

.tabulator-table {
background: white;
border-radius: 8px;
overflow: hidden;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.context-menu {
position: fixed;
background: white;
border: 1px solid #ccc;
border-radius: 4px;
box-shadow: 0 2px 10px rgba(0,0,0,0.2);
z-index: 1000;
}

.menu-item {
padding: 8px 12px;
cursor: pointer;
display: flex;
align-items: center;
gap: 5px;
}

.menu-item:hover {
background-color: #f5f5f5;
}

.menu-item.danger {
color: #e74c3c;
}
</style>