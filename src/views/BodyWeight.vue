<template>
<div class="main-content">
    <div class="content-header">
    <h1 class="page-title">小鼠体重管理</h1>
    </div>
    
    <div class="card">
    <div class="card-header">
        <h5 class="mb-0">体重趋势分析</h5>
    </div>
    <div class="card-body">
        <!-- 控制按钮区域 -->
        <div class="d-flex justify-content-between mb-4">
        <div>
            <button class="btn btn-primary me-2" @click="showChart">
            <i class="material-icons">insights</i>
            生成图表
            </button>
        </div>
        <div>
            <button class="btn btn-primary" @click="openRecordModal">
            <i class="material-icons btn-icon">add</i>
            录入体重
            </button>
        </div>
        <div>
            <button id="addGroupBtn" class="btn btn-sm btn-outline" @click="addGroup">
            <i class="material-icons">add</i> 添加分组
            </button>
        </div>
        </div>
        
            <!-- 分组设置 -->
        <div class="mb-4">
            <h5>分组设置</h5>
            <div class="groups-container">
            <div 
                v-for="(group, index) in groups" 
                :key="index" 
                class="group-card"
            >
                <div class="card">
                <div class="card-header compact-header">
                    <span>分组 {{ groupLetters[index] }}</span>
                    <button @click="removeGroup(index)">
                        <i class="material-icons">close</i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="mb-2">
                    <label class="form-label">性别</label>
                    <div class="d-flex flex-wrap">
                        <div class="form-check me-3">
                        <input 
                            class="form-check-input" 
                            type="checkbox" 
                            v-model="group.sex.M" 
                            :id="'group'+index+'SexM'"
                        >
                        <label class="form-check-label" :for="'group'+index+'SexM'">雄性</label>
                        </div>
                        <div class="form-check">
                        <input 
                            class="form-check-input" 
                            type="checkbox" 
                            v-model="group.sex.F" 
                            :id="'group'+index+'SexF'"
                        >
                        <label class="form-check-label" :for="'group'+index+'SexF'">雌性</label>
                        </div>
                    </div>
                    </div>
                    <div class="mb-2">
                        <div class="form-group">
                            <label class="form-label">基因型</label>
                            <select class="form-select" v-model="group.genotype" multiple>
                                <option v-for="genotype in allGenotypes" 
                                        :key="genotype.id"
                                        :value="genotype.name"
                                        class="option-item"
                                        :class="{ selected: group.genotype.includes(genotype.name) }">
                                    {{ genotype.name }}
                                </option>
                            </select>
                        </div>
                    </div>
                </div>
                </div>
            </div>
            
            <div 
                v-if="groups.length < 5" 
                class="group-card add-card"
                @click="addGroup"
            >
                <i class="material-icons">add</i>
                <span>添加分组</span>
            </div>
            </div>
        </div>
        
        <!-- 图表控制选项 -->
        <div class="chart-controls" v-if="hasData">
            <div class="control-group">
                <span class="control-label">平均线计算方式</span>
                <div>
                    <div class="form-check">
                        <input type="radio" id="monthlyAverage" v-model="averageMethod" value="monthly" class="form-check-input">
                        <label for="monthlyAverage" class="form-check-label">按月平均</label>
                    </div>
                    <div class="form-check">
                        <input type="radio" id="weeklyAverage" v-model="averageMethod" value="weekly" class="form-check-input">
                        <label for="weeklyAverage" class="form-check-label">按周平均</label>
                    </div>
                    <div class="form-check">
                        <input type="radio" id="dailyAverage" v-model="averageMethod" value="daily" class="form-check-input">
                        <label for="dailyAverage" class="form-check-label">按天平均</label>
                    </div>
                </div>
            </div>
            
            <div class="control-group">
                <span class="control-label">趋势线拟合</span>
                <div>
                    <div class="form-check">
                        <input type="checkbox" id="showTrendLine" v-model="showTrendLine" class="form-check-input">
                        <label for="showTrendLine" class="form-check-label">显示趋势线</label>
                    </div>
                </div>
            </div>
            
            <div class="control-group">
                <span class="control-label">置信区间</span>
                <div>
                    <div class="form-check">
                        <input type="checkbox" id="showConfidenceBand" v-model="showConfidenceBand" class="form-check-input">
                        <label for="showConfidenceBand" class="form-check-label">显示置信区间</label>
                    </div>
                </div>
            </div>

            <div class="control-group">
                <span class="control-label">散点图</span>
                <div>
                    <div class="form-check">
                        <input type="checkbox" id="showDot" v-model="showDot" class="form-check-input">
                        <label for="showDot" class="form-check-label">显示散点</label>
                    </div>
                </div>
            </div>
        </div>
            
        <!-- 图表容器 -->
        <div v-if="hasData" class="chart-area">
            <div class="chart-container">
                <canvas id="weightChart"></canvas>
            </div>
        </div>
            <!-- 无数据提示 -->
        <div v-else class="text-center py-5">
            <div class="mb-3">
                <i class="material-icons" style="font-size: 3rem; color: #6c757d;">bar_chart</i>
            </div>
            <h5 class="text-muted">请设置分组条件并点击"生成图表"按钮</h5>
        </div>
    </div>
    </div>
    
    <!-- 录入模态框 -->
    <div v-if="showModal">
        <div class="dialog-container">
            <div class="modal-header">
            <h5 class="modal-title">批量录入体重信息</h5>
            <button type="button" class="btn-close" @click="closeModal">
                <i class="material-icons">close</i>
            </button>
            </div>
            <div class="modal-body">
            <div class="form-group">
                <label for="recordDate" class="form-label">记录日期</label>
                <input type="date" class="form-control" id="recordDate" v-model="recordDate">
            </div>
            
            <div class="input-table">
                <div class="table-wrapper">
                <table class="table">
                    <thead>
                    <tr>
                        <th style="width: 20px;">
                        <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
                        </th>
                        <th>区域</th>
                        <th>笼位</th>
                        <th>小鼠ID</th>
                        <th>基因型</th>
                        <th>性别</th>
                        <th>体重 (g)</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr 
                        v-for="(mouse, index) in lived_mice" 
                        :key="mouse.id"
                        :class="{ 'selected-row': selectedRows[index] }"
                    >
                        <td>
                        <input type="checkbox" v-model="selectedRows[index]">
                        </td>
                        <td>{{ mouse.section }}</td>
                        <td>{{ mouse.cage_name }}</td>
                        <td>{{ mouse.id }}</td>
                        <td>{{ mouse.genotype }}</td>
                        <td>{{ mouse.sex }}</td>
                        <td>
                        <input 
                            type="number" 
                            step="0.01" 
                            class="form-control weight-input" 
                            placeholder="输入体重"
                            v-model="weightValues[mouse.tid]"
                            :tabindex="index + 1"
                            @keydown.tab.prevent="handleTab(index)"
                        >
                        </td>
                    </tr>
                    </tbody>
                </table>
                </div>
            </div>
            
            <div class="d-grid mt-3">
                <button id="saveBtn" class="btn btn-primary" @click="saveWeightRecords">
                <i class="material-icons">save</i> 保存所有记录
                </button>
            </div>
            </div>
        </div>
        <div class="modal-backdrop" @click.self="closeModal"></div>
    </div>
</div>
</template>

<script>
import { ref, nextTick, onMounted, watch } from 'vue';
import axios from 'axios';
import Chart from 'chart.js/auto';
import regression from 'regression';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

export default {
name: 'BodyWeight',
setup() {
    // 小鼠数据
    const lived_mice = ref([]);
    // 体重输入值
    const weightValues = ref({});
    // 选中的行
    const selectedRows = ref([]);
    const selectAll = ref(false);
    // 模态框控制
    const showModal = ref(false);
    const recordDate = ref(new Date().toISOString().split('T')[0]);
    const allGenotypes = ref([]);
    
    // 分组数据
    const groups = ref([{ sex: { M: true, F: true }, genotype: [] }]);
    const groupLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
    
    // 图表选项
    const averageMethod = ref('weekly');
    const showTrendLine = ref(false);
    const showConfidenceBand = ref(false);
    const showDot = ref(true);
    
    // 图表实例
    const hasData = ref(false);
    let weightChart = null;
    
    // 体重记录数据
    const weightRecords = ref([]);

    // 初始化方法
    const init = async () => {
    try {
        // 获取小鼠数据
        const response = await axios.get('/api/lived_mice');
        lived_mice.value = response.data;
        const genotypeResponse = await axios.get('/api/genotypes');
        allGenotypes.value = genotypeResponse.data;
        // 初始化选中状态数组
        selectedRows.value = new Array(lived_mice.value.length).fill(false);
        
        // 获取体重记录
        const recordsResponse = await axios.get('/api/weight');
        weightRecords.value = recordsResponse.data;
    } catch (error) {
        console.error('获取小鼠数据失败:', error);
    }
    };

    // 打开录入模态框
    const openRecordModal = () => {
    showModal.value = true;
    nextTick(() => {
        // 自动聚焦到第一个输入框
        const firstInput = document.querySelector('.weight-input');
        if (firstInput) firstInput.focus();
    });
    };

    // 关闭模态框
    const closeModal = () => {
    showModal.value = false;
    };

    // 处理Tab键
    const handleTab = (index) => {
    const inputs = document.querySelectorAll('.weight-input');
    if (index < inputs.length - 1) {
        inputs[index + 1].focus();
    }
    };

    // 全选/取消全选
    const toggleSelectAll = () => {
    selectedRows.value = selectedRows.value.map(() => selectAll.value);
    };

    // 保存体重记录
    const saveWeightRecords = async () => {
    try {
        const records = [];
        
        lived_mice.value.forEach((mouse) => {
        const weight = weightValues.value[mouse.tid];
        // 只添加有有效体重值的记录
        if (weight && weight > 0) {
            records.push({
            mouse_id: mouse.tid,
            weight: parseFloat(weight),
            record_date: recordDate.value
            });
        }
        });
        
        if (records.length === 0) {
        toast.error('请至少填写一条有效的记录');
        return;
        }
        
        // 发送批量请求
        await axios.post('/api/weight', { records });
        toast.success(`成功保存 ${records.length} 条记录！`);
        weightValues.value = {};
        showModal.value = false;
        
        // 重新获取体重记录
        const recordsResponse = await axios.get('/api/weight');
        weightRecords.value = recordsResponse.data;
    } catch (error) {
        console.error('保存体重记录失败:', error);
        toast.error('保存失败: ' + (error.response?.data?.error || error.message));
    }
    };
    
    // 添加分组
    const addGroup = () => {
        if (groups.value.length >= 8) {
            toast.info('最多只能添加8个分组');
            return;
        }
        groups.value.push({ sex: { M: true, F: true }, genotype: [] });
    };

    // 移除分组
    const removeGroup = (index) => {
    if (groups.value.length > 1) {
        groups.value.splice(index, 1);
    }
    };

    const showChart = async () => {
    if (groups.value.length === 0) {
        toast.error('请至少添加一个分组');
        return;
    }
    
    try {
        // 获取小鼠数据
        const miceRes = await axios.get('/api/mice');
        const allMiceData = miceRes.data;
        
        if (weightRecords.value.length === 0) {
            toast.error('没有可用的体重记录数据');
            return;
        }
        
        hasData.value = true;
        await nextTick();
        generateChart(weightRecords.value, allMiceData);
    } catch (error) {
        console.error('生成图表失败:', error);
        toast.error('生成图表失败: ' + error.message);
    }
    };

    // 生成图表
    const generateChart = (records, allMiceData) => {
    try {
        const ctx = document.getElementById('weightChart');
        if (!ctx) {
            console.error('图表容器未找到');
            return;
        }
        
        // 销毁现有图表
        if (weightChart) {
            weightChart.destroy();
        }
        
        const datasets = [];
        const colors = ['#F27970', '#BB9727', '#54B345', '#32B897', '#05B9E2', '#8983BF', '#C76DA2', "#743027"];
        
        // 处理数据
        groups.value.forEach((group, groupIndex) => {
            const groupName = `分组 ${groupLetters[groupIndex]}`;
            const color = colors[groupIndex % colors.length];
            
            // 筛选符合分组条件的小鼠
            const groupMice = allMiceData.filter(mouse => {
                const sexMatch = mouse.sex === 'M' ? group.sex.M : group.sex.F;
                const genotypeMatch = group.genotype.length === 0 || group.genotype.includes(mouse.genotype);
                return sexMatch && genotypeMatch;
            });
            
            if (groupMice.length === 0){
                toast.error("所选组别无小鼠！");
            }
            
            // 获取这些小鼠的体重记录
            const groupRecords = records.filter(record => 
                groupMice.some(mouse => mouse.tid === record.mouse_id)
            );
            
            if (groupRecords.length === 0){
                toast.error("所选组别无数据！");
            }
            // 1. 散点图数据集（显示所有数据点）
            const scatterData = [];
            
            groupRecords.forEach(record => {
                const mouse = allMiceData.find(m => m.tid === record.mouse_id);
                scatterData.push({
                    x: record.record_livingdays,
                    y: record.weight,
                    mouseId: mouse.id
                });
            });
            
            // 添加散点图数据集
            datasets.push({
                label: `${groupName} - 数据点`,
                data: scatterData,
                borderColor: color,
                backgroundColor: `${color}80`, // 半透明
                pointRadius: 4,
                pointHoverRadius: 6,
                showLine: false,
                type: 'scatter'
            });
            
            // 2. 平均线数据集
            const lineData = [];
            
            if (averageMethod.value === 'weekly') {
                // 按周计算平均值
                const weeklyAverages = {};
                
                // 按周分组数据
                groupRecords.forEach(record => {
                    const week = Math.floor(record.record_livingdays / 7);
                    if (!weeklyAverages[week]) {
                        weeklyAverages[week] = { total: 0, count: 0 };
                    }
                    weeklyAverages[week].total += record.weight;
                    weeklyAverages[week].count += 1;
                });
                
                // 计算每周平均值
                for (const week in weeklyAverages) {
                    const avg = weeklyAverages[week].total / weeklyAverages[week].count;
                    lineData.push({
                        x: parseInt(week) * 7 + 3.5, // 周中的天数（中间点）
                        y: parseFloat(avg.toFixed(2))
                    });
                }
                
                // 按周数排序
                lineData.sort((a, b) => a.x - b.x);
            }
            else if (averageMethod.value === 'monthly') {
                // 按月计算平均值
                const monthlyAverages = {};
                
                // 按月分组数据
                groupRecords.forEach(record => {
                    const month = Math.floor(record.record_livingdays / 30);
                    if (!monthlyAverages[month]) {
                        monthlyAverages[month] = { total: 0, count: 0 };
                    }
                    monthlyAverages[month].total += record.weight;
                    monthlyAverages[month].count += 1;
                });
                
                // 计算每月平均值
                for (const month in monthlyAverages) {
                    const avg = monthlyAverages[month].total / monthlyAverages[month].count;
                    lineData.push({
                        x: parseInt(month) * 30 + 15, // 周中的天数（中间点）
                        y: parseFloat(avg.toFixed(2))
                    });
                }
                
                // 按月数排序
                lineData.sort((a, b) => a.x - b.x);
            } 
            else {
                // 按天计算平均值
                const dailyAverages = {};
                
                // 按天分组数据
                groupRecords.forEach(record => {
                    const day = record.record_livingdays;
                    if (!dailyAverages[day]) {
                        dailyAverages[day] = { total: 0, count: 0 };
                    }
                    dailyAverages[day].total += record.weight;
                    dailyAverages[day].count += 1;
                });
                
                // 计算每天平均值
                for (const day in dailyAverages) {
                    const avg = dailyAverages[day].total / dailyAverages[day].count;
                    lineData.push({
                        x: parseInt(day),
                        y: parseFloat(avg.toFixed(2))
                    });
                }
                
                // 按天数排序
                lineData.sort((a, b) => a.x - b.x);
            }
            
            // 添加平均线数据集
            datasets.push({
                label: `${groupName} - 平均线`,
                data: lineData,
                borderColor: color,
                backgroundColor: 'transparent',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 6,
                fill: false,
                tension: 0.3,
                type: 'line'
            });
            
            // 3. 趋势线（如果启用）
            if (showTrendLine.value && lineData.length >= 2) {
                // 准备回归分析数据
                const regressionData = lineData.map(point => [point.x, point.y]);
                
                // 使用线性回归
                const result = regression.linear(regressionData);
                const gradient = result.equation[0];
                const intercept = result.equation[1];
                const r2 = result.r2;
                
                // 计算趋势线的起点和终点
                const firstX = lineData[0].x;
                const lastX = lineData[lineData.length - 1].x;
                
                const trendData = [
                    { x: firstX, y: gradient * firstX + intercept },
                    { x: lastX, y: gradient * lastX + intercept }
                ];
                
                // 添加趋势线数据集
                datasets.push({
                    label: `${groupName} - 趋势线 (R²=${r2.toFixed(3)})`,
                    data: trendData,
                    borderColor: color,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    borderDash: [5, 5],
                    type: 'line'
                });
            }
            
            // 4. 置信区间（如果启用）
            if (showConfidenceBand.value && averageMethod.value === 'weekly' && lineData.length >= 2) {
                // 计算每周的标准差和置信区间
                const weeklyStats = {};
                
                // 按周分组数据
                groupRecords.forEach(record => {
                    const week = Math.floor(record.record_livingdays / 7);
                    if (!weeklyStats[week]) {
                        weeklyStats[week] = { values: [] };
                    }
                    weeklyStats[week].values.push(record.weight);
                });
                
                // 计算置信区间
                const confidenceDataUpper = [];
                const confidenceDataLower = [];
                
                for (const week in weeklyStats) {
                    const values = weeklyStats[week].values;
                    const mean = values.reduce((a, b) => a + b, 0) / values.length;
                    const stdDev = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / values.length);
                    
                    // 95% 置信区间
                    const margin = 1.96 * stdDev / Math.sqrt(values.length);
                    
                    confidenceDataUpper.push({
                        x: parseInt(week) * 7 + 3.5,
                        y: mean + margin
                    });
                    
                    confidenceDataLower.push({
                        x: parseInt(week) * 7 + 3.5,
                        y: mean - margin
                    });
                }
                
                // 按周数排序
                confidenceDataUpper.sort((a, b) => a.x - b.x);
                confidenceDataLower.sort((a, b) => a.x - b.x);
                
                // 添加置信区间数据集
                datasets.push({
                    label: `${groupName} - 95% 置信区间`,
                    data: confidenceDataUpper,
                    borderColor: 'transparent',
                    backgroundColor: `${color}20`,
                    pointRadius: 0,
                    fill: '+1',
                    type: 'line',
                    showLine: false
                });
                
                datasets.push({
                    label: `${groupName} - 置信区间下界`,
                    data: confidenceDataLower,
                    borderColor: 'transparent',
                    backgroundColor: `${color}20`,
                    pointRadius: 0,
                    fill: false,
                    type: 'line',
                    showLine: false
                });
            } else if (showConfidenceBand.value && averageMethod.value === 'monthly' && lineData.length >= 2){
                // 计算每月的标准差和置信区间
                const monthlyStats = {};
                
                // 按月分组数据
                groupRecords.forEach(record => {
                    const month = Math.floor(record.record_livingdays / 30);
                    if (!monthlyStats[month]) {
                        monthlyStats[month] = { values: [] };
                    }
                    monthlyStats[month].values.push(record.weight);
                });
                
                // 计算置信区间
                const confidenceDataUpper = [];
                const confidenceDataLower = [];
                
                for (const month in monthlyStats) {
                    const values = monthlyStats[month].values;
                    const mean = values.reduce((a, b) => a + b, 0) / values.length;
                    const stdDev = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / values.length);
                    
                    // 95% 置信区间
                    const margin = 1.96 * stdDev / Math.sqrt(values.length);
                    
                    confidenceDataUpper.push({
                        x: parseInt(month) * 30 + 15,
                        y: mean + margin
                    });
                    
                    confidenceDataLower.push({
                        x: parseInt(month) * 30 + 15,
                        y: mean - margin
                    });
                }
                
                // 按月数排序
                confidenceDataUpper.sort((a, b) => a.x - b.x);
                confidenceDataLower.sort((a, b) => a.x - b.x);
                
                // 添加置信区间数据集
                datasets.push({
                    label: `${groupName} - 95% 置信区间`,
                    data: confidenceDataUpper,
                    borderColor: 'transparent',
                    backgroundColor: `${color}20`,
                    pointRadius: 0,
                    fill: '+1',
                    type: 'line',
                    showLine: false
                });
                
                datasets.push({
                    label: `${groupName} - 置信区间下界`,
                    data: confidenceDataLower,
                    borderColor: 'transparent',
                    backgroundColor: `${color}20`,
                    pointRadius: 0,
                    fill: false,
                    type: 'line',
                    showLine: false
                });
            }
        });
        
        // 创建图表
        weightChart = new Chart(ctx, {
            type: 'scatter',
            data: { 
                datasets: datasets.filter(d => {
                        // 根据 showDot 决定是否包含散点数据集
                        if (d.label.includes('数据点')) {
                            return showDot.value; // 只返回 true 时包含散点
                        }
                        return true; // 其他数据集始终显示
                    }
                )
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            filter: item => !item.text.includes('数据点') && 
                                   !item.text.includes('置信区间下界')
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const dataset = context.dataset;
                                const point = context.raw;
                                
                                if (dataset.label.includes('数据点')) {
                                    return `小鼠 ${point.mouseId}: ${point.y}g`;
                                }
                                return `${dataset.label}: ${point.y}g`;
                            },
                            title: (context) => {
                                const point = context[0].raw;
                                if (averageMethod.value === 'weekly') {
                                    const week = Math.floor(point.x / 7);
                                    return `第${week + 1}周 (${week*7}-${week*7+6}天)`;
                                } else if (averageMethod.value === 'monthly') {
                                    const month = Math.floor(point.x / 30);
                                    return `第${month + 1}月 (${month*30}-${month*30+29}天)`;
                                }
                                return `生存天数: ${point.x}天`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: '体重 (g)'
                        },
                        beginAtZero: false
                    },
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: () => {
                                if (averageMethod.value === 'weekly') {
                                    return `生存周数`;
                                } else if (averageMethod.value === 'monthly') {
                                    return `生存月数`;
                                }
                                return `生存天数(天)`;
                            }
                        },
                        ticks: {
                            stepSize: 7,
                            callback: function(value) {
                                if (averageMethod.value === 'weekly') {
                                    const week = Math.floor(value / 7);
                                    return week >= 0 ? `第${week+1}周` : value;
                                } else if (averageMethod.value === 'monthly') {
                                    const month = Math.floor(value / 30);
                                    return month >= 0 ? `第${month+1}月` : value;
                                }
                                return value;
                            }
                        }
                    }
                }
            }
        });

        } catch (error) {
            console.error('生成图表失败:', error);
        }
    };

    // 监听图表选项变化
    watch([averageMethod, showTrendLine, showConfidenceBand, showDot], () => {
        if (hasData.value) {
            showChart();
        }
    });

    // 组件挂载时初始化
    onMounted(() => {
        init();
    });

    return {
    lived_mice,
    weightValues,
    selectedRows,
    selectAll,
    showModal,
    recordDate,
    groups,
    groupLetters,
    allGenotypes,
    hasData,
    averageMethod,
    showTrendLine,
    showConfidenceBand,
    showDot,
    openRecordModal,
    closeModal,
    handleTab,
    toggleSelectAll,
    addGroup,
    removeGroup,
    saveWeightRecords,
    showChart
    };
}
};
</script>

<style scoped>
/* 使用与dashboard一致的卡片样式 */
.card {
margin-bottom: 1.5rem;
border-radius: 8px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
background-color: white;
overflow: hidden;
}

.card-header {
padding: 1rem;
background-color: #f8f9fa;
border-bottom: 1px solid #dee2e6;
font-weight: 600;
}

.card-body {
padding: 1.5rem;
}

.content-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 20px;
}

.page-title {
font-size: 1.5rem;
font-weight: 600;
margin: 0;
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
transition: all 0.2s;
}

.btn-card {
padding: 4px 8px;
border: none;
cursor: pointer;
display: flex;
align-items: center;
font-size: 1px;
transition: all 0.2s;
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

.btn-sm {
padding: 6px 12px;
font-size: 0.875rem;
}

.btn-icon {
margin-right: 5px;
}

.btn-danger {
background-color: var(--danger);
color: white;
}

.form-group {
margin-bottom: 1rem;
}

.form-label {
display: block;
margin-bottom: 0.5rem;
font-weight: 500;
}

.form-control {
display: block;
width: 100%;
padding: 0.5rem;
font-size: 1rem;
line-height: 1.5;
color: #495057;
background-color: #fff;
border: 1px solid #ced4da;
border-radius: 4px;
transition: border-color 0.15s;
}

.form-select {
display: block;
width: 100%;
padding: 0.5rem;
font-size: 1rem;
background-color: #fff;
border: 1px solid #ced4da;
border-radius: 4px;
height: auto;
}

.dialog-container {
position: fixed;
top: 50%;
left: 50%;
transform: translate(-50%, -50%);
z-index: 1001; /* 高于遮罩层 */
background-color: white;
border-radius: 8px;
width: 90%;
max-width: 800px;
max-height: 90vh;
overflow: auto;
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
padding: 1rem;
background-color: var(--primary);
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

.input-table {
margin-top: 1rem;
}

.table-wrapper {
overflow-x: auto;
}

.table {
width: 100%;
border-collapse: collapse;
margin-bottom: 1rem;
}

.table th, 
.table td {
padding: 0.75rem;
border: 1px solid #dee2e6;
text-align: left;
}

.table th {
background-color: #f8f9fa;
font-weight: 600;
}

.table tbody tr:hover {
background-color: #f5f7fa;
}

.weight-input {
width: 100%;
padding: 0.5rem;
border: 1px solid #ced4da;
border-radius: 4px;
font-size: 1rem;
}

.selected-row {
background-color: #e6f7ff;
}

.d-grid {
display: grid;
}

.mt-3 {
margin-top: 1rem;
}

.chart-container {
position: relative;
height: 400px;
width: 100%;
}

.d-flex {
display: flex;
}

.justify-content-between {
justify-content: space-between;
}

.justify-content-end {
justify-content: flex-end;
}

.mb-4 {
margin-bottom: 1.5rem;
}

.me-2 {
margin-right: 0.5rem;
}

/* 图表控制区域 */
.chart-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 30px;
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
}

.control-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.control-label {
    font-weight: 500;
    font-size: 14px;
}

/* 响应式调整 */
@media (max-width: 992px) {
.content-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
}

.chart-container {
    height: 300px;
}
}

@media (max-width: 768px) {
    .chart-controls {
        flex-direction: column;
    }
}

/* 添加分组容器样式 */
.groups-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 每行最多四个 */
  gap: 15px;
  margin-bottom: 20px;
}

/* 分组卡片样式 */
.group-card {
  width: 200px;
  height: 210px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.group-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 10px rgba(0,0,0,0.1);
}

/* 添加分组卡片样式 */
.add-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  border: 1px dashed #ced4da;
  cursor: pointer;
}

.add-card:hover {
  background-color: #e9ecef;
  border-color: #adb5bd;
}

.add-card i {
  font-size: 2rem;
  margin-bottom: 8px;
  color: #6c757d;
}

.add-card span {
  font-weight: 500;
  color: #495057;
}

/* 卡片内部调整 */
.group-card .card {
  height: 100%;
  margin: 0;
}

.group-card .card-header {
  padding: 8px;
  font-size: 0.9rem;
}

.group-card .card-body {
  padding: 10px;
  height: calc(100% - 40px); /* 减去头部高度 */
  overflow-y: auto;
}

.group-card .form-label {
  font-size: 0.8rem;
  margin-bottom: 4px;
}

.group-card .form-select {
  font-size: 0.8rem;
  height: 80px;
}

.group-card .form-check {
  font-size: 0.8rem;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .groups-container {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  }
  
  .group-card {
    width: 130px;
    height: 130px;
  }
}

@media (max-width: 576px) {
  .groups-container {
    grid-template-columns: repeat(2, 1fr); /* 小屏幕每行两个 */
  }
}

.modal-backdrop {
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background-color: rgba(0, 0, 0, 0.5);
display: flex;
justify-content: center;
align-items: center;
z-index: 950;
}

.compact-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0.5rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-size: 0.85rem;
  font-weight: 600;
}

.compact-header button {
  background: none;
  border: none;
  padding: 0;
  color: #6c757d;
  cursor: pointer;
  font-size: 0.9rem;
}

.compact-header button:hover {
  color: #dc3545;
}

.text-center {
  text-align: center;
}

.text-muted {
  color: #6c757d;
}

.option-item {
    cursor: pointer;
    transition: all 0.2s ease;
    /* 自动换行设置 */
    white-space: normal;
    word-wrap: break-word;
}

/* 斑马纹效果 - 行间色差 */
.option-item:nth-child(odd) {
    background-color: #ffffff;
}

.option-item:nth-child(even) {
    background-color: #f8f9fa;
}

.option-item:hover {
    background-color: #e3f2fd;
}

.option-item.selected {
    background-color: #3498db;
    color: white;
}
</style>