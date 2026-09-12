<template>
  <div class="main-content">
    <div class="content-header">
      <h1 class="page-title">小鼠生存分析</h1>
    </div>
    
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">生存曲线分析</h5>
      </div>
      <div class="card-body">
        <!-- 控制按钮区域 -->
        <div class="d-flex mb-4">
        <select v-model="showChartType" style="min-width:200px;">
            <option value="pred">使用预设分组</option>
            <option value="temp">使用临时分组</option>
        </select>
        </div>
        <div v-if="showChartType === 'pred'" class="d-flex justify-content-between mb-4">
          <select v-model="selectedPredefinedGroupId" style="min-width:100px;">
            <option v-if="predefinedGroups.length === 0" :value='null' :disabled="true">---请在设置中确定预设分组---</option>
            <option v-for="group in predefinedGroups" :value="group.id" :key="group.id">
                {{ group.name }}
            </option>
          </select>
          <button class="btn btn-primary" @click="fetchData('pred')">
            <i class="material-icons">insights</i>
            以预设分组生成生存曲线
          </button>
        </div>
        <div v-if="showChartType === 'temp'" class="d-flex justify-content-between mb-4">
            <button class="btn btn-primary" @click="fetchData('temp')">
              <i class="material-icons">insights</i>
              以临时分组生成生存曲线
            </button>
            <button class="btn btn-sm btn-outline" @click="addGroup">
              <i class="material-icons">add</i> 添加分组
            </button>
            <button id="addGroupBtn" class="btn btn-sm btn-danger" @click="clearGroups">
            <i class="material-icons">clear</i> 清空分组
            </button>
        </div>
        
        <!-- 分组设置 -->
        <div v-if="showChartType === 'temp'" class="mb-4">
          <h5>分组设置</h5>
          <div class="groups-container">
            <div 
              v-for="(group, index) in tempGroups" 
              :key="index" 
              class="group-card"
            >
              <div class="card">
                <div class="card-header compact-header d-flex justify-content-between align-items-center">
                  <span>分组 {{ index }}</span>
                  <button @click="removeGroup(index)" v-if="tempGroups.length > 1">
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
                        <label class="form-label">基因型包含：（需要更加复杂的逻辑请使用预设分组）</label>
                        <div class="genotype-tree">
                            <div v-for="(combinations, locus) in geneStore.allGenotypes" :key="locus" class="locus-item">
                            <div class="locus-header">
                                <label class="locus-label">
                                <input 
                                    type="checkbox" 
                                    :value="locus" 
                                    v-model="group.genotype"
                                    @change="onLocusSelect(index, locus)"
                                    class="locus-checkbox"
                                >
                                <span class="locus-name">{{ locus }}</span>
                                </label>
                            </div>
                            <div v-if="combinations && combinations.length" class="combinations-list">
                                <div v-for="combination in combinations" :key="combination" class="combination-item">
                                <label class="combination-label">
                                    <input 
                                    type="checkbox" 
                                    :value="`${locus}<sup>${combination}</sup>`"
                                    v-model="group.genotype"
                                    @change="onCombinationSelect(index, locus, combination)"
                                    class="combination-checkbox"
                                    >
                                    <span class="combination-name" v-html="`${locus}<sup>${combination}</sup>`"></span>
                                </label>
                                </div>
                            </div>
                            </div>
                        </div>
                        </div>
                    </div>
                </div>
              </div>
            </div>
            
            <div 
              v-if="tempGroups.length < 8" 
              class="group-card add-card"
              @click="addGroup"
            >
              <i class="material-icons">add</i>
              <span>添加分组</span>
            </div>
          </div>
        </div>
        
        <div v-if="hasData">
          <!-- 统计信息卡片 -->
          <div class="card mb-4">
            <div class="card-header">
              统计摘要
            </div>
              <div 
                v-for="(group, index) in groups" 
                :key="index"
              >
              <div class="card-body">
                <div class="d-flex flex-wrap justify-content-around">
                  <!-- 图例 -->
                  <div class="d-flex flex-wrap mt-4">
                      <span class="legend-color" :style="{backgroundColor: group.color}"></span>
                      {{ group.name || `分组 ${index}` }}
                  </div>
                  <div class="stat-card text-center mx-2">
                    <div class="stat-value">{{ group.allMice }}</div>
                    <div class="stat-label">总小鼠数</div>
                  </div>
                  <div class="stat-card text-center mx-2">
                    <div class="stat-value">{{ group.deadMice }}</div>
                    <div class="stat-label">死亡小鼠数</div>
                  </div>
                  <div class="stat-card text-center mx-2">
                    <div class="stat-value">{{ group.censoredMice }}</div>
                    <div class="stat-label">存活小鼠数</div>
                  </div>
                  <div class="stat-card text-center mx-2">
                    <div class="stat-value">{{ group.maxDays }} 天</div>
                    <div class="stat-label">最长生存时间</div>
                  </div>
                  <div class="stat-card text-center mx-2">
                    <div class="stat-value">{{ group.ls50 }} 天</div>
                    <div class="stat-label">中位生存时间</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 图表容器 -->
          <div class="chart-container">
            <canvas id="survivalChart" height="400"></canvas>
          </div>
          <div class="d-flex justify-content-end mt-3 mb-3">
            <button class="primary-btn" @click="exportSurvivalChart">
              <i class="material-icons" style="font-size: 18px;">download</i> 导出图表
            </button>
          </div>

          <!-- 数据表格 -->
          <div class="card mt-4">
            <div class="card-header">
              生存数据详情
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>小鼠ID</th>
                      <th>性别</th>
                      <th>基因型</th>
                      <th>生存天数</th>
                      <th>状态</th>
                      <th>分组</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(mouse, index) in displayedMice" :key="index">
                      <td>{{ mouse.mouse_id }}</td>
                      <td>{{ mouse.sex === 'M' ? '雄性' : '雌性' }}</td>
                      <td v-html="mouse.genotype"></td>
                      <td>{{ mouse.living_days }} 天</td>
                      <td>
                        <span :class="{'text-success': mouse.status === 0, 'text-danger': mouse.status === 1}">
                          {{ mouse.status === 1 ? '死亡' : '存活' }}
                        </span>
                      </td>
                      <td>
                        <span class="badge" :style="{backgroundColor: mouse.color}">
                          {{ mouse.groupName }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <!-- 分页控件 -->
              <nav v-if="filteredMice.length > pageSize">
                <ul class="pagination justify-content-center">
                  <li class="page-item" :class="{disabled: currentPage === 1}">
                    <a class="page-link" href="#" @click.prevent="currentPage > 1 && currentPage--">上一页</a>
                  </li>
                  <li class="page-item" v-for="page in totalPages" :key="page" 
                      :class="{active: currentPage === page}">
                    <a class="page-link" href="#" @click.prevent="currentPage = page">{{ page }}</a>
                  </li>
                  <li class="page-item" :class="{disabled: currentPage === totalPages}">
                    <a class="page-link" href="#" @click.prevent="currentPage < totalPages && currentPage++">下一页</a>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
        <!-- 无数据提示 -->
        <div v-else class="text-center py-5">
          <div class="mb-3">
            <i class="material-icons" style="font-size: 3rem; color: #6c757d;">bar_chart</i>
          </div>
          <h5 class="text-muted">请设置分组条件并点击"生成生存曲线"按钮</h5>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import axios from 'axios';
import Chart from 'chart.js/auto';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';
import { useGeneStore, useExperimentStore } from '@/stores'
import { storeToRefs } from 'pinia'

const geneStore = useGeneStore()
const { tempGroups } = storeToRefs(geneStore)
const { addGroup, removeGroup, clearGroups, getTempGroups, onLocusSelect, onCombinationSelect } = geneStore
const experimentStore = useExperimentStore()
const { predefinedGroups, selectedPredefinedGroupId, showChartType } = storeToRefs(experimentStore)
const { getPredefinedGroups } = experimentStore

// 响应式数据
const groups = ref([]);
const chartInstance = ref(null);
const hasData = ref(false);
const currentPage = ref(1);
const pageSize = 10;

// 获取生存数据
const fetchData = async (groupType) => {
  try {
    let groupData = []
    if (groupType === 'temp') {
      if (tempGroups.value.length === 0) {
        toast.info('请至少添加一个分组');
        return;
      }
      groupData = await getTempGroups()
    } else if (groupType === 'pred') {
      if (!selectedPredefinedGroupId.value) {
        toast.info('请选择预设分组');
        return;
      }
      groupData = await getPredefinedGroups()
    }
    if (groupData.length === 0) {
      toast.info('预设分组暂无信息');
      return;
    }
    const response = await axios.post('/api/survival-analysis', {
      groups: groupData.map(g => g.mice)
    });

    if (response.data.success) {
      // 更新前端状态
      groups.value = response.data.group_results.map((group, index) => {
        if (groupData[index]) {
          return {
            ...group, // 保留所有原有属性
            name: groupData[index].name,
            color: groupData[index].color
          };
        }
        return group; // 如果没有对应的 groupData，返回原对象
      });
      hasData.value = true;
      await nextTick();
      // 使用后端准备好的图表数据
      renderChart();
    } else {
      toast.error(response.data.error || '分析失败');
    }
  } catch (error) {
    console.error('获取生存数据失败:', error);
    toast.error(`获取数据失败：${error}`);
  }
};

// 渲染图表
const renderChart = () => {
  const ctx = document.getElementById('survivalChart');
  
  // 销毁现有图表实例
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
  
  if (groups.value.length === 0) {
    return;
  }

  // 创建生存曲线数据集
  const datasets = groups.value
    .filter(group => group.survivalData && group.survivalData.length > 0)
    .map((group, groupIndex) => {
      // 生存曲线数据集
      const survivalDataset = {
        label: group.name,
        data: group.survivalData.map(point => ({
          x: point.x,
          y: point.y
        })),
        borderColor: group.color,
        backgroundColor: `${group.color}20`,
        borderWidth: 3,
        pointRadius: 0, // 隐藏曲线上的点
        fill: false,
        stepped: true,
        tension: 0,
        spanGaps: false
      };

      // 死亡事件点数据集
      const eventPoints = group.survivalData
        .filter(point => point.mouseIds && point.mouseIds.length > 0)
        .map(point => ({
          x: point.x,
          y: point.y,
          mouseIds: point.mouseIds
        }));
      
      const eventDataset = {
        label: `${group.name} - 死亡事件`,
        data: eventPoints,
        pointBackgroundColor: group.color,
        pointBorderColor: `${group.color}20`,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointStyle: '',
        showLine: false,
        borderWidth: 0
      };

      // 删失事件数据集
      const censoredDataset = {
        label: `${group.name} - 删失事件`,
        data: group.censoredPoints.map(point => ({
          x: point.x,
          y: point.y,
          mouseIds: point.mouseIds
        })),
        pointBackgroundColor: `${group.color}20`,
        pointBorderColor: `${group.color}20`,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointStyle: 'rectRounded',
        showLine: false,
        borderWidth: 0
      };

      return [survivalDataset, eventDataset, censoredDataset];
    })
    .flat(); // 将多维数组展平为一维

  // 获取最大时间范围
  const maxTime = Math.max(
    ...groups.value.flatMap(group => [
      ...(group.survivalData || []).map(p => p.x),
      ...(group.censoredPoints || []).map(p => p.x)
    ]),
    10 // 确保最小值
  ) + 5; // 添加边距

  // 创建图表
  chartInstance.value = new Chart(ctx, {
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
            text: '生存时间 (天)'
          },
          min: 0,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            stepSize: Math.ceil(maxTime / 10)
          }
        },
        y: {
          type: 'linear',
          title: {
            display: true,
            text: '生存率'
          },
          min: 0,
          max: 1.1,
          ticks: {
            callback: (value) => (value * 100).toFixed(0) + '%'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            boxWidth: 12,
            padding: 20,
            font: {
              size: 12
            },
            filter: item => !item.text.includes('事件') // 隐藏事件点的图例
          }
        },
        tooltip: {
          filter: function(tooltipItem) {
            // 只对死亡事件和删失事件显示工具提示
            return tooltipItem.dataset.label.includes('死亡事件') || 
                  tooltipItem.dataset.label.includes('删失事件');
          },
          callbacks: {
            label: (context) => {
              const datasetLabel = context.dataset.label || '';
              const value = context.parsed.y;
              const mouseIds = context.raw.mouseIds || [];
              
              if (datasetLabel.includes('死亡事件')) {
                return `死亡事件: ${(value * 100).toFixed(1)}% (${mouseIds.length}只小鼠死亡)`;
              } else if (datasetLabel.includes('删失事件')) {
                return `删失事件：${mouseIds.length}只小鼠尚存活`;
              }
              return `生存率: ${(value * 100).toFixed(1)}%`;
            },
            title: (tooltipItems) => {
              const item = tooltipItems[0];
              const dataPoint = item.raw;
              
              if (dataPoint.mouseIds && dataPoint.mouseIds.length > 0) {
                return `小鼠编号: ${dataPoint.mouseIds.join(', ')}\n时间: ${item.parsed.x} 天`;
              }
              return `存活时间: ${item.parsed.x} 天`;
            }
          }
        }
      }
    }
  });
};

const exportSurvivalChart = async () => {
  if (!chartInstance.value) {
    toast.info('请先生成图表');
    return;
  }

  // 记录导出审计（审计禁用时跳过）
  try {
    const resp = await axios.get('/api/audit-info');
    if (resp.data.audit_enabled === false) {
      console.info('当前数据库已禁用审计，跳过审计记录')
    }
  } catch (e) { console.warn('审计记录失败:', e) }

  const W = 1600, H = 800;
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = W;
  tempCanvas.height = H;
  tempCanvas.style.position = 'fixed';
  tempCanvas.style.left = '-9999px';
  tempCanvas.style.top = '-9999px';
  document.body.appendChild(tempCanvas);

  const src = chartInstance.value;
  const datasets = src.config.data.datasets.map(ds => ({
    label: ds.label,
    data: ds.data.map(p => ({ x: p.x, y: p.y })),
    borderColor: ds.borderColor,
    backgroundColor: ds.backgroundColor,
    borderWidth: ds.borderWidth,
    pointRadius: ds.pointRadius,
    pointBackgroundColor: ds.pointBackgroundColor,
    pointBorderColor: ds.pointBorderColor,
    pointStyle: ds.pointStyle,
    showLine: ds.showLine,
    stepped: ds.stepped,
    tension: ds.tension,
    spanGaps: ds.spanGaps
  }));

  const yScale = src.scales.y;

  const exportChart = new Chart(tempCanvas.getContext('2d'), {
    type: 'line',
    data: { datasets },
    options: {
      responsive: false,
      maintainAspectRatio: true,
      animation: false,
      devicePixelRatio: 2,
      scales: {
        x: {
          type: 'linear',
          title: { display: true, text: '生存时间 (天)' },
          min: src.scales.x.min,
          max: src.scales.x.max
        },
        y: {
          type: 'linear',
          title: { display: true, text: '生存率' },
          min: 0,
          max: 1.1,
          ticks: {
            callback: value => (value * 100).toFixed(0) + '%'
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            boxWidth: 12,
            padding: 20,
            font: { size: 12 },
            filter: item => !item.text.includes('事件')
          }
        },
        tooltip: { enabled: false }
      }
    }
  });

  setTimeout(async () => {
    const filename = `生存曲线_${new Date().toISOString().slice(0, 10)}.png`;
    if (window.pywebview && window.pywebview.api) {
      tempCanvas.toBlob(async (blob) => {
        const arrayBuffer = await blob.arrayBuffer();
        const uint8array = new Uint8Array(arrayBuffer);
        const dataArray = Array.from(uint8array);
        const state = await window.pywebview.api.save_file_dialog(dataArray, filename);
        if (state.success) {
          toast.success(`导出成功，文件路径：${state.path}`);
        } else {
          toast.info(state.message || '导出失败');
        }
        exportChart.destroy();
        document.body.removeChild(tempCanvas);
      }, 'image/png');
    } else {
      const link = document.createElement('a');
      link.download = filename;
      link.href = tempCanvas.toDataURL('image/png');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      exportChart.destroy();
      document.body.removeChild(tempCanvas);
    }
  }, 300);
};

// 计算属性
const filteredMice = computed(() => {
  return groups.value.flatMap(group => 
    (group.mice || []).map(mouse => ({
      ...mouse,
      groupName: group.name || `分组 ${groups.value.indexOf(group)}`,
      color: group.color
    }))
  );
});
const totalPages = computed(() => Math.ceil(filteredMice.value.length / pageSize));
const displayedMice = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredMice.value.slice(start, start + pageSize);
});
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
  margin-bottom: 1.5rem;
}

.legend-item {
  display: inline-block;
  margin-right: 20px;
  font-size: 0.9rem;
}

.legend-color {
  display: inline-block;
  width: 15px;
  height: 15px;
  border-radius: 3px;
  margin-right: 5px;
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
    grid-template-columns: repeat(2, 1fr);
  }
}

.option-item {
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: normal;
    word-wrap: break-word;
}

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

.pagination {
    margin: 1.5rem 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.page-item {
    display: inline-block;
    margin: 0 4px;
    border-radius: 6px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.page-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.page-link {
    display: block;
    min-width: 42px;
    height: 42px;
    line-height: 42px;
    padding: 0 12px;
    text-align: center;
    text-decoration: none;
    font-weight: 500;
    font-size: 1rem;
    color: #4a5568;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 1px solid #dee2e6;
    border-radius: 6px;
    transition: all 0.25s ease;
    cursor: pointer;
}

.page-link:hover {
    color: #2d3748;
    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
    border-color: #c4c9d0;
}

.page-item.active .page-link {
    color: white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-color: #667eea;
    box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
}

.page-item.active .page-link:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
}

.page-item.disabled .page-link {
    color: #a0aec0;
    background: linear-gradient(135deg, #f8f9fa 0%, #edf2f7 100%);
    border-color: #e2e8f0;
    cursor: not-allowed;
    opacity: 0.7;
    pointer-events: none;
}

.page-item.disabled:hover {
    transform: none;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

@media (max-width: 576px) {
    .page-link {
        min-width: 36px;
        height: 36px;
        line-height: 36px;
        padding: 0 8px;
        font-size: 0.9rem;
    }
    .page-item {
        margin: 0 2px;
    }
}

.page-link:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.25);
}

.table th {
  padding: 15px 12px;
  position: sticky;
  top: 0;
}
</style>