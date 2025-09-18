<template>
<div class="main-content">
<!-- 背景遮罩（主模态） -->
<div class="modal-overlay" @click.self="closeMainModal"></div>

<!-- 主内容区 -->
<div class="mouse-detail-modal">
    <div class="page-header">
    <button class="back-button" @click="closeMainModal">
        <i class="material-icons">arrow_back</i>
        返回
    </button>
    <!-- 添加返回上一只按钮 -->
    <button 
        v-if="prevMouseId"
        class="back-button" 
        @click="navigateToMouse(prevMouseId)"
    >
        <i class="material-icons">replay</i>
        返回上一只
    </button>
    <h2>小鼠详情 #{{ mouseData.id }}</h2>
    </div>

    <div class="detail-grid">
    <div class="grid-item basic-info">
        <div class="card">
        <h3 class="card-title">小鼠基本信息</h3>
        <div class="info-content">
            <div class="info-row">
            <span class="info-label">ID:</span>
            <span class="info-value">{{ mouseData.id }}</span>
            </div>
            <div class="info-row">
            <span class="info-label">基因型:</span>
            <span class="info-value">{{ mouseData.genotype }}</span>
            </div>
            <div class="info-row">
            <span class="info-label">性别:</span>
            <span class="info-value">{{ mouseData.sex }}</span>
            </div>
            <div class="info-row">
            <span class="info-label">动物房位置:</span>
            <span class="info-value">{{ mouseData.cage_section || '未分配' }}</span>
            </div>
            <div class="info-row">
            <span class="info-label">笼位:</span>
            <span class="info-value">{{ mouseData.cage_id || '未分配' }}</span>
            </div>
        </div>
        </div>
    </div>

    <div class="grid-item status-records">
        <div class="card">
        <h3 class="card-title">状态记录</h3>
        <button 
            v-if="!showAddRecordForm" 
            class="add-record-button" 
            @click.stop="openAddRecordForm">
            <i class="material-icons">add</i>
            添加记录
        </button>

        <!-- 添加记录表单（内联显示） -->
        <div v-else class="add-record-form">
            <div class="form-group">
                <label>记录日期</label>
                <input type="date" v-model="newRecord.record_date">
            </div>
            <div class="form-group">
                <label>详细描述</label>
                <textarea 
                    v-model="newRecord.status" 
                    placeholder="输入详细描述..."
                    rows="2"
                ></textarea>
            </div>
            <div class="form-buttons">
            <button class="btn btn-outline" @click="cancelAddRecord">取消</button>
            <button class="btn btn-primary" @click="saveNewRecord">保存</button>
            </div>
        </div>

        <div class="status-content">
            <div v-if="mouseData.status_records && mouseData.status_records.length" class="status-list">
            <div v-for="record in mouseData.status_records" :key="record.id" class="status-item" :class="{ 'deleting': deletingRecordId === record.id }" @click="setDeletingRecord(record)">
                <div class="status-date">{{ record.record_livingdays }}天时</div>
                <div class="status-description">{{ record.status }}</div>
            </div>
            </div>
            <div v-else-if="!showAddRecordForm" class="no-data">
                <i class="material-icons">info</i>
                <p>暂无状态记录</p>
            </div>
        </div>
        </div>
    </div>

    <div class="grid-item pedigree">
        <div class="card">
        <h3 class="card-title">谱系图</h3>
        <!-- SVG 容器（D3 绘图） -->
        <div ref="pedigreeChart" class="chart-container svg-container"></div>
        </div>
    </div>

    <div class="grid-item weight-chart">
        <div class="card">
        <h3 class="card-title">体重变化图</h3>
        <!-- 为 Chart.js 提供固定高度的父容器，canvas 放在内部 -->
        <div class="chart-container canvas-wrapper">
            <canvas ref="weightChart"></canvas>
        </div>
        </div>
    </div>
    </div>
</div>
</div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'
import { Chart, registerables } from 'chart.js'
import { toast } from 'vue3-toastify';

Chart.register(...registerables)

export default {
name: 'MouseDetailModal',
props: {
    mouseId: { type: String, required: true }
},
setup(props, { emit }) {
    const prevMouseId = ref(null);

    const closeMainModal = () => { emit('close') }

    // state refs
    const mouseData = ref({})
    const weightChart = ref(null)
    const pedigreeChart = ref(null)

    // chart / d3 refs
    let chartInstance = null
    const simulationRef = ref(null)
    let resizeObserver = null
    let resizeTimer = null

    const currentMouseID = ref(props.mouseId)

    // 监听props.mouseId变化
    watch(currentMouseID, (newId) => {
        if (newId) {
            fetchMouseData();
        }
    });

    // fetch data
    const fetchMouseData = async () => {
    try {
        const response = await fetch(`/api/mice/${currentMouseID.value}`)
        if (!response.ok) throw new Error('获取数据失败')
        mouseData.value = await response.json()
        // 渲染图表在 DOM 更新后进行
        await nextTick()
        renderWeightChart()
        renderPedigreeChart()
    } catch (error) {
        console.error('获取小鼠数据失败:', error)
    }
    }

    // ========== 状态记录相关 ==========
    const deletingRecordId = ref(null)
    let clickTimer = null
    const setDeletingRecord = (record) => {
    if (deletingRecordId.value === record.id) {
        deleteRecord(record)
        return
    }
    if (clickTimer) { clearTimeout(clickTimer); clickTimer = null }
    deletingRecordId.value = record.id
    clickTimer = setTimeout(() => { deletingRecordId.value = null }, 1000)
    }

    const deleteRecord = async (record) => {
    try {
        const response = await fetch(`/api/status_records/${record.id}`, { method: 'DELETE' })
        if (response.ok) {
        const index = mouseData.value.status_records.findIndex(r => r.id === record.id)
        if (index !== -1) mouseData.value.status_records.splice(index, 1)
        console.log('记录删除成功')
        } else {
        console.error('删除记录失败')
        }
    } catch (error) {
        console.error('删除记录时出错:', error)
    } finally {
        deletingRecordId.value = null
    }
    }

    // 添加记录表单状态
    const showAddRecordForm = ref(false)
    const newRecord = ref({ record_date: null, status: '' }) 
    
    const openAddRecordForm = () => {
        // 设置默认日期为今天
        const today = new Date()
        const formattedDate = today.toISOString().split('T')[0]
        newRecord.value = { record_date: formattedDate, status: '' }
        showAddRecordForm.value = true
    }
    
    const cancelAddRecord = () => {
        showAddRecordForm.value = false
    }

    const saveNewRecord = async () => {
    try {
        const recordToSave = { ...newRecord.value, mouse_tid: currentMouseID.value, birth_date: mouseData.value.birth_date }
        await fetch(`/api/status_records`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(recordToSave)
        })
        showAddRecordForm.value = false
        toast.success('状态记录已添加')
        // 刷新数据
        await fetchMouseData()
    } catch (error) {
        console.error('添加记录失败:', error)
        toast.error('添加记录失败，请重试')
    }
    }
    
    const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN')
    }

    // ========== Chart.js 渲染（体重图） ==========
    const renderWeightChart = () => {
    if (!weightChart.value || !mouseData.value.weight_records) return
    const weightRecords = Array.isArray(mouseData.value.weight_records) ? mouseData.value.weight_records : []
    if (weightRecords.length === 0) {
        // 若无数据，销毁实例并返回（保持 canvas 空白）
        if (chartInstance) { chartInstance.destroy(); chartInstance = null }
        return
    }

    const dataPoints = weightRecords.map(record => ({ x: record.record_livingdays, y: record.weight }))

    // 如果已经有实例，更新数据即可，避免 destroy -> create 循环
    if (chartInstance) {
        chartInstance.data.datasets[0].data = dataPoints
        chartInstance.update()
        return
    }

    // 首次创建 Chart 实例（使用 canvas context）
    const ctx = weightChart.value.getContext('2d')
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
        datasets: [{
            label: '体重 (g)',
            data: dataPoints,
            borderColor: '#4285f4',
            backgroundColor: 'rgba(66, 133, 244, 0.1)',
            tension: 0.3,
            fill: true,
            pointBackgroundColor: '#4285f4',
            pointBorderColor: '#fff',
            pointRadius: 4,
            pointHoverRadius: 6
        }]
        },
        options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { mode: 'index', intersect: false }
        },
        scales: {
            x: {
            type: 'linear', // 关键：x 轴为线性数值轴（天数）
            title: { display: true, text: '天数' },
            grid: { color: 'rgba(0,0,0,0.05)' }
            },
            y: {
            beginAtZero: false,
            title: { display: true, text: '体重 (g)' },
            grid: { color: 'rgba(0,0,0,0.05)' }
            }
        }
        }
    })
    }

    const fetchMouseInfo = async (mouseId) => {
    try {
        const response = await fetch(`/api/mice/${mouseId}/brief`);
        return await response.json();
    } catch (error) {
        console.error('获取小鼠信息失败:', error);
        return { id: mouseId, genotype: '未知', sex: '未知' };
    }
    };

const renderPedigreeChart = async () => {
  if (!pedigreeChart.value || !mouseData.value.pedigree) return

  // 清除旧内容
  d3.select(pedigreeChart.value).selectAll('*').remove()

  // 停止旧的 simulation
  if (simulationRef.value) {
    try { simulationRef.value.stop() } catch (e) { /* ignore */ }
    simulationRef.value = null
  }

  const pedigree = mouseData.value.pedigree || {};
  const width = pedigreeChart.value.clientWidth || 400
  const height = pedigreeChart.value.clientHeight || 220

  const svg = d3.select(pedigreeChart.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height])
    .attr('preserveAspectRatio', 'xMidYMid meet')

  // 添加箭头标记
  const defs = svg.append('defs');

  // 父代到当前小鼠的箭头
  defs.append('marker')
    .attr('id', 'arrow-father')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#ccc');

  // 当前小鼠到后代的箭头
  defs.append('marker')
    .attr('id', 'arrow-offspring')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#999');

  // 创建节点数组
  const nodes = []
  const links = []
  
  // 创建当前小鼠节点
  const currentNode = {
    id: currentMouseID.value,
    name: `#${mouseData.value.id}`,
    type: 'current',
    birth_date: mouseData.value.birth_date,
    genotype: mouseData.value.genotype,
    sex: mouseData.value.sex,
    // 设置初始位置为中心
    x: width / 2,
    y: height / 2,
    fixed: true // 固定当前节点位置
  }
  nodes.push(currentNode)

  // 创建异步任务数组
  const nodePromises = []

  // 处理父代
  if (pedigree.father_id && pedigree.father_id.length) {
    for (const id of pedigree.father_id) {
      nodePromises.push(
        fetchMouseInfo(id).then(father => {
          const fatherNode = {
            id,
            name: `#${father.id}`,
            birth_date: father.birth_date,
            type: 'father',
            genotype: father.genotype,
            sex: father.sex,
            // 设置父代初始位置在左侧
            x: width / 4,
            y: height / 2 - (pedigree.father_id.length > 1 ? 30 : 0)
          }
          nodes.push(fatherNode)
          links.push({
            source: fatherNode,
            target: currentNode,
            type: 'father'
          })
          return fatherNode
        }).catch(error => {
          console.error(`获取父代小鼠 ${id} 失败:`, error)
          const fallbackNode = {
            id,
            name: `#${id}`,
            birth_date: '未知',
            type: 'father',
            genotype: '未知',
            sex: '未知',
            x: width / 4,
            y: height / 2 - (pedigree.father_id.length > 1 ? 30 : 0)
          }
          nodes.push(fallbackNode)
          links.push({
            source: fallbackNode,
            target: currentNode,
            type: 'father'
          })
          return fallbackNode
        })
      )
    }
  }
  
  // 处理母代
  if (pedigree.mother_id && pedigree.mother_id.length) {
    for (const id of pedigree.mother_id) {
      nodePromises.push(
        fetchMouseInfo(id).then(mother => {
          const motherNode = {
            id,
            name: `#${mother.id}`,
            birth_date: mother.birth_date,
            type: 'mother',
            genotype: mother.genotype,
            sex: mother.sex,
            // 设置母代初始位置在左侧
            x: width / 4,
            y: height / 2 + (pedigree.mother_id.length > 1 ? 30 : 0)
          }
          nodes.push(motherNode)
          links.push({
            source: motherNode,
            target: currentNode,
            type: 'mother'
          })
          return motherNode
        }).catch(error => {
          console.error(`获取母代小鼠 ${id} 失败:`, error)
          const fallbackNode = {
            id,
            name: `#${id}`,
            birth_date: '未知',
            type: 'mother',
            genotype: '未知',
            sex: '未知',
            x: width / 4,
            y: height / 2 + (pedigree.mother_id.length > 1 ? 30 : 0)
          }
          nodes.push(fallbackNode)
          links.push({
            source: fallbackNode,
            target: currentNode,
            type: 'mother'
          })
          return fallbackNode
        })
      )
    }
  }
  
  // 处理后代
  if (pedigree.offspring && pedigree.offspring.length) {
    for (const [index, id] of pedigree.offspring.entries()) {
      nodePromises.push(
        fetchMouseInfo(id).then(offspring => {
          const offspringNode = {
            id,
            name: `#${offspring.id}`,
            birth_date: offspring.birth_date,
            type: 'offspring',
            genotype: offspring.genotype,
            sex: offspring.sex,
            // 设置后代初始位置在右侧，根据数量垂直分布
            x: width * 0.75,
            y: height / (pedigree.offspring.length + 1) * (index + 1)
          }
          nodes.push(offspringNode)
          links.push({
            source: currentNode,
            target: offspringNode,
            type: 'offspring'
          })
          return offspringNode
        }).catch(error => {
          console.error(`获取后代小鼠 ${id} 失败:`, error)
          const fallbackNode = {
            id,
            name: `#${id}`,
            birth_date: '未知',
            type: 'offspring',
            genotype: '未知',
            sex: '未知',
            x: width * 0.75,
            y: height / (pedigree.offspring.length + 1) * (index + 1)
          }
          nodes.push(fallbackNode)
          links.push({
            source: currentNode,
            target: fallbackNode,
            type: 'offspring'
          })
          return fallbackNode
        })
      )
    }
  }

  // 等待所有节点加载完成
  try {
    await Promise.all(nodePromises)
  } catch (error) {
    console.error('谱系图节点加载错误:', error)
  }

  // 创建力导向图并保存引用
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links)
      .id(d => d.id)
      .distance(100) // 连接距离
      .strength(0.8) // 连接强度
    )
    .force('charge', d3.forceManyBody()
      .strength(-200) // 减少排斥力
    )
    .force('collide', d3.forceCollide().radius(30)) // 防止节点重叠
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('x', d3.forceX().x(d => {
      // 根据类型设置水平位置约束
      if (d.type === 'father' || d.type === 'mother') return width * 0.25
      if (d.type === 'current') return width / 2
      return width * 0.75
    }).strength(0.1)) // 水平位置约束强度
    .force('y', d3.forceY().y(height / 2).strength(0.05)) // 垂直居中约束

  const link = svg.append('g')
    .selectAll('line')
    .data(links)
    .enter()
    .append('line')
    .attr('stroke', d => {
      if (d.type === 'father') return '#34a853' // 父代用绿色
      if (d.type === 'mother') return '#ea4335' // 母代用红色
      return '#999' // 后代用灰色
    })
    .attr('stroke-width', 2)
    .attr('marker-end', d => {
      if (d.type === 'father' || d.type === 'mother') {
        return 'url(#arrow-father)';
      } else {
        return 'url(#arrow-offspring)';
      }
    });

  // 创建节点组（包含圆形和文本）
  const nodeGroups = svg.append('g')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'node-group')
    .attr('transform', d => `translate(${d.x},${d.y})`)
    .call(d3.drag()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded)
    );

  // 在节点组内添加圆形
  nodeGroups.append('circle')
    .attr('r', 20)
    .attr('fill', d => {
      switch (d.type) {
        case 'current': return '#4285f4'; // 当前小鼠蓝色
        case 'father': return '#34a853'; // 父代绿色
        case 'mother': return '#ea4335'; // 母代红色
        default: return '#999'; // 后代灰色
      }
    });

  // 在节点组内添加文本标签
  nodeGroups.append('text')
    .text(d => d.name)
    .attr('font-size', '12px')
    .attr('text-anchor', 'middle')
    .attr('dy', 5)
    .attr('fill', '#fff');

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeGroups
      .attr('transform', d => `translate(${d.x},${d.y})`)
  })

  function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }
  
  function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    // 保持拖动后的位置
    d.fx = event.x
    d.fy = event.y
  }

  // 创建tooltip元素
  let tooltip = d3.select('.pedigree-tooltip');

  if (tooltip.empty()) {
    tooltip = d3.select('body')
      .append('div')
      .attr('class', 'pedigree-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', 'rgba(255,255,255,0.9)')
      .style('border', '1px solid #ddd')
      .style('border-radius', '4px')
      .style('padding', '8px')
      .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
      .style('z-index', '1000')
      .style('font-size', '14px')
  }

  // 节点添加悬停事件
  nodeGroups
    .on('mouseover', function(event, d) {
      if (tooltip) {
        tooltip
          .html(`
          <div>ID: #${d.name}</div>
          <div>生日: #${formatDate(d.birth_date)}</div>
          <div>基因型: ${d.genotype || '未知'}</div>
          <div>性别: ${d.sex === 'M' ? '雄性' : d.sex === 'F' ? '雌性' : '未知'}</div>
          `)
          .style('visibility', 'visible')
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 30) + 'px');
      }
      
      // 高亮当前节点和相关边
      nodeGroups.attr('stroke-width', 0);
      d3.select(this).attr('stroke', '#333').attr('stroke-width', 2);
      
      link.attr('stroke-opacity', 0.2);
      link.filter(l => l.source.id === d.id || l.target.id === d.id)
        .attr('stroke-opacity', 1)
        .attr('stroke', d => {
            if (d.type === 'father') return '#34a853'
            if (d.type === 'mother') return '#ea4335'
            return '#4285f4'
          })
      })
    .on('mouseout', function() {
        tooltip.style('visibility', 'hidden')
        
        // 恢复默认样式
        nodeGroups.attr('stroke-width', 0)
        link.attr('stroke-opacity', 1).attr('stroke', d => {
          if (d.type === 'father') return '#34a853'
          if (d.type === 'mother') return '#ea4335'
          return '#999'
        })
      })
    .on('dblclick', (event, d) => {
      if (d.id !== currentMouseID.value) {
        tooltip.style('visibility', 'hidden');
        // 存储当前小鼠ID作为返回目标
        navigateToMouse(d.id);
      }
    });

  // 保存引用
  simulationRef.value = simulation
}

    // ========== ResizeObserver（只观察谱系图容器，带防抖） ==========
    const setupResizeObserver = () => {
    resizeObserver = new ResizeObserver((entries) => {
        if (resizeTimer) clearTimeout(resizeTimer)
        resizeTimer = setTimeout(() => {
        // 只对 d3 svg 重新布局/重绘
        renderPedigreeChart()
        // Chart.js 会自己监听容器变化，若需要强制 resize：
        if (chartInstance) {
            try { chartInstance.resize() } catch (e) { /* ignore */ }
        }
        }, 120)
    })

    if (pedigreeChart.value) resizeObserver.observe(pedigreeChart.value)
    // **注意**：不要 observe weightChart（canvas）本身 — 会造成 destroy/create 循环
    }

    const navigateToMouse = (mouseId) => {
        prevMouseId.value = currentMouseID.value
        currentMouseID.value = mouseId
    };

    onMounted(() => {
      fetchMouseData()
      setupResizeObserver()
    })

    onUnmounted(() => {
    if (chartInstance) chartInstance.destroy()
    if (resizeObserver) resizeObserver.disconnect()
    if (simulationRef.value) {
        try { simulationRef.value.stop() } catch (e) {}
        simulationRef.value = null
    }
    })

    return {
    closeMainModal,
    mouseData,
    weightChart,
    pedigreeChart,
    formatDate,
    setDeletingRecord,
    deletingRecordId,
    saveNewRecord,
    newRecord,
    cancelAddRecord,
    openAddRecordForm,
    showAddRecordForm,
    prevMouseId,
    navigateToMouse,
    currentMouseID
    }
}
}
</script>

<style scoped>
/* 遮罩层 */
.modal-overlay {
position: fixed;
top: 0; left: 10px; right: 0; bottom: 0;
background-color: rgba(0, 0, 0, 0.6);
z-index: 100;
animation: fadeIn 0.3s ease;
}

/* 主模态 */
.mouse-detail-modal {
position: fixed;
top: 50%; left: 52%;
transform: translate(-50%, -50%);
width: 90%; 
max-width: 1200px; 
max-height: 90vh;
background-color: #f8f9fa;
border-radius: 12px;
box-shadow: 0 10px 40px rgba(0,0,0,0.3);
padding: 20px;
overflow-y: auto;
z-index: 101;
animation: slideIn 0.4s ease;
}

@keyframes fadeIn {
from { opacity: 0; }
to { opacity: 1; }
}

@keyframes slideIn {
from { 
    opacity: 0;
    transform: translate(-50%, -45%);
}
to { 
    opacity: 1;
    transform: translate(-50%, -50%);
}
}

.page-header {
display: flex;
align-items: center;
margin-bottom: 20px;
}

.back-button {
display: flex;
align-items: center;
background: #4285f4;
color: white;
border: none;
padding: 8px 12px;
border-radius: 4px;
cursor: pointer;
margin-right: 15px;
font-size: 14px;
transition: all 0.2s;
}

.back-button:hover {
background: #3367d6;
transform: translateX(-2px);
}

.page-header h2 {
color: #2c3e50;
margin: 0;
font-weight: 600;
font-size: 1.8rem;
}

.detail-grid {
display: grid;
grid-template-columns: 1fr 1fr;
grid-template-rows: auto auto;
gap: 20px;
min-height: 400px;
}

.grid-item {
min-height: 200px;
}

.basic-info {
grid-column: 1;
grid-row: 1;
}

.status-records {
grid-column: 2;
grid-row: 1;
}

.status-item {
pointer-events: auto;
cursor: pointer;
padding: 8px 12px;
border: 1px solid #e0e0e0;
border-radius: 4px;
margin-bottom: 8px;
transition: all 0.3s ease;
position: relative;
}

.status-item.deleting {
background-color: #fff5f5;
border-color: #feb2b2;
box-shadow: 0 0 0 1px #feb2b2;
}

.pedigree {
grid-column: 1;
grid-row: 2;
}

.weight-chart {
grid-column: 2;
grid-row: 2;
}

.card {
background: white;
border-radius: 8px;
box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
padding: 20px;
height: 100%;
display: flex;
flex-direction: column;
}

.card-title {
color: #4285f4;
margin-top: 0;
margin-bottom: 15px;
font-size: 16px;
font-weight: 600;
padding-bottom: 10px;
border-bottom: 1px solid #eaeaea;
}

.info-content {
flex: 1;
}

.info-row {
display: flex;
margin-bottom: 12px;
align-items: center;
}

.info-label {
font-weight: 600;
color: #555;
width: 120px;
flex-shrink: 0;
}

.info-value {
color: #333;
}

.status-content {
flex: 1;
overflow-y: auto;
max-height: 200px;
}

.status-list {
display: flex;
flex-direction: column;
gap: 12px;
}

.status-item {
display: flex;
align-items: center;
padding: 10px;
background-color: #f8f9fa;
border-radius: 6px;
border-left: 3px solid #4285f4;
}

.status-date {
font-weight: 600;
color: #4285f4;
margin-right: 12px;
min-width: 80px;
}

.status-description {
color: #555;
}

.no-data {
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
height: 100%;
color: #999;
}

.no-data i {
font-size: 36px;
margin-bottom: 10px;
opacity: 0.5;
}

.no-data p {
margin: 0;
font-style: italic;
}
/* Chart / SVG 容器：为 canvas 提供固定高度，避免 flex:1 导致尺寸被父 flex 反复拉伸 */
.chart-container {
width: 100%;
}

/* pedigree SVG 的容器 */
.svg-container {
min-height: 220px;
height: 220px;
}

/* weight chart 父容器（有固定高度），canvas 填满该容器 */
.canvas-wrapper {
height: 260px;
flex: none;
position: relative;
}

/* 确保 canvas 正确填充父容器（Chart.js 使用父容器大小） */
canvas {
width: 100% !important;
height: 100% !important;
display: block;
}

.action-buttons {
display: flex;
justify-content: flex-end;
gap: 15px;
margin-top: 25px;
padding-top: 20px;
border-top: 1px solid #eaeaea;
}

.btn {
padding: 10px 20px;
border-radius: 6px;
font-size: 14px;
display: flex;
align-items: center;
gap: 8px;
cursor: pointer;
transition: all 0.2s;
}

.btn-outline {
background: transparent;
border: 1px solid #4285f4;
color: #4285f4;
}

.btn-outline:hover {
background: rgba(66, 133, 244, 0.1);
}

.btn-primary {
background: #4285f4;
color: white;
border: none;
}

.btn-primary:hover {
background: #3367d6;
}

/* 响应式设计 */
@media (max-width: 1200px) {
.mouse-detail-modal {
    width: 95%;
}
}

@media (max-width: 992px) {
  .mouse-detail-modal {
    width: 95%;
    left: 50%;
    transform: translateX(-50%);
  }
.detail-grid {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, auto);
    height: auto;
}

.basic-info {
    grid-column: 1;
    grid-row: 1;
}

.status-records {
    grid-column: 1;
    grid-row: 2;
}

.pedigree {
    grid-column: 1;
    grid-row: 3;
}

.weight-chart {
    grid-column: 1;
    grid-row: 4;
}

.action-buttons {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
}
}

@media (max-width: 768px) {
.mouse-detail-modal {
    padding: 15px;
    width: 98%;
}

.page-header {
    flex-direction: column;
    align-items: flex-start;
}

.back-button {
    margin-bottom: 10px;
    width: 100%;
    justify-content: center;
}

.info-row {
    flex-direction: column;
    align-items: flex-start;
}

.info-label {
    margin-bottom: 4px;
}

.status-item {
    flex-direction: column;
    align-items: flex-start;
}

.status-date {
    margin-bottom: 6px;
}
}


.add-record-button {
display: flex;
align-items: center;
background: #4285f4;
color: white;
border: none;
padding: 6px 12px;
border-radius: 4px;
cursor: pointer;
font-size: 14px;
transition: all 0.2s;
}

.add-record-button:hover {
background: #3367d6;
}

.add-record-button i {
margin-right: 5px;
font-size: 18px;
}

.modal-content {
background: white;
border-radius: 12px;
width: 90%;
max-width: 500px;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
animation: modalIn 0.3s ease;
}

@keyframes modalIn {
from { opacity: 0; transform: translateY(-20px); }
to { opacity: 1; transform: translateY(0); }
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
color: #2c3e50;
}

.close-button {
background: none;
border: none;
cursor: pointer;
color: #777;
font-size: 24px;
padding: 5px;
}

.close-button:hover {
color: #333;
}

.btn-cancel {
background: #f5f5f5;
color: #555;
border: 1px solid #ddd;
}

.btn-cancel:hover {
background: #eaeaea;
}

.btn-confirm {
background: #4285f4;
color: white;
}

.btn-confirm:hover {
background: #3367d6;
}

.add-record-form {
  background-color: #f9f9f9;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
  border: 1px solid #e0e0e0;
}

.add-record-form .form-group {
  margin-bottom: 12px;
}

.add-record-form label {
  display: block;
  font-weight: 500;
  color: #555;
  margin-bottom: 5px;
}

.add-record-form input[type="date"] {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.add-record-form textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
  min-height: 60px;
}

.form-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

/* 添加悬停提示样式 */
.pedigree-tooltip {
  z-index: 1000;
  font-size: 14px;
  line-height: 1.4;
  min-width: 120px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  position: absolute;
}

/* 返回按钮样式调整 */
.page-header .back-button {
  margin-right: 10px;
}
</style>
