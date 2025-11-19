<template>
  <div class="mouse-group-manager">
    <h2 class="section-title">ID分组管理</h2>
    
    <div class="id-grouping-container">
      <!-- 候选小鼠列表 -->
      <div class="candidate-mice">
        <h3>候选小鼠</h3>
        <div class="selection-controls">
          <div class="selection-info">
            已选择 {{ selectedMiceCount }} 只小鼠
          </div>
          <div class="selection-buttons">
            <button class="btn btn-outline" @click="selectAllMice">
              全选
            </button>
            <button class="btn btn-outline" @click="deselectAllMice">
              全不选
            </button>
          </div>
        </div>
        <div class="detail-item">
          <div class="checkbox-group">
            <input type="checkbox" v-model="isRepeated" id="edit-repeat-checkbox" :disabled="isRepeatedAble">
            <label for="edit-repeat-checkbox">是否可重复选择小鼠</label>
          </div>
        </div>
        <div class="search-container">
          <input 
            type="text" 
            class="search-input" 
            placeholder="搜索小鼠ID或基因型..."
            v-model="searchTerm"
          >
        </div>
        <div class="mice-list">
          <div 
            v-for="mouse in filteredMice" 
            :key="mouse.tid"
            class="mouse-item"
            :class="{ selected: isMouseSelected(mouse.tid) }"
            @click="toggleMouseSelection(mouse.tid)"
            draggable="true"
            @dragstart="onDragStart($event, mouse.tid)"
          >
            <input 
              type="checkbox" 
              class="mouse-checkbox"
              :checked="isMouseSelected(mouse.tid)"
              @click.stop
            >
            <div class="mouse-info">
              <div class="mouse-id">{{ mouse.id }}</div>
              <div class="mouse-details" v-html="mouse.genotype.symbol"></div>
              <div class="mouse-details">{{ mouse.sex }} · {{ mouse.strain }} · {{ mouse.birth_date }}</div>
            </div>
          </div>
          <div v-if="filteredMice.length === 0" style="color:gray;">
            暂无可选小鼠，请在小鼠页面为小鼠添加"完成实验"
          </div>
        </div>
      </div>
      
      <!-- 分组管理 -->
      <div class="grouping-section">
        <h3>分组管理</h3>
        <div class="groups-container">
          <div 
            v-for="(group, groupIndex) in editingGroup.rules" 
            :key="groupIndex"
            class="group-item"
            @dragover="onDragOver"
            @drop="onDrop($event, groupIndex)"
          >
            <div class="group-header">
              <div class="group-name">
                <input 
                  type="text" 
                  class="group-name-input" 
                  v-model="group.name"
                  placeholder="分组名称"
                >
                <div class="color-picker">
                  <div 
                    v-for="color in colors" 
                    :key="color"
                    class="color-option"
                    :class="{ selected: group.color === color }"
                    :style="{ backgroundColor: color }"
                    @click="group.color = color"
                  >
                    <i class="material-icons" v-if="group.color === color">check</i>
                  </div>
                </div>
              </div>
              <div class="group-actions">
                <button 
                  class="action-btn btn-danger"
                  @click="removeGroup(groupIndex)"
                  :disabled="editingGroup.rules.length <= 1"
                >
                  <i class="material-icons">delete</i>
                </button>
              </div>
            </div>
            <div class="group-mice">
              <div 
                v-for="mouse in groupedMice[groupIndex]" 
                :key="mouse.tid"
                class="assigned-mouse"
              >
                <div class="mouse-id">{{ mouse.id }}</div>
                <div class="mouse-details" v-html="mouse.genotype.symbol"></div>
                <div class="mouse-details">{{ mouse.sex }} · {{ mouse.strain }} · {{ mouse.birth_date }}</div>
                <div class="mouse-actions">
                  <button 
                    class="action-btn btn-outline"
                    @click="removeMouseFromGroup(mouse.tid, groupIndex)"
                  >
                    <i class="material-icons">remove_circle</i>
                  </button>
                </div>
              </div>
              <div v-if="group.mouseId.length === 0" class="empty-group">
                暂无小鼠，请从左侧拖拽或选择添加
              </div>
            </div>
          </div>
        </div>
        
        <div class="grouping-actions">
          <button class="btn btn-outline" @click="addGroup">
            <i class="material-icons">add</i> 添加新分组
          </button>
          <button v-if="editingGroup.rules.length > 0" class="btn btn-outline" @click="resetGroup">
            <i class="material-icons">refresh</i> 重置分组
          </button>
          <button class="btn btn-success" @click="saving" :disabled="isSaving">
            <i class="material-icons">save</i> {{ isSaving? "保存中...": "保存ID分组" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// 定义props
const props = defineProps({
  candidateMice: {
    type: Array,
    default: () => []
  },
  editingGroup: {
    type: Object,
    default: () => ({ rules: [] })
  },
  colors: {
    type: Array,
    default: () => []
  }
})

// 定义emits
const emit = defineEmits(['update:editingGroup', 'save-group'])

// 使用ref创建本地数据
const searchTerm = ref('')
const selectedMouseIds = ref(new Set())
const isRepeated = ref(false)
const isSaving = ref(false)

// 计算属性
const filteredMice = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) {
    return props.candidateMice.filter(mouse => 
      !isMouseInAnyGroup(mouse.tid)
    )
  }
  return props.candidateMice.filter(mouse => {
    if (isMouseInAnyGroup(mouse.tid)) {
      return false
    }
    const searchableFields = [
      mouse.id || '',
      mouse.strain || '',
      mouse.sex || '',
      mouse.genotype.symbol || ''
    ]
    return searchableFields.some(field => 
      field.toLowerCase().includes(term)
    )
  })
})

const selectedMiceCount = computed(() => selectedMouseIds.value.size)

const isRepeatedAble = computed(() => {
  return props.editingGroup.rules.some(group => group.mouseId?.length>0)
})

const groupedMice = computed(() => {
  return props.editingGroup.rules.map(group => {
    return group.mouseId.map(mId => props.candidateMice.find(m => m.tid === mId))
  })
})

// 方法
const isMouseInAnyGroup = (mouseId) => {
  if (isRepeated.value) {
    return false
  } else {
    return props.editingGroup.rules.some(group => group.mouseId.includes(mouseId))
  }
}

const isMouseSelected = (mouseId) => {
  return selectedMouseIds.value.has(mouseId)
}

const toggleMouseSelection = (mouseId) => {
  if (selectedMouseIds.value.has(mouseId)) {
    selectedMouseIds.value.delete(mouseId)
  } else {
    selectedMouseIds.value.add(mouseId)
  }
}

const selectAllMice = () => {
  filteredMice.value.forEach(mouse => {
    selectedMouseIds.value.add(mouse.tid)
  })
}

const deselectAllMice = () => {
  selectedMouseIds.value.clear()
}

const removeMouseFromGroup = (mouseId, groupIndex) => {
  const mouseIndex = props.editingGroup.rules[groupIndex].mouseId.indexOf(mouseId)
  if (mouseIndex > -1) {
    props.editingGroup.rules[groupIndex].mouseId.splice(mouseIndex, 1)
    // 触发更新
    emit('update:editingGroup', { ...props.editingGroup })
  }
}

const onDragStart = (event, mId) => {
  if (!selectedMouseIds.value.has(mId)) {
    selectedMouseIds.value.add(mId);
  }
  const selectedMIs = Array.from(selectedMouseIds.value);
  event.dataTransfer.setData('application/json', JSON.stringify(selectedMIs));
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('text/plain', `移动 ${selectedMIs.length} 只小鼠`);
}

const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move';
  event.currentTarget.classList.add('drag-over');
}

const onDrop = (event, groupIndex) => {
  event.preventDefault()
  event.currentTarget.classList.remove('drag-over');
  try {
    const mouseIdsData = event.dataTransfer.getData('application/json');
    const mouseIds = JSON.parse(mouseIdsData);
    if (!Array.isArray(mouseIds) || mouseIds.length === 0) {
      console.error('无效的拖拽数据');
      return;
    }
    mouseIds.forEach(mouseId => {
      if (!isMouseInAnyGroup(mouseId)) {
        if (!props.editingGroup.rules[groupIndex].mouseId.includes(mouseId)) {
          props.editingGroup.rules[groupIndex].mouseId.push(mouseId);
        }
      }
    });
    selectedMouseIds.value.clear();
    // 触发更新
    emit('update:editingGroup', { ...props.editingGroup })
  } catch (error) {
    console.error('拖拽放置失败:', error);
  }
}

const addGroup = () => {
  const usedColors = new Set(props.editingGroup.rules.map(g => g.color))
  const availableColor = props.colors.find(color => !usedColors.has(color)) || props.colors[0]
  props.editingGroup.rules.push({name: `新分组${props.editingGroup.rules.length + 1}`, color: availableColor, mouseId: []})
  emit('update:editingGroup', { ...props.editingGroup })
}

const removeGroup = (index) => {
  props.editingGroup.rules.splice(index, 1)
  emit('update:editingGroup', { ...props.editingGroup })
}

const saving = () => {
  if (!props.editingGroup.name) {
    alert('请填写预设分组名称')
    return
  }
  if (props.editingGroup.rules.some(group => !group.name)) {
    alert('请填写分组名称')
    return
  }
  isSaving.value = true
  emit('save-group')
}

const resetGroup = () => {
  isSaving.value = false
  props.editingGroup.rules.forEach(group => {
    group.mouseId = []
  })
  emit('update:editingGroup', { ...props.editingGroup })
}
</script>

<style scoped>
.mouse-group-manager {
  width: 90%;
	max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 20px;
}

.section-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
  color: #2c3e50;
}

.id-grouping-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.candidate-mice, .grouping-section {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  background: #fafafa;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.candidate-mice h3, .grouping-section h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.selection-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.selection-info {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
}

.selection-buttons {
  display: flex;
  gap: 10px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-container {
  margin-bottom: 15px;
}

.mice-list {
	max-height: 300px;
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: white;
}

.mouse-item {
  display: flex;
  align-items: center;
  padding: 10px;
	gap: 10px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.mouse-item:hover {
  background-color: #f0f7ff;
}

.mouse-item.selected {
  background-color: #e3f2fd;
}

.mouse-checkbox {
  margin-right: 10px;
	margin: 0;
}

.mouse-info {
	font-size: 12px;
	color: #666;
	flex: 1;
	display: flex;
	gap: 10px;
	align-items: center;
}

.mouse-id {
  font-weight: 600;
  color: #2c3e50;
}

.mouse-details {
  font-size: 12px;
  color: #666;
  margin-top: 3px;
}

.groups-container {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: white;
  padding: 10px;
}

.group-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  margin-bottom: 15px;
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #e8f4fd;
  border-bottom: 1px solid #e0e0e0;
  border-radius: 6px 6px 0 0;
}

.group-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-name-input {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  min-width: 150px;
}

.group-actions {
  display: flex;
  gap: 5px;
}

.group-mice {
  padding: 10px;
  min-height: 100px;
  max-height: 200px;
  overflow-y: auto;
}

.assigned-mouse {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px;
  margin-bottom: 5px;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #2c6fbb;
}

.mouse-actions {
  display: flex;
  gap: 5px;
}

.empty-group {
  text-align: center;
  padding: 20px;
  color: #999;
  font-style: italic;
}

.grouping-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.drag-over {
  background-color: #f0f7ff;
  border: 2px dashed #2c6fbb;
}
</style>