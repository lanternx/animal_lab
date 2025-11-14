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
    <div v-show="activeTab === 'visualization'" class="tab-content">
    <div class="action-buttons">
        <button class="btn btn-primary" @click="showGroupModal = true" :disabled="!allGroups.id">
        <i class="material-icons">group</i>
        修改分组
        </button>
        <button class="btn btn-primary" @click="generateChart">
        <i class="material-icons">bar_chart</i>
        生成图表
        </button>
    </div>
    <!-- 数据展示区域 -->
    <div v-if="hasData" class="chart-container" id="chart-container">
        <canvas id="experimentChart"></canvas>
    </div>
    </div>

    <!-- 数据列表标签页 -->
    <div v-show="activeTab === 'data'" class="tab-content">
    <div class="action-buttons">
        <button class="btn btn-primary" @click="openRecordModal">
        <i class="material-icons">note_add</i>
        录入数据
        </button>
        <button class="btn btn-success" @click="exportData">
        <i class="material-icons">download</i>
        导出数据
        </button>
    </div>
    
    <!-- 数据表格 -->
    <div class="data-table-container">
        <!-- 搜索和筛选控件 -->
        <div class="table-controls">
            <div class="search-controls">
                <input v-model="searchTerm" id="search-input" placeholder="搜索小鼠编号或数据..." @input="onSearchChange">
                <button @click="resetFilters" class="reset-btn">
                    <i class="material-icons">refresh</i>
                </button>
            </div>
        
            <!-- 列筛选 -->
            <div class="column-filters">
                <select v-model="groupFilter" id="group-filter" @change="onGroupFilterChange">
                    <option value="">所有分组</option>
                    <option v-for="group in groupNames" :key="group" :value="group">
                        {{ group }}
                    </option>
                </select>
            </div>
        </div>
        
        <!-- Tabulator 数据表格 -->
        <div ref="tabulatorRef" class="tabulator-table"></div>
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
            <div ref="recordTabulatorRef" class="tabulator-table" style="height: 300px;"></div>
            
            <div class="d-grid mt-3">
                <button class="btn btn-primary" @click="saveExperimentRecord">
                <i class="material-icons">save</i> 保存记录
                </button>
            </div>
        </div>
    </div>
    </div>

    <!-- ID分组 -->
    <div v-if="showGroupModal" class="modal-backdrop" @click.self="showGroupModal=false">
        <IdGroupingManager
            :candidate-mice="candidateMice"
            :editing-group="allGroups"
            :colors="colors"
            @update:editing-group="handleGroupUpdate"
            @save-group="saveGroup"
        />
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
import { Chart } from 'chart.js/auto';
import regression from 'regression';
import { useGeneStore, useExperimentStore } from '@/stores'
import { storeToRefs } from 'pinia'
import IdGroupingManager from '@/components/IdGroupingManager.vue'

const geneStore = useGeneStore()
const {mice} = storeToRefs(geneStore)
const {colors} = geneStore

const experimentStore = useExperimentStore()
const {experiments} = storeToRefs(experimentStore)
const {fetchPredefinedGroups} = experimentStore


//切换实验时
onBeforeRouteUpdate(async (to, from) => {
    if (currentRequestToken) {
        currentRequestToken.cancel('取消上一个请求');
    }
    experimentData.value = [];
    candidateMice.value = [];
    allGroups.value = {
        id: null,
        name: '',
        description: '',
        Gtype: '',
        experiment_id: null,
        rules: []
    }
    if (to.params.experimentId !== from.params.experimentId) {
        experimentId.value = to.params.experimentId;
        await init();
    }
});
let currentRequestToken = null;

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
const candidateMice = ref([])
const allGroups = ref({
    id: null,
    name: '',
    description: '',
    Gtype: '',
    experiment_id: null,
    rules: []
})

// 分组管理状态
const showGroupModal = ref(false);

// 数据列表状态
const searchTerm = ref('');
const groupFilter = ref('');
const tabulatorInstance = ref(null);
const tabulatorRef = ref(null);
const contextMenu = reactive({
rowData: null,
cell: null
});

// 录入数据状态
const showRecordModal = ref(false);
const recordDate = ref(new Date().toISOString().split('T')[0]);
const researcher = ref('');
const recordTabulatorRef = ref(null);
const recordTabulatorInstance = ref(null);
const recordRowData = ref([]);

const groupNames = computed(() => {
    return allGroups.value.rules.map(group => group.name)
})

var cellContextMenu = [
    {
        label: "编辑记录",
        action: (e, cell) => {
            if (!cell) {
                toast.error('未选中单元格');
                return;
            }
            cell.edit(true);
            cell.getTable().on("cellEdited", async function(){
                const rowData = cell.getRow().getData();
                const field = cell.getField();
                const value = cell.getValue();
                
                // 确定更新的是基本字段还是实验值字段
                let updateData = {};
                
                if (['researcher', 'notes'].includes(field)) {
                    // 更新基本字段
                    updateData[field] = value;
                } else {
                    updateData.value = {
                        field_definition_id: parseInt(field.split('_')[1]),
                        field_value: value
                    };
                }
                try {
                    await axios.patch(`/api/experiments/${rowData.__experimentId}`, updateData);
                    toast.success('记录更新成功');
                    await fetchData();
                } catch (error) {
                    console.error('更新记录失败:', error);
                    toast.error('更新失败: ' + (error.response?.data?.error || error.message));
                    // 恢复原始值
                    cell.restoreOldValue();
                }
            });
        }
    },
    {
        label: "删除记录",
        action: (e, cell) => {
            if (!cell) {
                toast.error('未选中单元格');
                return;
            }
            const rowData = cell.getRow().getData();
            contextMenu.rowData = {
                experimentId: rowData.__experimentId // 使用隐藏字段
            };
            deleteRecord();
        }
    }
]

const columnDefs = computed(() => {
    const baseColumns = [
        {
        title: '记录时间',
        field: 'field_date',
        width: 150,
        headerHozAlign: 'left',
        frozen: true,
        },
        { 
        title: '分组', 
        field: 'group',
        width: 120,
        frozen: true,
        },
        {
        title: '小鼠ID',
        field: 'id',
        width: 100,
        headerHozAlign: 'left',
        frozen: true,
        },
        // 隐藏实验记录ID列
        {
            field: "__experimentId",
            visible: false
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
        },
        contextMenu: cellContextMenu,
        editor: field.data_type === 'BOOLEAN' ? 'select' : 'input',
        editorParams: field.data_type === 'BOOLEAN' ? { values: ['是', '否'] } : {},
    }));

    const additionalColumns = [
        {
        title: '实验人员',
        field: 'researcher',
        width: 150,
        headerHozAlign: 'left',
        contextMenu: cellContextMenu,
        editor: 'input'
        },
        {
        title: '备注',
        field: 'notes',
        width: 200,
        headerHozAlign: 'left',
        contextMenu: cellContextMenu,
        editor: 'input'
        }
    ];

    return [...baseColumns, ...fieldColumns, ...additionalColumns];
});

const recordColumnDefs = computed(() => {
    const columns = [
        {
        title: '分组',
        field: 'group',
        width: 120,
        frozen: true,
        },
        {
        title: '小鼠ID',
        field: 'mouse_id',
        width: 120,
        frozen: true,
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

const fetchGroups = async () => {
try {
    const response = await axios.get(`/api/experiments/${experimentId.value}/grouped_mice`, {cancelToken: currentRequestToken.token});
    if (response.data.error) {
        toast.error("请在设置页面为本实验设置预设分组")
        return
    }
    allGroups.value = response.data;
} catch (error) {
    console.error('获取小鼠错误:', error);
    toast.error('获取小鼠错误: ' + error.message);
}
}

const handleGroupUpdate = (updatedGroup) => {
    Object.assign(allGroups, updatedGroup)
}

const saveGroup = async () => {
    if (allGroups.value.rules.some(group => !group.name)) {
        toast.info('请填写分组名称')
        return
    }
    try {
        await axios.put(`/api/groups/predefined/${allGroups.value.id}`, allGroups.value)
        toast.success('预设ID分组保存成功')
        fetchPredefinedGroups()
        showGroupModal.value = false
    } catch (error) {
        console.error('保存分组失败:', error)
        toast.error(error.response?.data?.error || '保存分组失败')
    }
}

// 生命周期钩子
onMounted(() => {
init();
});

// 监听器
watch(experimentData, (newData) => {
if (tabulatorInstance.value) {
    tabulatorInstance.value.setData(newData);
}
});

// 方法
async function init() {
currentRequestToken = axios.CancelToken.source();
try {
    const experiment = experiments.value.find(ex => ex.id === Number(experimentId.value))
    experimentName.value = experiment.name;
    fieldDefinitions.value = experiment.fields;

    await fetchCandidate();
    await fetchGroups();
    await fetchData();
    
    // 初始化 Tabulator
    initTabulator();

    generateChart()
} catch (error) {
    if (!axios.isCancel(error)) {
        console.error('初始化失败:', error);
        toast.error('初始化失败: ' + error.message);
    }
}
}

function initTabulator() {
if (!tabulatorRef.value) return;
if (tabulatorInstance.value) {
tabulatorInstance.value.destroy();
}
tabulatorInstance.value = new Tabulator(tabulatorRef.value, {
    data: experimentData.value,
    columns: columnDefs.value.map(col => ({
        ...col,
        editable: false, // 默认所有列不可编辑
        headerSort: true, // 启用表头排序
        sorter: "string" // 默认使用字符串排序
    })),
    layout: 'fitColumns',
    height: '85vh',
    selectable: true,
    selectableRange: true,
    clipboard: "copy",
    groupBy: 'group',
    groupHeader: (value, count) => {
        return `${value} <span style='color:#666;'>(${count} 条记录)</span>`;
    }
});
}

function initRecordTabulator() {
if (!recordTabulatorRef.value) return;
if (recordTabulatorInstance.value) {
recordTabulatorInstance.value.destroy();
}
recordTabulatorInstance.value = new Tabulator(recordTabulatorRef.value, {
    data: recordRowData.value,
    columns: recordColumnDefs.value,
    layout: 'fitColumns',
    height: '400px',
    selectableRange:1,
    selectableRangeColumns:true,
    selectableRangeRows:true,
    selectableRangeClearCells:true,
    editTriggerEvent:"dblclick",
    clipboard: true,
    clipboardCopyStyled:false,
    clipboardCopyConfig:{
        rowHeaders:false,
        columnHeaders:false,
    },
    clipboardCopyRowRange:"range",
    clipboardPasteParser:"range",
    clipboardPasteAction:"range",
    rowHeader:{resizable: false, frozen: true, width:40, hozAlign:"center", formatter: "rownum", cssClass:"range-header-col", editor:false},

    groupBy: 'group',
    groupHeader: (value, count) => {
        return `${value} <span style='color:#666;'>(${count} 条记录)</span>`;
    }
});
}

function onSearchChange() {
    if (tabulatorInstance.value) {
        // 多字段搜索 - 使用 OR 逻辑
        tabulatorInstance.value.setFilter("id",  "starts", searchTerm.value);
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

async function exportData () {
    if (tabulatorInstance.value) {
        const params = {
                experiment_ids: [experimentId.value],
                format: 'xlsx'
            };
        const response = await axios.get(`/api/export/experiment`, { 
            params,
            responseType: 'blob'
        })
        // 使用 PyWebview 的保存文件对话框
        if (window.pywebview && window.pywebview.api) {
            const filename = `experiment_export.xlsx`
            const arrayBuffer = await response.data.arrayBuffer()
            const uint8array = new Uint8Array(arrayBuffer)
            const dataArray = Array.from(uint8array)
            const state = await window.pywebview.api.save_file_dialog(dataArray, filename)
            if(state.success){
                toast.success(`导出成功，文件路径：${state.path}`)
            } else {
                toast.info(state.message || "导出失败")
            }
        } else {
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `experiment_export.xlsx`)
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            toast.success("导出成功")
        }
    }
}

async function fetchData() {
try {
    const response = await axios.get(`/api/experiment/${experimentId.value}/data`, {cancelToken: currentRequestToken.token});
    experimentData.value = response.data;
    hasData.value = experimentData.value.length > 0;
} catch (error) {
    console.error('获取数据:', error);
    toast.error('获取数据: ' + error.message);
}
}

async function fetchCandidate() {
try{
    const miceExperiment = await axios.get(`/api/experiments/${experimentId.value}/mice`)
    candidateMice.value = miceExperiment.data
} catch (error) {
    console.error('获取数据:', error);
    toast.error('获取数据: ' + error.message);
}
}

async function generateChart() {
    if (!hasData.value) {
        toast.error('暂无实验数据，无法生成图表');
        return;
    }
    // 清空图表容器
    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer) return;
    
    chartContainer.innerHTML = '';
    
    // 获取字段定义
    const xFields = fieldDefinitions.value.filter(f => f.visualize_type === 'x');
    const yFields = fieldDefinitions.value.filter(f => f.visualize_type === 'y');
    const columnFields = fieldDefinitions.value.filter(f => f.visualize_type === 'column');
    
    xFields.push({field_name: '日期', id: 'date', data_type: 'DATE'}); // 添加日期字段作为X轴选项
    // 如果没有可视化字段，提示用户
    if (xFields.length === 0 && yFields.length === 0 && columnFields.length === 0) {
        const noVizFields = document.createElement('div');
        noVizFields.className = 'no-data';
        noVizFields.innerHTML = `
        <i class="material-icons">bar_chart</i>
        <p>没有配置可视化字段，请在字段设置中指定x、y或column类型</p>
        `;
        chartContainer.appendChild(noVizFields);
        return;
    }

    // 处理数据分组
    const groupedData = {};
    experimentData.value.forEach(item => {
        const group = item.group;
        if (!groupedData[group]) {
        groupedData[group] = [];
        }
        groupedData[group].push(item);
    });
    
    // 创建X-Y图表（散点图/折线图）
    if (xFields.length > 0 && yFields.length > 0) {
        // 为每个X-Y组合创建图表
        xFields.forEach((xField, xIndex) => {
        yFields.forEach((yField, yIndex) => {
            const chartCard = document.createElement('div');
            chartCard.className = 'chart-card';
            
            const canvas = document.createElement('canvas');
            canvas.id = `chart-xy-${xField.id}-${yField.id}`;
            canvas.className = 'chart-canvas';
            canvas.width = 400;
            canvas.height = 350;
            canvas.style.backgroundColor = 'white';
            canvas.style.border = '1px solid #e0e0e0';
            canvas.style.borderRadius = '8px';
            canvas.style.padding = '15px';
            canvas.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            chartCard.appendChild(canvas);
            chartContainer.appendChild(chartCard);
            
            createXYChart(canvas, xField, yField, groupedData);
        });
        });
    }

    // 创建柱状图
    if (columnFields.length > 0) {
    columnFields.forEach((columnField, colIndex) => {
        const chartCard = document.createElement('div');
        chartCard.className = 'chart-card';
        
        const canvas = document.createElement('canvas');
        canvas.id = `chart-column-${columnField.id}`;
        canvas.className = 'chart-canvas';
        canvas.width = 300;
        canvas.height = 350;
        canvas.style.backgroundColor = 'white';
        canvas.style.border = '1px solid #e0e0e0';
        canvas.style.borderRadius = '8px';
        canvas.style.padding = '15px';
        canvas.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        chartCard.appendChild(canvas);
        chartContainer.appendChild(chartCard);
        
        createBoxPlotWithPoints(canvas, columnField, groupedData); // 使用新函数
    });
    }

    // 如果只有Y字段，创建箱线图+散点图
    if (xFields.length === 0 && yFields.length > 0 && columnFields.length === 0) {
    yFields.forEach((columnField, colIndex) => {
        const chartCard = document.createElement('div');
        chartCard.className = 'chart-card';
        
        const canvas = document.createElement('canvas');
        canvas.id = `chart-column-${columnField.id}`;
        canvas.className = 'chart-canvas';
        canvas.width = 300;
        canvas.height = 350;
        canvas.style.backgroundColor = 'white';
        canvas.style.border = '1px solid #e0e0e0';
        canvas.style.borderRadius = '8px';
        canvas.style.padding = '15px';
        canvas.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        chartCard.appendChild(canvas);
        chartContainer.appendChild(chartCard);
        
        createBoxPlotWithPoints(canvas, columnField, groupedData); // 使用新函数
    });
    }

    // 如果只有X字段，创建频率分布图
    if (xFields.length > 0 && yFields.length === 0 && columnFields.length === 0) {
        xFields.forEach((xField, xIndex) => {
        const chartCard = document.createElement('div');
        chartCard.className = 'chart-card';
        
        const canvas = document.createElement('canvas');
        canvas.id = `chart-dist-${xField.id}`;
        canvas.className = 'chart-canvas';
        canvas.width = 300;
        canvas.height = 350;
        canvas.style.backgroundColor = 'white';
        canvas.style.border = '1px solid #e0e0e0';
        canvas.style.borderRadius = '8px';
        canvas.style.padding = '15px';
        canvas.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        chartCard.appendChild(canvas);
        chartContainer.appendChild(chartCard);
        
        createDistributionChart(canvas, xField, groupedData);
        });
    }
}

function createXYChart(canvas, xField, yField, groupedData) {
    const ctx = canvas.getContext('2d');

    // 准备数据集
    const datasets = [];
    // 检查x字段是否为日期类型
    const isDateField = xField.data_type === 'DATE';
    let globalMin = Infinity;
    let globalMax = -Infinity;
    let globalXMin = Infinity;
    let globalXMax = -Infinity;

    let firstDayTimestamp = Infinity;
    // 计算第一天的时间戳
    if (isDateField) {
        firstDayTimestamp = Math.min(...Object.values(groupedData).flatMap(group => 
            group.map(item => {
                const xValue = item[`field_${xField.id}`];
                if (xValue) {
                    if (typeof xValue === 'string') return new Date(xValue).getTime();
                    if (xValue instanceof Date) return xValue.getTime();
                }
                return Infinity;
            }).filter(ts => !isNaN(ts))
        ));
    }
        
    Object.keys(groupedData).forEach((groupName, index) => {
        const groupData = groupedData[groupName];
        const color = groupData[0]?.color;
        const data = [];

        groupData.forEach(item => {
            const xValue = item[`field_${xField.id}`];
            const yValue = item[`field_${yField.id}`];
            
            // 如果是日期字段，将日期字符串转换为时间戳
            if (isDateField && xValue) {
                let timestamp = null;
                // 处理日期格式，确保它能被正确解析
                if (typeof xValue === 'string') {
                    timestamp = new Date(xValue).getTime();
                } else if (xValue instanceof Date) {
                    timestamp = xValue.getTime();
                }
                if (timestamp && !isNaN(timestamp) && yValue !== null && !isNaN(yValue)) {
                    const daysSinceStart = Math.floor((timestamp - firstDayTimestamp) / (1000 * 60 * 60 * 24));
                    data.push({
                        x: daysSinceStart,
                        y: parseFloat(yValue)
                    });
                }
            } else {
                if (xValue !== null && yValue !== null && !isNaN(xValue) && !isNaN(yValue)) {
                    data.push({
                    x: parseFloat(xValue),
                    y: parseFloat(yValue)
                    });
                }
            }
        });
        
        // 按x值排序
        data.sort((a, b) => a.x - b.x);
        
        datasets.push({
            label: groupName,
            data: data,
            borderColor: color,
            backgroundColor: color+ '80',
            pointBackgroundColor: color,
            tension: 0.1,
            pointRadius: 5,
            pointHoverRadius: 7,
            showLine: false
        });

        // 计算LOESS平滑线和置信区间（需要至少6个点）
        if (data.length >= 6) {
            try {
                const mappedData = data.map(d => [d.x, d.y]);
                const result = regression.polynomial(mappedData, { order: 3, precision: 4 });
                const fitPoints = [];
                const xMin = Math.min(...mappedData.map(p => p[0]));
                const xMax = Math.max(...mappedData.map(p => p[0]));
                const pointCount = 200; // 趋势线点数
                for (let i = 0; i < pointCount; i++) {
                    const x = xMin + (xMax - xMin) * i / (pointCount - 1);
                    const y = result.predict(x)[1];
                    fitPoints.push({ x, y });
                }
                datasets.push({
                    label: `${groupName}趋势线`,
                    data: fitPoints,
                    borderColor: color,
                    backgroundColor: 'rgba(0,0,0,0)',
                    pointRadius: 0,
                    borderWidth: 2,
                    showLine: true,
                    tension: 0.1,
                    type: 'line'
                });
            } catch (e) {
                console.error(`计算失败: ${e.message}`);
            }
        }

        globalMin = Math.min(globalMin, ...data.map(d => d.y));
        globalMax = Math.max(globalMax, ...data.map(d => d.y));
        globalXMin = Math.min(globalXMin, ...data.map(d => d.x));
        globalXMax = Math.max(globalXMax, ...data.map(d => d.x));
    });

    // 如果全局最小值和最大值仍然是Infinity，则设置为0
    if (globalMin === Infinity) globalMin = 0;
    if (globalMax === -Infinity) globalMax = 1;
    if (globalXMin === Infinity) globalXMin = 0;
    if (globalXMax === -Infinity) globalXMax = 1;
    
    // 计算y轴的范围，留出一些边距
    const padding = (globalMax - globalMin) * 0.1;
    const yMin = globalMin - padding;
    const yMax = globalMax + padding;
    const xPadding = (globalXMax - globalXMin) * 0.1;
    let xMin = globalXMin - xPadding;
    let xMax = globalXMax + xPadding;

    if (xMin === xMax) {
        // 如果所有x值相同，设置一个默认范围
        xMin -= 1;
        xMax += 1;
    }

    // 创建图表
    new Chart(ctx, {
        type: 'scatter',
        data: {
        datasets: datasets
        },
        options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                min: isDateField ? Math.floor(xMin) : xMin,
                max: isDateField ? Math.ceil(xMax) : xMax,
                title: {
                    display: true,
                    text: isDateField ? "距离开始的天数" : `${xField.field_name}${xField.unit ? ` (${xField.unit})` : ''}`
                },
                ticks: {
                    // 对于日期字段，强制显示整数刻度
                    callback: function(value) {
                        if (isDateField) {
                            return Math.round(value); // 四舍五入到最接近的整数
                        }
                        return typeof value === 'number' ? value.toFixed(3) : value;
                    },
                    stepSize: isDateField ? 1 : undefined // 对于日期字段，设置步长为1
                }
            }
            ,
            y: {
            min: yMin,
            max: yMax,
            title: {
                display: true,
                text: `${yField.field_name}${yField.unit ? ` (${yField.unit})` : ''}`
            }
            }
        },
        plugins: {
            title: {
            display: true,
            text: `${xField.field_name} vs ${yField.field_name}`,
            font: {
                size: 16
            }
            },
            tooltip: {
            callbacks: {
                label: function(context) {
                    return `${context.dataset.label}: (${context.parsed.x}, ${context.parsed.y})`;
                }
            }
            }
        }
        }
    });
}

// 创建箱线图+散点图函数
function createBoxPlotWithPoints(canvas, columnField, groupedData) {
  const ctx = canvas.getContext('2d');
  
  // 准备数据
  const groupNames = Object.keys(groupedData);
  const groupColors = {};
  groupNames.forEach(gname => {
    groupColors[gname] = groupedData[gname][0]?.color;
  });
  
  const scatterDatasets = [];  // 改为存储多个散点图数据集
  const boxPlotStats = [];
  let globalMin = Infinity;
  let globalMax = -Infinity;

  // 为每个分组计算统计数据并创建散点图数据集
  groupNames.forEach((groupName, groupIndex) => {
    const groupItems = groupedData[groupName];
    const groupColor = groupColors[groupName];

    // 获取该分组所有小鼠在该字段上的值
    const values = groupItems
      .map(item => {
        const value = parseFloat(item[`field_${columnField.id}`]);
        return isNaN(value) ? null : value;
      })
      .filter(val => val !== null);
    
    if (values.length > 0) {
      // 排序以便计算分位数
      values.sort((a, b) => a - b);
      
      // 计算五数概括
      const min = values[0];
      const q1 = calculateQuartile(values, 0.25);
      const median = calculateMedian(values);
      const q3 = calculateQuartile(values, 0.75);
      const max = values[values.length - 1];
      
      boxPlotStats.push({ min, q1, median, q3, max });
      
      // 为每个分组创建单独的散点图数据集
      const scatterData = values.map((value, index) => {
        // 为散点添加一些随机偏移，避免重叠
        const xOffset = (Math.random() - 0.5) * 0.2;
        return {
          x: groupIndex + xOffset,
          y: value
        };
      });
      
      scatterDatasets.push({
        type: 'scatter',
        label: groupName,  // 使用分组名称作为标签
        data: scatterData,
        backgroundColor: groupColor + 'AA',  // 使用分组颜色
        borderColor: '#FFFFFF',
        borderWidth: 1,
        pointRadius: 4,
        pointHoverRadius: 6
      });
      
    } else {
      boxPlotStats.push({ min: 0, q1: 0, median: 0, q3: 0, max: 0 });
      // 即使没有数据也添加一个空的数据集以保持图例一致
      scatterDatasets.push({
        type: 'scatter',
        label: groupName,
        data: [],
        backgroundColor: groupColor + 'AA',
        borderColor: '#FFFFFF',
        borderWidth: 1,
        pointRadius: 4,
        pointHoverRadius: 6
      });
    }

    if (values.length > 0) {
      globalMin = Math.min(globalMin, ...values);
      globalMax = Math.max(globalMax, ...values);
    }
  });

  // 如果全局最小值和最大值仍然是Infinity，则设置为0
  if (globalMin === Infinity) globalMin = 0;
  if (globalMax === -Infinity) globalMax = 1;
  
  // 计算y轴的范围，留出一些边距
  const padding = (globalMax - globalMin) * 0.1;
  const yMin = globalMin - padding;
  const yMax = globalMax + padding;
  
  // 创建组合图表
  new Chart(ctx, {
    data: {
      labels: groupNames,
      datasets: scatterDatasets  // 使用多个散点图数据集
    },
    // ... 其余配置保持不变
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: false,
          min: yMin,
          max: yMax,
          title: {
            display: true,
            text: `${columnField.field_name}${columnField.unit ? ` (${columnField.unit})` : ''}`
          }
        },
        x: {
          title: {
            display: true,
            text: '分组'
          },
          min: -0.5,
          max: groupNames.length - 0.5,
          ticks: {
            callback: function(value, index, values) {
              return groupNames[value] || '';
            }
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: `${columnField.field_name}的分布（箱线图+散点图）`,
          font: {
            size: 16
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              // 现在可以根据datasetIndex获取对应的分组名称
              const groupName = scatterDatasets[context.datasetIndex]?.label || '未知分组';
              return `${groupName}: ${context.parsed.y.toFixed(2)}`;
            }
          }
        }
      },
        legend: {
          position: 'top'
        }
    },
        plugins: [{
      // 自定义插件绘制箱线图
      afterDraw: function(chart) {
        const ctx = chart.ctx;
        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        
        // 绘制每个分组的箱线图
        groupNames.forEach((groupName, groupIndex) => {
          const stats = boxPlotStats[groupIndex];
          if (!stats) return;
          
          const xCenter = xAxis.getPixelForValue(groupIndex);
          const boxWidth = 20;
          const whiskerWidth = 10;
          
          // 设置颜色
          ctx.strokeStyle = groupColors[groupName];
          ctx.fillStyle = groupColors[groupName] + '40'; // 半透明填充
          ctx.lineWidth = 1.5;
          
          // 绘制箱体 (Q1到Q3)
          const boxTop = yAxis.getPixelForValue(stats.q3);
          const boxBottom = yAxis.getPixelForValue(stats.q1);
          const boxHeight = boxBottom - boxTop;
          
          ctx.fillRect(xCenter - boxWidth/2, boxTop, boxWidth, boxHeight);
          ctx.strokeRect(xCenter - boxWidth/2, boxTop, boxWidth, boxHeight);
          
          // 绘制中位数线
          const medianY = yAxis.getPixelForValue(stats.median);
          ctx.beginPath();
          ctx.moveTo(xCenter - boxWidth/2, medianY);
          ctx.lineTo(xCenter + boxWidth/2, medianY);
          ctx.strokeStyle = groupColors[groupName];
          ctx.lineWidth = 2;
          ctx.stroke();
          
          // 绘制须线
          const minY = yAxis.getPixelForValue(stats.min);
          const maxY = yAxis.getPixelForValue(stats.max);
          
          // 上须线
          ctx.beginPath();
          ctx.moveTo(xCenter, boxTop);
          ctx.lineTo(xCenter, minY);
          ctx.stroke();
          
          // 下须线
          ctx.beginPath();
          ctx.moveTo(xCenter, boxBottom);
          ctx.lineTo(xCenter, maxY);
          ctx.stroke();
          
          // 绘制须线端点
          // 上端点
          ctx.beginPath();
          ctx.moveTo(xCenter - whiskerWidth/2, minY);
          ctx.lineTo(xCenter + whiskerWidth/2, minY);
          ctx.stroke();
          
          // 下端点
          ctx.beginPath();
          ctx.moveTo(xCenter - whiskerWidth/2, maxY);
          ctx.lineTo(xCenter + whiskerWidth/2, maxY);
          ctx.stroke();
        });
      }
    }]
  });
}

// 计算中位数的辅助函数
function calculateMedian(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  } else {
    return sorted[mid];
  }
}

// 计算四分位数的辅助函数
function calculateQuartile(values, quartile) {
  const sorted = [...values].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * quartile;
  const base = Math.floor(pos);
  const rest = pos - base;
  
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  } else {
    return sorted[base];
  }
}

function createDistributionChart(canvas, xField, groupedData) {
    const ctx = canvas.getContext('2d');

    // 准备数据集
    const datasets = [];
    let allValues = {};
    const fieldKey = `field_${xField.id}`;

    // 检查x字段是否为日期类型
    let firstDayTimestamp = Infinity;
    const isDateField = xField.data_type === 'DATE';
    if (isDateField) {
        firstDayTimestamp = Math.min(...Object.values(groupedData).flatMap(group => 
        group.map(item => {
            const xValue = item[fieldKey];
            if (xValue) {
                if (typeof xValue === 'string') return new Date(xValue).getTime();
                if (xValue instanceof Date) return xValue.getTime();
            }
            return Infinity;
        }).filter(ts => !isNaN(ts))
        ));
    }

    let globalMax = -Infinity;
    let globalMin = Infinity;

    for (const [groupName, groupData] of Object.entries(groupedData)){
        const values = [];
        
        for (const item of groupData) {
            const rawValue = item[fieldKey];
            if (rawValue == null) continue;
            let timestamp = null;
            if (typeof rawValue === 'string') {
                timestamp = new Date(rawValue).getTime();
            } else if (rawValue instanceof Date) {
                timestamp = rawValue.getTime();
            }
            const numValue = isDateField
            ? Math.floor((timestamp - firstDayTimestamp) / (1000 * 60 * 60 * 24))
            : parseFloat(rawValue);
            
            if (!isNaN(numValue)) values.push(numValue);
        }
        globalMax = Math.max(globalMax, ...values);
        globalMin = Math.min(globalMin, ...values);
        allValues[groupName] = values;
    }

    const range = globalMax - globalMin;
    const bandwidth = 1; // 固定带宽为1

    // 高斯核函数
    const gaussianKernel = u => Math.exp(-u * u / 2) / Math.sqrt(2 * Math.PI);

    // 为每个分组创建核密度估计
    for (const [index, [groupName, values]] of Object.entries(Object.entries(allValues))) {
        if (values.length === 0) {
            datasets.push({ label: groupName, data: [] });
            return;
        }
        
        // 创建200个均匀分布的点
        const n = 200;
        const step = range / n;
        const points = [];
        const color = groupedData[groupName][0]?.color;
        
        for (let i = 0; i <= n; i++) {
            const x = globalMin + i * step;
            let sum = 0;
            
            for (const v of values) {
                const u = (x - v) / bandwidth;
                sum += gaussianKernel(u);
            }
            
            const density = sum / (values.length * bandwidth);
            points.push({ x, y: density });
        }
        
        datasets.push({
            label: groupName,
            data: points,
            borderColor: color,
            backgroundColor: color + '40',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.3,
            fill: true
        });
    };
    // 创建图表
    new Chart(ctx, {
        type: 'line',
        data: {
        datasets: datasets
        },
        options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
            type: 'linear',
            title: {
                display: true,
                text: isDateField ? "距离开始的天数" : `${xField.field_name}${xField.unit ? ` (${xField.unit})` : ''}`
            },
            min: isDateField ? Math.floor(globalMin) : globalMin,
            max: isDateField ? Math.ceil(globalMax) : globalMax,
            },
            y: {
            title: {
                display: true,
                text: '概率密度'
            }
            }
        },
        plugins: {
            title: {
            display: true,
            text: `${xField.field_name}的频率分布`,
            font: {
                size: 16
            }
            }
        }
        }
    });
}

function initRecordData() {
    const rowData = [];

    allGroups.value.rules.forEach(group => {
        group.mouseId.forEach(mTid => {
        const row = {
            group: group.name,
            mouse_id: mice.value.find(m => m.tid === mTid).id,
            mouse_tid: mTid,
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

async function deleteRecord() {
    if (!contextMenu.rowData?.experimentId) return;
    if (!confirm('确定要删除这条记录吗？')) return;
    try {
        await axios.delete(`/api/experiments/${contextMenu.rowData.experimentId}`);
        toast.success('记录删除成功');
        await fetchData();
    } catch (error) {
        console.error('删除记录失败:', error);
        toast.error('删除失败: ' + (error.response?.data?.error || error.message));
    }
}

async function saveExperimentRecord() {
try {
    if (!recordTabulatorInstance.value) {
    toast.error('表格未初始化');
    return;
    }
    
    const allRows = recordTabulatorInstance.value.getData();
    
    if (recordDate.value === '') {
        toast.error('请填写记录日期');
        return;
    }

    let records = [];
    for (const row of allRows) {
        let values = {};
        let is_valid = true;
        let is_integrated = true;
        let lack_field = '';
        for (const field of fieldDefinitions.value) {
            if (field.is_required && (row[`field_${field.id}`] === null || row[`field_${field.id}`] === undefined || row[`field_${field.id}`] === '')) {
                is_valid = false;
                lack_field = field.field_name;
                break;
            }
            values[field.id] = row[`field_${field.id}`];
        }
        if (!is_valid) {
            for (const field of fieldDefinitions.value) {
                if (field.is_required && values[field.id]) {
                    is_integrated = false;
                }
            }
            if (!is_integrated) {
                toast.error(`小鼠 ${row.mouse_id} 的字段 ${lack_field} 是必填的`);
                return;
            } else {
                continue; // 跳过未填写的行
            }
        }
        records.push({
            mouse_id: row.mouse_tid,
            researcher: researcher.value,
            date: recordDate.value,
            notes: row.notes,
            values: values
        });
    }
    
    const requestData = {
        experiment_type_id: experimentId.value,
        records: records
    };
    
    const response = await axios.post('/api/experiments', requestData);
    toast.success(response.data.message);
    
    showRecordModal.value = false;
    await fetchData();
    generateChart()
} catch (error) {
    console.error('保存实验记录失败:', error);
    toast.error('保存失败: ' + (error.response?.data?.error || error.message));
}
}
</script>

<style scoped>
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

.chart-container {
display: grid;
grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  justify-content: center;
  align-items: start;
  padding: 20px;
  overflow-y: auto;
  height: 90%;
  width: 90%;
  min-height: 500px;
}

.chart-canvas {
width: 300px;
height: 400px;
border: 1px solid #e0e0e0;
border-radius: 8px;
padding: 15px;
background: white;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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

.modal-body {
padding: 1.5rem;
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
flex-direction: column;
flex: 1;
display: flex;
max-width: 95%;
}

.data-table-container {
background: white;
border-radius: 8px;
padding: 20px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
max-width: 95%;
max-height: 90%;
overflow: auto;
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

.column-filters select {
padding: 8px 12px;
border: 1px solid #dcdfe6;
border-radius: 4px;
background: white;
}

.tabulator-table {
background: white;
border-radius: 8px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chart-card {
  flex: 0 0 calc(50% - 20px);
  margin-bottom: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 15px;
  width: 330px; /* 400px + 左右padding */
  height: 430px; /* 最小宽度 */
}

@media (max-width: 1024px) {
  .chart-card {
    flex: 0 0 100%;
    min-width: auto;
  }
}

.mouse-group-manager {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 20px;
}
</style>