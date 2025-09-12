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
        <div class="d-flex justify-content-between mb-4">
          <div>
            <button class="btn btn-primary" @click="fetchData">
              <i class="material-icons">insights</i>
              生成生存曲线
            </button>
          </div>
          <div>
            <button class="btn btn-sm btn-outline" @click="addGroup">
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
                <div class="card-header compact-header d-flex justify-content-between align-items-center">
                  <span>分组 {{ groupLetters[index] }}</span>
                  <button @click="removeGroup(index)" v-if="groups.length > 1">
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
                                :value="genotype.name">
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
                      <span class="legend-color" :style="{backgroundColor: getColor(index)}"></span>
                      {{ group.name || `分组 ${groupLetters[index]}` }}
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
                      <td>{{ mouse.genotype }}</td>
                      <td>{{ mouse.living_days }} 天</td>
                      <td>
                        <span :class="{'text-success': mouse.status === 0, 'text-danger': mouse.status === 1}">
                          {{ mouse.status === 1 ? '死亡' : '存活' }}
                        </span>
                      </td>
                      <td>
                        <span class="badge" :style="{backgroundColor: getGroupColor(mouse.groupIndex)}">
                          {{ mouse.groupName || `分组 ${groupLetters[mouse.groupIndex]}` }}
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
                    <a class="page-link" href="#" @click.prevent="currentPage--">上一页</a>
                  </li>
                  <li class="page-item" v-for="page in totalPages" :key="page" 
                      :class="{active: currentPage === page}">
                    <a class="page-link" href="#" @click.prevent="currentPage = page">{{ page }}</a>
                  </li>
                  <li class="page-item" :class="{disabled: currentPage === totalPages}">
                    <a class="page-link" href="#" @click.prevent="currentPage++">下一页</a>
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

<script>
import { ref, computed, onMounted, nextTick } from 'vue';
import axios from 'axios';
import Chart from 'chart.js/auto';
import { max } from 'd3';

export default {
  name: 'SurvivalAnalysis',
  setup() {
    const micedata = ref([]);

    // 分组颜色方案
    const groupColors = [
      '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
      '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
    ];
    
    // 基因型选项
    const allGenotypes = ref([]);
    
    // 分组数据
    const groups = ref([]);
    const groupLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
    
    // 生存数据
    const survivalData = ref([]);
    const chartInstance = ref(null);
    const hasData = ref(false);
    const currentPage = ref(1);
    const pageSize = 10;
    
    // 添加新分组
    const addGroup = () => {
      if (groups.value.length >= 8) {
        alert('最多只能添加8个分组');
        return;
      }
      groups.value.push({ 
        sex: { M: true, F: true }, 
        genotype: [] 
      });
    };
    
    // 删除分组
    const removeGroup = (index) => {
      if (groups.value.length > 1) {
        groups.value.splice(index, 1);
      }
    };
    
    // 获取分组颜色
    const getGroupColor = (index) => {
      return groupColors[index % groupColors.length];
    };

    // 获取颜色（兼容bodyweight.vue的样式）
    const getColor = (index) => {
      const colors = [
        '#6a11cb', '#2575fc', '#20c997', '#ff416c', '#ff4b2b'
      ];
      return colors[index % colors.length];
    };

    const fetchData = async () => {
      try {
        if (groups.value.length === 0) {
          alert('请至少添加一个分组');
          return;
        } 
        // 重置所有分组的统计数据
        groups.value.forEach(group => {
          group.allMice = 0;
          group.deadMice = 0;
          group.censoredMice = 0;
          group.maxDays = 0;
          group.ls50 = 0;
          group.survivalData = []; // 存储生存曲线数据点
          group.censoredPoints = []; // 存储删失事件点
        });

        // 处理数据并添加分组信息
        survivalData.value = micedata.value.map(mouse => {
          // 确定小鼠属于哪个分组
          const groupIndex = groups.value.findIndex(group => {
            const sexMatch = group.sex[mouse.sex];
            const genotypeMatch = group.genotype.length === 0 || 
                                group.genotype.includes(mouse.genotype);
            return sexMatch && genotypeMatch;
          });
          
          if (groupIndex >= 0) {
            // 更新分组统计数据
            const group = groups.value[groupIndex];
            group.allMice++;
            
            // 注意：status=1表示死亡，status=0表示删失
            if (mouse.status === 1) {
              group.deadMice++;
            } else if (mouse.status === 0) {
              group.censoredMice++;
            }
            
            if (mouse.living_days > group.maxDays) {
              group.maxDays = mouse.living_days;
            }
          }
          
          return {
            ...mouse,
            groupIndex: groupIndex >= 0 ? groupIndex : -1
          };
        });
        // 为每个分组计算生存曲线数据点和中位生存时间
        groups.value.forEach(group => {
          if (group.allMice > 0) {
            // 筛选当前分组的小鼠数据
            const groupMice = survivalData.value.filter(
              m => m.groupIndex === groups.value.indexOf(group)
            );
            
            // 按生存时间排序
            const sortedData = [...groupMice].sort((a, b) => a.living_days - b.living_days);
            
            let cumulativeSurvival = 1.0;
            let atRisk = sortedData.length;
            let ls50Found = false;
            // 添加起始点 (0, 1)
            group.survivalData.push({ x: 0, y: 1, mouseIds: [] });
            for (let i = 0; i < sortedData.length; i++) {
              const mouse = sortedData[i];
              // 处理删失事件（status=0）
              if (mouse.status === 0) {
                group.censoredPoints.push({
                  x: mouse.living_days,
                  y: cumulativeSurvival,
                  mouseIds: [mouse.mouse_id]
                });
                atRisk--;
                continue;
              }
              // 计算死亡事件后的生存率（status=1）
              const deathsAtTime = sortedData.filter(m => 
                m.living_days === mouse.living_days && m.status === 1
              );
              // 计算新的生存率
              const survivalRate = 1 - (deathsAtTime.length / atRisk);
              cumulativeSurvival *= survivalRate;
              // 添加数据点
              group.survivalData.push({
                x: mouse.living_days,
                y: cumulativeSurvival,
                mouseIds: deathsAtTime.map(m => m.mouse_id)
              });
              // 记录中位生存时间
              if (!ls50Found && cumulativeSurvival <= 0.5) {
                group.ls50 = mouse.living_days;
                ls50Found = true;
              }
              // 调整索引和剩余数量
              atRisk -= deathsAtTime.length;
              i += deathsAtTime.length - 1;
            };
          }
        });
        const maximumDays = Math.max(...groups.value.map(g => g.maxDays));
        // 在所有分组循环完成后，单独处理全删失组
        groups.value.forEach(group => {
          if (group.deadMice === 0 && group.censoredMice > 0) {
            // 筛选当前分组的小鼠数据
            const groupMice = survivalData.value.filter(
              m => m.groupIndex === groups.value.indexOf(group)
            );
            
            // 按生存时间排序
            const sortedData = [...groupMice].sort((a, b) => a.living_days - b.living_days);
            
            // 创建水平生存曲线
            group.survivalData = [
              { x: 0, y: 1, mouseIds: [] },
              { x: maximumDays, y: 1, mouseIds: [] }
            ];
            
            // 添加所有删失点
            sortedData.forEach(mouse => {
              group.censoredPoints.push({
                x: mouse.living_days,
                y: 1,
                mouseIds: [mouse.mouse_id]
              });
            });
            
            // 中位生存时间未知
            group.ls50 = "未知";
          }
        });
        hasData.value = true;
        await nextTick();
        // 绘制图表
        renderChart();
      } catch (error) {
        console.error('获取生存数据失败:', error);
        alert('获取数据失败，请检查网络连接或后端服务');
      }
    };

const renderChart = () => {
  const ctx = document.getElementById('survivalChart');
  
  // 销毁现有图表实例
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
  
  // 创建生存曲线数据集
  const datasets = groups.value
    .filter(group => group.survivalData && group.survivalData.length > 0)
    .map((group, groupIndex) => {
      const groupName = group.name || `分组 ${groupLetters[groupIndex]}`;
      
      // 生存曲线数据集
      const survivalDataset = {
        label: groupName,
        data: group.survivalData.map(point => ({
          x: point.x,
          y: point.y,
          // 添加小鼠ID信息
          mouseIds: point.mouseIds || [] 
        })),
        borderColor: getColor(groupIndex),
        backgroundColor: `${getColor(groupIndex)}20`,
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
        label: `${groupName} - 死亡事件`,
        data: eventPoints,
        pointBackgroundColor: getColor(groupIndex),
        pointBorderColor: '#fff',
        pointRadius: 5,
        pointHoverRadius: 7,
        pointStyle: 'circle',
        showLine: false,
        borderWidth: 0
      };

      // 删失事件数据集
      const censoredDataset = {
        label: `${groupName} - 删失事件`,
        data: group.censoredPoints.map(point => ({
          x: point.x,
          y: point.y,
          mouseIds: point.mouseId
        })),
        pointBackgroundColor: '#000',
        pointBorderColor: '#000',
        pointRadius: 5,
        pointHoverRadius: 7,
        pointStyle: 'crossRot',
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
          callbacks: {
            label: (context) => {
              const datasetLabel = context.dataset.label || '';
              const value = context.parsed.y;
              
              if (datasetLabel.includes('死亡事件')) {
                return `死亡事件: ${(value * 100).toFixed(1)}%`;
              } else if (datasetLabel.includes('删失事件')) {
                return '删失事件';
              }
              return `生存率: ${(value * 100).toFixed(1)}%`;
            },
            title: (tooltipItems) => {
              const item = tooltipItems[0];
              const dataPoint = item.raw;
              
              if (dataPoint.mouseIds && dataPoint.mouseIds.length > 0) {
                return `小鼠编号: ${dataPoint.mouseIds.join(', ')}\n时间: ${item.parsed.x} 天`;
              }
              return `时间: ${item.parsed.x} 天`;
            }
          }
        }
      }
    }
  });
};
    
    // 过滤并分页显示的小鼠数据
    const filteredMice = computed(() => survivalData.value);
    const totalPages = computed(() => Math.ceil(filteredMice.value.length / pageSize));
    const displayedMice = computed(() => {
      const start = (currentPage.value - 1) * pageSize;
      return filteredMice.value.slice(start, start + pageSize);
    });
    
    // 初始化
    const init = async () => {
      try {
        // 获取基因型数据
        const response = await axios.get('/api/genotypes');
        allGenotypes.value = response.data;
        // 发送请求到后端API获取所有生存数据
        const miceResponse = await axios.get('/api/survival');
        micedata.value = miceResponse.data;
      } catch (error) {
        console.error('获取基因型数据失败:', error);
      }
    };
    
    onMounted(() => {
      init();
    });
    
    return {
      groups,
      allGenotypes,
      groupLetters,
      survivalData,
      hasData,
      currentPage,
      pageSize,
      filteredMice,
      totalPages,
      addGroup,
      removeGroup,
      fetchData,
      getGroupColor,
      getColor,
      displayedMice
    };
  }
};
</script>

<style scoped>
/* 使用与bodyweight.vue一致的卡片样式 */
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

/* 图表容器 */
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

.stat-card {
  text-align: center;
  padding: 1rem;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a2a6c;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
}

.table-responsive {
  overflow-x: auto;
}

.table-hover tbody tr:hover {
  background-color: #f5f7fa;
}

.badge {
  padding: 0.4em 0.6em;
  border-radius: 0.5rem;
  color: white;
  font-weight: 500;
}

.text-success {
  color: #52c41a;
}

.text-danger {
  color: #f5222d;
}

.text-muted {
  color: #6c757d;
}

.mx-2 {
  margin-left: 0.5rem;
  margin-right: 0.5rem;
}

.mx-3 {
  margin-left: 1rem;
  margin-right: 1rem;
}

.text-center {
  text-align: center;
}
</style>