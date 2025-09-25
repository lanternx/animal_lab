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
            <input v-model="searchTerm" placeholder="搜索小鼠编号或数据...">
            <button @click="resetFilters" class="reset-btn">
                <i class="material-icons">refresh</i>
            </button>
            </div>
            
            <!-- 列筛选 -->
            <div class="column-filters">
            <select v-model="groupFilter">
                <option value="">所有分组</option>
                <option v-for="group in availableGroups" :key="group" :value="group">
                    {{ group }}
                </option>
            </select>
            </div>
        </div>
        
        <!-- 数据表格 -->
        <ag-grid-vue
            class="ag-theme-alpine"
            style="height: 85vh;"
            :columnDefs="columnDefs"
            :rowData="processedData"
            :defaultColDef="defaultColDef"
            :enableRangeSelection="true"
            :enableCellTextSelection="true"
            :ensureDomOrder="true"
            :groupHeaderHeight="40"
            :headerHeight="40"
            :rowHeight="35"
            :suppressRowClickSelection="true"
            :context="gridContext"
            @gridReady="onGridReady"
            @cellContextMenu="onCellContextMenu"
            @sortChanged="onSortChanged"
            @filterChanged="onFilterChanged"
        />

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
        
        <!-- Ag-Grid 数据表格 -->
        <div class="ag-grid-container" style="flex: 1; min-height: 0;">
        <ag-grid-vue
            class="ag-theme-alpine"
            style="height: 100%; width: 100%;"
            :columnDefs="recordColumnDefs"
            :rowData="recordRowData"
            :defaultColDef="recordDefaultColDef"
            :groupHeaderHeight="40"
            :headerHeight="40"
            :rowHeight="35"
            :suppressRowClickSelection="true"
            :enableCellChangeFlash="true"
            :stopEditingWhenCellsLoseFocus="true"
            @gridReady="onRecordGridReady"
            @cellValueChanged="onCellValueChanged"
        />
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
import { ref, onMounted, watch, computed, nextTick, reactive } from 'vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import { AgGridVue } from "ag-grid-vue3";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { useRoute } from 'vue-router';

// 实验ID
const route = useRoute();
const experimentId = ref(route.params.experimentId);
const experimentName = ref('');

// 标签页状态
const activeTab = ref('visualization');

const selectedCandidates = ref([]);
const editingGroups = ref({}); // 跟踪哪些分组正在编辑
const editingGroupNames = ref({}); // 存储编辑中的分组名称
const groupNameInputs = ref([]); // 用于引用输入框DOM元素

// 数据状态
const lived_mice = ref([]);
const candidateMice = ref([]);
const groupedMice = ref({});
const availableGroups = ref([]);
const groupLetters = ['A', 'B', 'C', 'D', 'E'];
const experimentData = ref([]);
const fieldDefinitions = ref([]);

// 数据列表相关状态
const searchTerm = ref('');
const groupFilter = ref('');
const sortField = ref('mouse_id');
const sortDirection = ref('asc');
const filters = ref({
    mouse_id: '',
    class_id: ''
});
const gridApi = ref(null);
const gridContext = reactive({});

// 模态框控制
const showGroupModal = ref(false);
const showRecordModal = ref(false);
const recordDate = ref(new Date().toISOString().split('T')[0]);
const researcher = ref('');
const notes = ref('');
const selectedMouseId = ref(null);
const fieldValues = ref({});

// 右键菜单状态
const contextMenu = reactive({
    visible: false,
    x: 0,
    y: 0,
    rowData: null
});

// 图表相关
const hasData = ref(false);
let experimentChart = null;

// 计算属性：过滤和排序后的数据
const filteredData = computed(() => {
    let result = [...experimentData.value];

    // 应用搜索词筛选
    if (searchTerm.value) {
        const term = searchTerm.value.toLowerCase();
        result = result.filter(item => {
        const mouseId = getMouseId(item.mouse_id);
        return mouseId.toLowerCase().includes(term) || 
                JSON.stringify(item).toLowerCase().includes(term);
        });
    }

    // 应用列筛选
    Object.keys(filters.value).forEach(key => {
        if (filters.value[key]) {
        if (key === 'class_id') {
            result = result.filter(item => item[key] == filters.value[key]);
        } else {
            const filterVal = filters.value[key].toString().toLowerCase();
            result = result.filter(item => {
            const itemVal = item[key] ? item[key].toString().toLowerCase() : '';
            return itemVal.includes(filterVal);
            });
        }
        }
    });

    // 应用分组筛选
    if (groupFilter.value) {
        result = result.filter(item => item.class_id == groupFilter.value);
    }

    // 应用排序
    if (sortField.value) {
        result.sort((a, b) => {
        let modifier = sortDirection.value === 'asc' ? 1 : -1;
        let aValue = a[sortField.value];
        let bValue = b[sortField.value];
        
        // 处理空值
        if (aValue === null || aValue === undefined) aValue = '';
        if (bValue === null || bValue === undefined) bValue = '';
        
        // 处理数字排序
        if (typeof aValue === 'number' && typeof bValue === 'number') {
            return (aValue - bValue) * modifier;
        }
        
        // 默认字符串排序
        if (aValue.toString() < bValue.toString()) return -1 * modifier;
        if (aValue.toString() > bValue.toString()) return 1 * modifier;
        return 0;
        });
    }

    return result;
});

// 单元格右键点击事件
function onCellContextMenu(event) {
    // 阻止默认的右键菜单
    event.event.preventDefault();

    // 获取行数据
    const rowData = event.data;

    // 显示右键菜单
    contextMenu.visible = true;
    contextMenu.x = event.event.clientX;
    contextMenu.y = event.event.clientY;
    contextMenu.rowData = rowData;
}

// 处理数据格式
const processedData = computed(() => {
    const data = [];
    Object.entries(groupedMice.value).forEach(([groupName, groupArray]) => {
        groupArray.forEach(mouseData => {
            const mouse = mouseData.mouse_info;
            const rowData = {
                id: mouse.id,
                group: groupName,
                mouse_tid: mouse.tid, // 添加小鼠的tid用于后续操作
            };

            // 添加实验字段数据
            fieldDefinitions.value.forEach(field => {
                // 获取该小鼠该字段的值
                const value = getCellValue(mouse.tid, field.id);
                rowData[`field_${field.id}`] = value;
            });

            data.push(rowData);
        });
    });
    return data;
});

// 获取单元格值的方法
const getCellValue = (mouseTid, fieldId) => {
    // 从experimentData中查找该小鼠该字段的值
    const mouseData = experimentData.value.find(item => item.mouse_id === mouseTid);
    if (!mouseData) return null;
    
    // 根据字段定义获取正确的字段名
    const fieldDef = fieldDefinitions.value.find(f => f.id === fieldId);
    if (!fieldDef) return null;
    
    return mouseData[fieldDef.field_name] || null;
};

// 列定义
const columnDefs = computed(() => {
    const baseColumns = [
    {
        headerName: '小鼠ID',
        field: 'id',
        pinned: 'left',
        width: 150,
        checkboxSelection: true,
        headerCheckboxSelection: true,
        cellRenderer: 'agGroupCellRenderer',
    },
    { 
        headerName: '分组', 
        field: 'group',
        width: 120,
        rowGroup: true
    }
    ];

    // 动态添加实验字段列
    const fieldColumns = fieldDefinitions.value.map(field => ({
        headerName: field.field_name + (field.unit ? `(${field.unit})` : ''),
        field: `field_${field.id}`,
        editable: false, // 在数据列表页不可编辑
        width: 120,
        sortable: true, // 启用排序
        filter: true,   // 启用筛选
        cellStyle: { textAlign: field.data_type === 'INTEGER' || field.data_type === 'REAL' ? 'right' : 'left' },
        cellRenderer: (params) => {
            if (params.value === null || params.value === undefined) return '-';
            return params.value;
        }
    }));

    return [...baseColumns, ...fieldColumns];
});

// 默认列配置
const defaultColDef = {
    flex: 1,
    minWidth: 100,
    editable: true,
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: true,
};

// 初始化
const init = async () => {
try {
    // 获取实验类型信息
    const expResponse = await axios.get(`/api/experiment/${experimentId.value}`);
    experimentName.value = expResponse.data.name;

    fieldDefinitions.value = expResponse.data.fields;
    
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

function onGridReady(params) {
    gridApi.value = params.api;
    gridContext.gridApi = params.api;
    
    // 设置初始排序
    gridApi.value.applyColumnState({
        state: [{ colId: 'mouse_id', sort: 'asc' }],
        defaultState: { sort: null }
    });
    
    // 设置初始筛选
    gridApi.value.setFilterModel({
        'class_id': {
        filterType: 'set',
        values: ['对照组']
        }
    });
    
    // 自动调整列宽以适应内容
    gridApi.value.sizeColumnsToFit();
}

// 搜索变化处理
const onSearchChange = () => {
    if (gridApi.value) {
        gridApi.value.setQuickFilter(searchTerm.value);
    }
};

// 分组筛选变化处理
const onGroupFilterChange = () => {
    if (gridApi.value) {
        if (groupFilter.value) {
            gridApi.value.setFilterModel({
                'group': {
                    filterType: 'text',
                    type: 'equals',
                    filter: groupFilter.value
                }
            });
        } else {
            gridApi.value.setFilterModel(null);
        }
    }
};

// 排序变化处理
const onSortChanged = (event) => {
    console.log('排序已更改', event);
};

// 筛选变化处理
const onFilterChanged = (event) => {
    console.log('筛选已更改', event);
};

// 重置筛选
const resetFilters = () => {
    searchTerm.value = '';
    groupFilter.value = '';
    if (gridApi.value) {
        gridApi.value.setFilterModel(null);
        gridApi.value.setQuickFilter('');
    }
};

// 导出数据
const exportData = () => {
    if (gridApi.value) {
        gridApi.value.exportDataAsExcel({
            fileName: `${experimentName.value}_数据.xlsx`
        });
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
    availableGroups.value = Object.keys(groupedMice.value);
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

const toggleCandidateSelection = (tid) => {
    const index = selectedCandidates.value.indexOf(tid);
    if (index > -1) {
        selectedCandidates.splice(index, 1);
    } else {
        selectedCandidates.push(tid);
    }
};

// 拖拽开始
const onDragStart = (event, groupId) => {
    const ids = selectedCandidates.value.join(',');
    event.dataTransfer.setData('mouseIds', ids);
    event.dataTransfer.setData('groupId', groupId)
};

// 拖拽结束
const onDrop = (event, toGroupId) => {
    const mouseIds = event.dataTransfer.getData('mouseIds').split(',');
    const fromGroupId = event.dataTransfer.getData('groupId');
    
    mouseIds.forEach(id => {
        changeMouseGroup(id, toGroupId, fromGroupId);
    });
};

// 添加小鼠到分组
const changeMouseGroup = async (mouseId, groupId, newGroupId) => {
    try {
        await axios.post(`/api/experiment/${experimentId.value}/class_change`, {
            mouse_id: mouseId,
            class_id: groupId,
            class_new_id: newGroupId
        });
        
        // 更新本地数据
        await fetchCandidateMice();
        await fetchGroups();
    } catch (error) {
        console.error('添加小鼠到分组失败:', error);
        toast.error('添加小鼠到分组失败: ' + error.message);
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

// 清除所有分组
const clearSelection = async () => {
    selectedCandidates.value = [];
};

// 添加新分组
const addNewGroup = () => {
    if (availableGroups.value.length >= 5) {
        toast.error('最多只能添加5个分组');
        return;
    }
    availableGroups.value.push("新分组"+availableGroups.value.length.toString());
};

// 开始编辑分组名称
const startEditingGroup = (groupId) => {
    // 设置编辑状态和初始值
    editingGroups.value[groupId] = true;
    editingGroupNames.value[groupId] = groupId;

    // 下一个tick聚焦到输入框
    nextTick(() => {
        const input = groupNameInputs.value.find(el => el.dataset.groupId === groupId);
        if (input) {
        input.focus();
        input.select();
        }
    });
};

// 保存分组名称
const saveGroupName = async (oldGroupId) => {
    const newGroupId = editingGroupNames.value[oldGroupId].trim();

    // 验证新名称
    if (!newGroupId) {
        alert('分组名称不能为空');
        return;
    }

    if (newGroupId === oldGroupId) {
        // 名称未改变，直接取消编辑
        cancelEditingGroup(oldGroupId);
        return;
    }

    if (availableGroups.value.includes(newGroupId)) {
        alert('分组名称已存在，请使用其他名称');
        return;
    }

    try {
        // 调用API更新分组名称
        const response = await axios.put(`/api/experiment/${experimentId.value}/groups/${oldGroupId}`, {
        new_group_name: newGroupId
        });
        
        if (response.data.success) {
        // 更新本地状态
        groupedMice.value[newGroupId] = groupedMice.value[oldGroupId];
        delete groupedMice.value[oldGroupId];
        
        // 更新可用分组列表
        const index = availableGroups.value.indexOf(oldGroupId);
        if (index !== -1) {
            availableGroups.value.splice(index, 1, newGroupId);
        }
        
        // 退出编辑模式
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
};

// 取消编辑分组名称
const cancelEditingGroup = (groupId) => {
    editingGroups.value[groupId] = false;
    delete editingGroupNames.value[groupId];
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

// 记录表格列定义
const recordColumnDefs = computed(() => {
    const columns = [
        {
        headerName: '分组',
        field: 'group',
        rowGroup: true,
        hide: true,
        width: 120
        },
        {
        headerName: '小鼠ID',
        field: 'mouse_id',
        pinned: 'left',
        width: 120,
        editable: false,
        cellRenderer: 'agGroupCellRenderer',
        }
    ];

    // 添加实验字段列
    fieldDefinitions.value.forEach(field => {
        columns.push({
        headerName: `${field.field_name}${field.unit ? `(${field.unit})` : ''}${field.is_required ? '*' : ''}`,
        field: `field_${field.id}`,
        editable: true,
        width: 150,
        cellStyle: { textAlign: field.data_type === 'INTEGER' || field.data_type === 'REAL' ? 'right' : 'left' },
        cellRenderer: (params) => {
            if (params.value === null || params.value === undefined || params.value === '') return '-';
            return params.value;
        },
        cellEditor: field.data_type === 'BOOLEAN' ? 'agSelectCellEditor' : 'agTextCellEditor',
        cellEditorParams: field.data_type === 'BOOLEAN' ? {
            values: ['是', '否']
        } : {},
        valueFormatter: (params) => {
            if (params.value === null || params.value === undefined || params.value === '') return '';
            return params.value.toString();
        },
        valueParser: (params) => {
            if (params.newValue === '' || params.newValue === null || params.newValue === undefined) return null;
            
            try {
            switch (field.data_type) {
                case 'INTEGER':
                return parseInt(params.newValue);
                case 'REAL':
                return parseFloat(params.newValue);
                case 'BOOLEAN':
                return params.newValue === '是';
                case 'DATE':
                // 尝试解析日期
                const date = new Date(params.newValue);
                return isNaN(date.getTime()) ? params.newValue : date.toISOString().split('T')[0];
                default:
                return params.newValue;
            }
            } catch (e) {
            return params.newValue;
            }
        }
        });
    });

    // 添加备注列
    columns.push({
        headerName: '备注',
        field: 'notes',
        editable: true,
        width: 150
    });

    return columns;
});

// 记录表格默认列配置
const recordDefaultColDef = {
    flex: 1,
    minWidth: 100,
    resizable: true,
    filter: true,
    sortable: true,
};

// 初始化记录表格数据
const initRecordData = () => {
    const rowData = [];

    // 遍历分组和小鼠
    Object.entries(groupedMice.value).forEach(([groupName, group]) => {
        group.forEach(mouseData => {
        const mouse = mouseData.mouse_info;
        const row = {
            group: groupName,
            mouse_id: mouse.id,
            mouse_tid: mouse.tid,
            notes: ''
        };
        
        // 初始化字段值
        fieldDefinitions.value.forEach(field => {
            row[`field_${field.id}`] = null;
        });
        
        rowData.push(row);
        });
    });

    recordRowData.value = rowData;
};

// 记录表格就绪回调
const onRecordGridReady = (params) => {
    recordGridApi.value = params.api;

    // 自动展开所有分组
    setTimeout(() => {
        params.api.expandAll();
    }, 100);
};

// 单元格值改变事件
const onCellValueChanged = (params) => {
    // 可以在这里添加验证逻辑
    console.log('单元格值改变:', params);
};

// 保存实验记录
const saveExperimentRecord = async () => {
    try {
        if (!recordGridApi.value) {
            toast.error('表格未初始化');
            return;
        }
        
        // 获取所有行数据
        const allRows = [];
        recordGridApi.value.forEachNode(node => {
            if (!node.group) {
                allRows.push(node.data);
            }
        });
        
        // 验证必填字段
        for (const row of allRows) {
            for (const field of fieldDefinitions.value) {
                if (field.is_required && (row[`field_${field.id}`] === null || row[`field_${field.id}`] === undefined || row[`field_${field.id}`] === '')) {
                    toast.error(`小鼠 ${row.mouse_id} 的字段 ${field.field_name} 是必填的`);
                    return;
                }
            }
        }
        
        // 构建请求数据
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
        
        // 发送请求
        const response = await axios.post('/api/experiments', requestData);
        toast.success(response.data.message);
        
        // 关闭模态框
        showRecordModal.value = false;
        
        // 刷新数据
        await fetchData();
    } catch (error) {
        console.error('保存实验记录失败:', error);
        toast.error('保存失败: ' + (error.response?.data?.error || error.message));
    }
};

// 打开录入数据模态框
const openRecordModal = async () => {
    try {
        // 初始化表格数据
        initRecordData();
        
        // 显示模态框
        showRecordModal.value = true;
        
        // 确保表格正确渲染
        nextTick(() => {
        if (recordGridApi.value) {
            recordGridApi.value.refreshCells();
            recordGridApi.value.expandAll();
        }
        });
    } catch (error) {
        console.error('打开录入模态框失败:', error);
        toast.error('打开录入模态框失败: ' + error.message);
    }
};

// 关闭录入数据模态框
const closeRecordModal = async () => {
    showRecordModal.value = false;
};

// 获取排序图标
const sortIcon = (field) => {
if (sortField.value !== field) return 'material-icons inactive-icon';
return sortDirection.value === 'asc' 
    ? 'material-icons' 
    : 'material-icons rotated-icon';
};

// 表格排序
const sortTable = (field) => {
if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
} else {
    sortField.value = field;
    sortDirection.value = 'asc';
}
};

// 应用筛选
const applyFilters = () => {
// 筛选逻辑已在计算属性中处理
};


// 获取小鼠ID
const getMouseId = (mouseTid) => {
const mouse = lived_mice.value.find(m => m.tid === mouseTid);
return mouse ? mouse.id : `未知 (${mouseTid})`;
};

// 获取分组名称
const getGroupName = (classId) => {
if (!classId) return '未分组';
return `分组 ${groupLetters[classId-1]}`;
};

// 格式化字段值显示
const formatFieldValue = (item, field) => {
    const value = item[field.field_name];
    if (value === null || value === undefined) return '-';

    switch (field.data_type) {
        case 'BOOLEAN':
        return value ? '是' : '否';
        case 'DATE':
        return new Date(value).toLocaleDateString();
        default:
        return value.toString();
    }
};

// 编辑记录
const editRecord = (record) => {
    if (!contextMenu.rowData) return;
    // 实现编辑记录逻辑
    console.log('编辑记录:', record);
    // 可以打开一个编辑模态框，填充现有数据
    // 关闭菜单
    contextMenu.visible = false;
};

// 删除记录
const deleteRecord = async (record) => {
    if (!contextMenu.rowData) return;
    if (!confirm('确定要删除这条记录吗？')) return;
    try {
        await axios.delete(`/api/experiments/${record.id}`);
        toast.success('记录删除成功');
        await fetchData(); // 重新加载数据
    } catch (error) {
        console.error('删除记录失败:', error);
        toast.error('删除失败: ' + (error.response?.data?.error || error.message));
    }
    // 关闭菜单
    contextMenu.visible = false;
};

// 点击页面其他地方关闭菜单
document.addEventListener('click', () => {
    contextMenu.visible = false;
});

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

/* 数据表格样式 */
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

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  text-align: left;
  padding: 12px;
  border-bottom: 2px solid #e2e8f0;
  cursor: pointer;
  user-select: none;
}

.data-table th:hover {
  background: #f1f5f9;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.data-table tr:nth-child(even) {
  background-color: #f9fafc;
}

.data-table tr:hover {
  background-color: #f1f5ff;
}

.filter-row th {
  padding: 5px;
  background: #f1f5f9;
}

.filter-row input, .filter-row select {
  width: 100%;
  padding: 5px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 12px;
}

.actions {
  display: flex;
  gap: 5px;
}

.btn-icon {
  padding: 6px;
  border: none;
  border-radius: 4px;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background: #f1f5f9;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #ef4444;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #6c757d;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 10px;
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
</style>
