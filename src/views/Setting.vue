<template>
<div class="main-content">
    <div class="content-header">
    <h1 class="page-title">系统设置</h1>
    </div>
    
    <!-- 标签页导航 -->
    <div class="section-tabs">
    <div 
        v-for="tab in tabs" 
        :key="tab.id" 
        class="tab-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
    >
        {{ tab.title }}
    </div>
    </div>
    
    <!-- 基因型设置 -->
    <div v-if="activeTab === 'genotype'" class="form-container">
    <h2 class="section-title">基因型设置</h2>
    
    <div class="form-section">
        <h3>新增基因型</h3>
        <form @submit.prevent="addGenotype" class="form-group-row">
        <div class="form-group">
            <label>基因型名称 *</label>
            <input type="text" v-model="newGenotype.name" placeholder="例如: C57BL/6J" required>
        </div>
        
        <div class="form-group">
            <label>描述</label>
            <input type="text" v-model="newGenotype.description" placeholder="例如: 野生型小鼠">
        </div>
        
        <div class="form-group">
            <button type="submit" class="btn btn-primary">添加基因型</button>
        </div>
        </form>
    </div>
    
    <div class="form-section">
        <h3>基因型列表</h3>
        <div class="table-container">
        <table class="settings-table">
            <thead>
            <tr>
                <th>基因型名称</th>
                <th>描述</th>
                <th>操作</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="genotype in genotypes" :key="genotype.id">
                <td>{{ genotype.name }}</td>
                <td>{{ genotype.description }}</td>
                <td class="action-cell">
                <button class="action-btn" @click="editGenotype(genotype)">编辑</button>
                <button class="btn-danger" @click="deleteGenotype(genotype.id)">删除</button>
                </td>
            </tr>
            </tbody>
        </table>
        </div>
    </div>
    </div>
    
    <!-- 位置设置 -->
    <div v-if="activeTab === 'location'" class="form-container">
    <h2 class="section-title">位置设置</h2>
    
    <div class="form-section">
        <h3>新增位置</h3>
        <form @submit.prevent="addLocation" class="form-group-row">
        <div class="form-group">
            <label>位置标识 *</label>
            <input type="text" v-model="newLocation.identifier" placeholder="例如: A-3-2" required>
        </div>
        
        <div class="form-group">
            <label>描述</label>
            <input type="text" v-model="newLocation.description" placeholder="例如: A区3排2号架">
        </div>
        
        <div class="form-group">
            <button type="submit" class="btn btn-primary">添加位置</button>
        </div>
        </form>
    </div>
    
    <div class="form-section">
        <h3>位置列表</h3>
        <div class="table-container">
        <table class="settings-table">
            <thead>
            <tr>
                <th>位置标识</th>
                <th>描述</th>
                <th>操作</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="location in locations" :key="location.id">
                <td>{{ location.identifier }}</td>
                <td>{{ location.description }}</td>
                <td class="action-cell">
                <button class="action-btn" @click="editLocation(location)">编辑</button>
                <button class="btn-danger" @click="deleteLocation(location.id)">删除</button>
                </td>
            </tr>
            </tbody>
        </table>
        </div>
    </div>
    </div>
    
    <!-- 导出设置 -->
    <div v-if="activeTab === 'export'" class="form-container">
    <h2 class="section-title">导出设置</h2>
    <p class="section-description">在此设置导出数据的相关选项</p>
    
    <div class="form-section">
        <h3>数据导出设置</h3>
        <div class="btn-group">
        <button class="btn btn-primary" @click="exportData('mice')">导出小鼠表</button>
        <button class="btn btn-primary" @click="exportData('weights')">导出体重表</button>
        <button class="btn btn-primary" @click="exportData('survival')">导出生存表</button>
        <button class="btn btn-primary" @click="exportData('records')">导出状态信息表</button>
        </div>
        
        <div v-if="exportOptionsVisible" class="export-options">
        <div v-if="currentExportType !== 'survival'" class="form-group">
            <label>时间范围</label>
            <div class="date-range">
            <input type="date" v-model="exportStartDate">
            <span>至</span>
            <input type="date" v-model="exportEndDate">
            </div>
        </div>
        
        <div class="form-group">
            <label>文件格式</label>
            <select v-model="exportFormat">
            <option value="csv">CSV</option>
            <option value="xlsx">Excel</option>
            </select>
        </div>
        
        <div class="form-group">
            <button class="btn btn-primary" @click="confirmExport">确认导出</button>
        </div>
        </div>
    </div>
    </div>
    
    <!-- 导入小鼠 -->
    <div v-if="activeTab === 'import'" class="form-container">
    <h2 class="section-title">导入数据</h2>
    <p class="section-description">从Excel文件导入小鼠数据</p>
    
    <div class="form-section">
        <h3>选择Excel文件</h3>
        <div class="file-upload" @dragover.prevent @drop="handleDrop">
        <input type="file" accept=".xlsx, .xls" @change="handleFileUpload">
        <div class="upload-area" :class="{ 'dragover': isDragging }">
            <i class="material-icons">cloud_upload</i>
            <p v-if="!selectedFile">点击或拖拽Excel文件到此处上传</p>
            <p v-else class="file-info">
            <span>{{ selectedFile.name }}</span>
            <span>({{ formatFileSize(selectedFile.size) }})</span>
            </p>
            <button v-if="selectedFile" class="btn btn-outline" @click="clearFile">清除</button>
        </div>
        </div>
        
        <div v-if="selectedFile" class="import-options">
        <div class="form-group">
            <label>导入类型</label>
            <select v-model="importType">
            <option value="mice">小鼠信息</option>
            <option value="weights">体重数据</option>
           <!-- <option value="pedigree">血统关系</option>功能尚未实现 -->
            </select>
        </div>
        
        <div class="form-group">
            <label>处理重复数据</label>
            <select v-model="importConflictResolution">
            <option value="skip">跳过重复项</option>
            <option value="overwrite">覆盖现有数据</option>
            </select>
        </div>
        
        <div class="form-group">
            <button class="btn btn-primary" @click="importData" :disabled="isImporting">
            <span v-if="isImporting">导入中...</span>
            <span v-else>开始导入</span>
            </button>
        </div>

        <!-- 数据格式提示 - 根据导入类型动态显示 -->
        <div class="format-hint">
            <h4>
                <i class="material-icons">info</i>
                数据格式要求 - {{ importType === 'mice' ? '小鼠信息' : importType === 'weights' ? '体重数据' : '血统关系' }}
            </h4>
            
            <!-- 小鼠信息导入格式 -->
            <div v-if="importType === 'mice'">
                <table class="format-table">
                    <thead>
                        <tr>
                            <th>列名</th>
                            <th>数据类型</th>
                            <th>是否必填</th>
                            <th>说明</th>
                            <th>示例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="required">id</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>小鼠唯一标识</td>
                            <td class="example-row">M001</td>
                        </tr>
                        <tr>
                            <td><span class="required">genotype</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>基因型描述</td>
                            <td class="example-row">C57BL/6</td>
                        </tr>
                        <tr>
                            <td><span class="required">sex</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>性别（M/F）</td>
                            <td class="example-row">M</td>
                        </tr>
                        <tr>
                            <td><span class="required">birth_date</span></td>
                            <td>日期</td>
                            <td><span class="required">是</span></td>
                            <td>出生日期（YYYY-MM-DD）</td>
                            <td class="example-row">2023-05-15</td>
                        </tr>
                        <tr>
                            <td><span class="required">live_status</span></td>
                            <td>整数</td>
                            <td><span class="required">是</span></td>
                            <td>存活状态（1=存活，0=死亡）</td>
                            <td class="example-row">1</td>
                        </tr>
                        <tr>
                            <td><span class="optional">death_date</span></td>
                            <td>日期</td>
                            <td><span class="optional">否</span></td>
                            <td>死亡日期（当live_status=0时必填）</td>
                            <td class="example-row">2023-10-20</td>
                        </tr>
                        <tr>
                            <td><span class="optional">cage_id</span></td>
                            <td>字符串</td>
                            <td><span class="optional">否</span></td>
                            <td>笼位编号</td>
                            <td class="example-row">CAGE-01</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="note">
                    <div class="note-title">重要提示：</div>
                    <div class="note-content">
                        <p>1. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
                        <p>2. 性别字段只接受'M'（雄性）或'F'（雌性）</p>
                        <p>3. 基因型如果不存在会自动创建新基因型</p>
                        <p>4. 当live_status=0（死亡）时，必须提供death_date</p>
                    </div>
                </div>
            </div>
            
            <!-- 体重数据导入格式 -->
            <div v-if="importType === 'weights'">
                <table class="format-table">
                    <thead>
                        <tr>
                            <th>列名</th>
                            <th>数据类型</th>
                            <th>是否必填</th>
                            <th>说明</th>
                            <th>示例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="required">id</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>小鼠唯一标识</td>
                            <td class="example-row">M001</td>
                        </tr>
                        <tr>
                            <td><span class="required">birth_date</span></td>
                            <td>日期</td>
                            <td><span class="required">是</span></td>
                            <td>出生日期（YYYY-MM-DD）</td>
                            <td class="example-row">2023-05-15</td>
                        </tr>
                        <tr>
                            <td><span class="required">weight</span></td>
                            <td>数值</td>
                            <td><span class="required">是</span></td>
                            <td>体重值（克）</td>
                            <td class="example-row">25.3</td>
                        </tr>
                        <tr>
                            <td><span class="required">record_date</span></td>
                            <td>日期</td>
                            <td><span class="required">是</span></td>
                            <td>记录日期（YYYY-MM-DD）</td>
                            <td class="example-row">2023-06-15</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="note">
                    <div class="note-title">重要提示：</div>
                    <div class="note-content">
                        <p>1. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
                        <p>2. 体重值应为数值类型，最多保留两位小数</p>
                        <p>3. 记录日期必须晚于出生日期</p>
                        <p>4. 系统会自动计算生存天数 = (记录日期 - 出生日期)</p>
                    </div>
                </div>
            </div>
            
            <!-- 血统关系导入格式 -->
            <div v-if="importType === 'pedigree'">
                <table class="format-table">
                    <thead>
                        <tr>
                            <th>列名</th>
                            <th>数据类型</th>
                            <th>是否必填</th>
                            <th>说明</th>
                            <th>示例</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="required">mouse_id</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>小鼠唯一标识</td>
                            <td class="example-row">M001</td>
                        </tr>
                        <tr>
                            <td><span class="required">birth_date</span></td>
                            <td>日期</td>
                            <td><span class="required">是</span></td>
                            <td>出生日期（YYYY-MM-DD）</td>
                            <td class="example-row">2023-05-15</td>
                        </tr>
                        <tr>
                            <td><span class="required">father_id</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>父鼠ID（如不存在填'None'）</td>
                            <td class="example-row">F001</td>
                        </tr>
                        <tr>
                            <td><span class="required">mother_id</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>母鼠ID（如不存在填'None'）</td>
                            <td class="example-row">M002</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="note">
                    <div class="note-title">重要提示：</div>
                    <div class="note-content">
                        <p>1. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
                        <p>2. 父鼠ID和母鼠ID如不存在，必须填写字符串'None'（区分大小写）</p>
                        <p>3. 所有小鼠ID必须已在系统中存在</p>
                        <p>4. 父鼠和母鼠的出生日期必须早于当前小鼠的出生日期</p>
                    </div>
                </div>
            </div>
        </div>  
        </div>
    </div>
    </div>
    
    <!-- 编辑基因型对话框 -->
    <div v-if="editGenotypeDialogVisible" class="dialog-overlay">
    <div class="dialog-container">
        <h2>编辑基因型</h2>
        <div class="form-group">
        <label>基因型名称</label>
        <input type="text" v-model="editingGenotype.name" required>
        </div>
        <div class="form-group">
        <label>描述</label>
        <input type="text" v-model="editingGenotype.description">
        </div>
        <div class="dialog-buttons">
        <button class="btn btn-outline" @click="editGenotypeDialogVisible = false">取消</button>
        <button class="btn btn-primary" @click="saveGenotype">保存</button>
        </div>
    </div>
    </div>
    
    <!-- 编辑位置对话框 -->
    <div v-if="editLocationDialogVisible" class="dialog-overlay">
    <div class="dialog-container">
        <h2>编辑位置</h2>
        <div class="form-group">
        <label>位置标识</label>
        <input type="text" v-model="editingLocation.identifier" required>
        </div>
        <div class="form-group">
        <label>描述</label>
        <input type="text" v-model="editingLocation.description">
        </div>
        <div class="dialog-buttons">
        <button class="btn btn-outline" @click="editLocationDialogVisible = false">取消</button>
        <button class="btn btn-primary" @click="saveLocation">保存</button>
        </div>
    </div>
    </div>
    
    <!-- 导入结果对话框 -->
    <div v-if="importResultDialogVisible" class="dialog-overlay">
    <div class="dialog-container">
        <h2>导入结果</h2>
        <div class="import-result">
        <div class="result-item success">
            <i class="material-icons">check_circle</i>
            <span>成功导入: {{ importResult.successCount }} 条记录</span>
        </div>
        <div class="result-item warning">
            <i class="material-icons">warning</i>
            <span>跳过重复: {{ importResult.skippedCount }} 条记录</span>
        </div>
        <div class="result-item error" v-if="importResult.errors.length > 0">
            <i class="material-icons">error</i>
            <span>错误: {{ importResult.errors.length }} 条记录</span>
        </div>
        
        <div v-if="importResult.errors.length > 0" class="error-details">
            <h4>错误详情:</h4>
            <ul>
            <li v-for="(error, index) in importResult.errors" :key="index">
                行 {{ error.row }}: {{ error.message }}
            </li>
            </ul>
        </div>
        </div>
        <div class="dialog-buttons">
        <button class="btn btn-primary" @click="importResultDialogVisible = false">确定</button>
        </div>
    </div>
    </div>
</div>
</template>

<script>
import axios from 'axios';

export default {
name: 'SystemSettings',
data() {
    return {
    activeTab: 'genotype',
    tabs: [
        { id: 'genotype', title: '基因型设置' },
        { id: 'location', title: '位置设置' },
        { id: 'export', title: '导出设置' },
        { id: 'import', title: '导入数据' }
    ],
    newGenotype: {
        name: '',
        description: ''
    },
    genotypes: [],
    newLocation: {
        identifier: '',
        description: ''
    },
    locations: [],
    editingGenotype: {
        id: null,
        name: '',
        description: ''
    },
    editGenotypeDialogVisible: false,
    editingLocation: {
        id: null,
        identifier: '',
        description: ''
    },
    editLocationDialogVisible: false,
    
    // 导出设置
    exportOptionsVisible: false,
    exportStartDate: '',
    exportEndDate: '',
    exportFormat: 'xlsx',
    currentExportType: '',
    
    // 导入设置
    selectedFile: null,
    isDragging: false,
    importType: 'mice',
    importConflictResolution: 'skip',
    isImporting: false,
    importResultDialogVisible: false,
    importResult: {
        successCount: 0,
        skippedCount: 0,
        errors: []
    }
    };
},
mounted() {
    this.fetchGenotypes();
    this.fetchLocations();
    
},
methods: {
    fetchGenotypes() {
    axios.get('/api/genotypes')
        .then(response => {
        this.genotypes = response.data;
        })
        .catch(error => {
        console.error('获取基因型列表失败:', error);
        alert('获取基因型列表失败');
        });
    },
    
    addGenotype() {
    if (!this.newGenotype.name) {
        alert('请填写基因型名称');
        return;
    }
    
    axios.post('/api/genotypes', this.newGenotype)
        .then(response => {
        this.genotypes.push(response.data);
        this.newGenotype = { name: '', description: '' };
        })
        .catch(error => {
        console.error('添加基因型失败:', error);
        alert('添加基因型失败，请重试');
        });
    },
    
    editGenotype(genotype) {
    this.editingGenotype = { ...genotype };
    this.editGenotypeDialogVisible = true;
    },
    
    saveGenotype() {
    axios.put(`/api/genotypes/${this.editingGenotype.id}`, this.editingGenotype)
        .then(response => {
        const index = this.genotypes.findIndex(g => g.id === this.editingGenotype.id);
        if (index !== -1) {
            this.genotypes[index] = response.data;
        }
        this.editGenotypeDialogVisible = false;
        })
        .catch(error => {
        console.error('更新基因型失败:', error);
        alert('更新基因型失败，请重试');
        });
    },
    
    deleteGenotype(id) {
    if (!confirm('确定要删除这个基因型吗？')) return;
    
    axios.delete(`/api/genotypes/${id}`)
        .then(() => {
        this.genotypes = this.genotypes.filter(g => g.id !== id);
        })
        .catch(error => {
        console.error('删除基因型失败:', error);
        alert('删除基因型失败，请重试');
        });
    },
    
    fetchLocations() {
    axios.get('/api/locations')
        .then(response => {
        this.locations = response.data;
        })
        .catch(error => {
        console.error('获取位置列表失败:', error);
        alert('获取位置列表失败');
        });
    },
    
    addLocation() {
    if (!this.newLocation.identifier) {
        alert('请填写位置标识');
        return;
    }
    
    axios.post('/api/locations', this.newLocation)
        .then(response => {
        this.locations.push(response.data);
        this.newLocation = { identifier: '', description: '' };
        })
        .catch(error => {
        console.error('添加位置失败:', error);
        alert('添加位置失败，请重试');
        });
    },
    
    editLocation(location) {
    this.editingLocation = { ...location };
    this.editLocationDialogVisible = true;
    },
    
    saveLocation() {
    axios.put(`/api/locations/${this.editingLocation.id}`, this.editingLocation)
        .then(response => {
        const index = this.locations.findIndex(l => l.id === this.editingLocation.id);
        if (index !== -1) {
            this.locations[index] = response.data;
        }
        this.editLocationDialogVisible = false;
        })
        .catch(error => {
        console.error('更新位置失败:', error);
        alert('更新位置失败，请重试');
        });
    },
    
    deleteLocation(id) {
    if (!confirm('确定要删除这个位置吗？')) return;
    
    axios.delete(`/api/locations/${id}`)
        .then(() => {
        this.locations = this.locations.filter(l => l.id !== id);
        })
        .catch(error => {
        console.error('删除位置失败:', error);
        alert('删除位置失败，请重试');
        });
    },
    
    exportData(type) {
    this.currentExportType = type;
    this.exportOptionsVisible = true;
    },
    
    confirmExport() {
    const params = {
        start_date: this.exportStartDate,
        end_date: this.exportEndDate,
        format: this.exportFormat
    };
    
    axios.get(`/api/export/${this.currentExportType}`, { 
        params,
        responseType: 'blob'
    })
    .then(response => {
        // 使用 PyWebview 的保存文件对话框
        if (window.pywebview && window.pywebview.api) {
            // 创建默认文件名
            const filename = `${this.currentExportType}_export.${this.exportFormat}`;
            
            response.data.arrayBuffer().then(arrayBuffer => {
                const uint8array = new Uint8Array(arrayBuffer);
                const dataArray = Array.from(uint8array);
                // 调用 PyWebview API 保存文件
                window.pywebview.api.save_file_dialog(dataArray, filename).then(() => {
                    this.exportOptionsVisible = false;
                });
            });
        } else {
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${this.currentExportType}_export.${this.exportFormat}`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.exportOptionsVisible = false;
        }
    })
    .catch(error => {
        console.error('导出数据失败:', error);
        alert('导出数据失败，请重试');
    });
    },
    
    handleFileUpload(event) {
    this.selectedFile = event.target.files[0];
    event.target.value = null; // 重置input，允许再次选择相同文件
    },
    
    handleDrop(event) {
    event.preventDefault();
    this.isDragging = false;
    
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
        this.selectedFile = event.dataTransfer.files[0];
    }
    },
    
    clearFile() {
    this.selectedFile = null;
    },
    
    formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    importData() {
        if (!this.selectedFile) {
            alert('请选择要导入的文件');
            return;
        }
        
        this.isImporting = true;
        
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('type', this.importType);
        formData.append('conflict_resolution', this.importConflictResolution);
        
        axios.post('/api/import', formData, {
            headers: {
            'Content-Type': 'multipart/form-data'
            }
        })
        .then(response => {
            this.importResult = response.data;
            this.importResultDialogVisible = true;
            this.isImporting = false;
        })
        .catch(error => {
            console.error('导入失败:', error);
            alert(`导入失败: ${error.response?.data?.error || '服务器错误'}`);
            this.isImporting = false;
        });
    }
}
};
</script>

<style scoped>
/* 使用与Dashboard.vue相同的样式变量 */
:root {
--primary: #2c6fbb;
--secondary: #4CAF50;
--danger: #f44336;
--warning: #FF9800;
--light: #f8f9fa;
--dark: #343a40;
--border: #dee2e6;
--header-height: 60px;
--footer-height: 25px;
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
}

.section-tabs {
display: flex;
border-bottom: 1px solid #e0e0e0;
margin-bottom: 25px;
padding: 0 10px;
}

.tab-item {
padding: 10px 20px;
cursor: pointer;
margin-right: 5px;
border-radius: 5px 5px 0 0;
font-weight: 500;
color: #666;
transition: all 0.2s ease;
}

.tab-item:hover {
background-color: #f5f5f5;
}

.tab-item.active {
color: var(--primary);
background-color: rgba(25, 118, 210, 0.08);
border-bottom: 2px solid var(--primary);
}

.form-container {
background: white;
padding: 20px;
border-radius: 8px;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section-title {
font-size: 1.3rem;
font-weight: 600;
margin-bottom: 15px;
padding-bottom: 10px;
border-bottom: 1px solid #eee;
}

.section-description {
color: #666;
margin-bottom: 20px;
}

.form-section {
margin-bottom: 30px;
}

.form-section h3 {
font-size: 1.1rem;
margin-bottom: 15px;
color: #333;
font-weight: 500;
}

.form-group-row {
display: flex;
flex-wrap: wrap;
gap: 15px;
margin-bottom: 20px;
}

.form-group {
flex: 1;
min-width: 250px;
}

.form-group label {
display: block;
margin-bottom: 8px;
font-weight: 500;
color: #444;
}

.form-group input, .form-group select {
width: 100%;
padding: 10px;
border: 1px solid #ddd;
border-radius: 4px;
font-size: 14px;
}

.form-group input:focus, .form-group select:focus {
border-color: var(--primary);
outline: none;
box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.btn {
padding: 8px 16px;
border-radius: 4px;
border: none;
cursor: pointer;
display: inline-flex;
align-items: center;
font-size: 14px;
transition: background-color 0.2s;
}

.btn-primary {
background-color: var(--primary);
color: white;
}

.btn-primary:hover {
background-color: #1a56b4;
}

.btn-outline {
background-color: transparent;
border: 1px solid var(--primary);
color: var(--primary);
}

.btn-outline:hover {
background-color: rgba(25, 118, 210, 0.1);
}

.btn-danger {
padding: 6px 12px;
background-color: #e53935;
border: 1px solid #ddd;
border-radius: 4px;
cursor: pointer;
font-size: 13px;
transition: all 0.2s;
color: white;
margin-left: 8px;
}

.btn-danger:hover {
background-color: #c62828;
}

.table-container {
overflow-x: auto;
}

.settings-table {
width: 100%;
border-collapse: collapse;
margin-top: 15px;
}

.settings-table th, 
.settings-table td {
padding: 12px 15px;
text-align: left;
border-bottom: 1px solid #eee;
}

.settings-table th {
background-color: #f8f9fa;
font-weight: 600;
position: sticky;
top: 0;
}

.settings-table tbody tr:hover {
background-color: #f5f7fa;
}

.action-cell {
white-space: nowrap;
}

.action-btn {
padding: 6px 12px;
background-color: #f5f5f5;
border: 1px solid #ddd;
border-radius: 4px;
cursor: pointer;
font-size: 13px;
transition: all 0.2s;
}

.action-btn:hover {
background-color: #e0e0e0;
}

.btn-group {
display: flex;
gap: 15px;
margin-top: 20px;
}

.file-upload {
margin-top: 15px;
}

.file-upload input[type="file"] {
display: none;
}

.upload-area {
border: 2px dashed #ccc;
border-radius: 8px;
padding: 30px;
text-align: center;
cursor: pointer;
transition: all 0.3s;
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
min-height: 150px;
}

.upload-area.dragover {
border-color: var(--primary);
background-color: rgba(25, 118, 210, 0.05);
}

.upload-area i {
font-size: 48px;
color: #888;
margin-bottom: 15px;
}

.upload-area p {
color: #666;
margin: 5px 0;
}

.file-info {
display: flex;
flex-direction: column;
align-items: center;
margin-top: 10px;
}

.file-info span:first-child {
font-weight: 500;
margin-bottom: 5px;
}

.import-options, .export-options {
margin-top: 20px;
padding: 15px;
background-color: #f9f9f9;
border-radius: 8px;
}

.date-range {
display: flex;
align-items: center;
gap: 10px;
}

.date-range input {
flex: 1;
}

.dialog-overlay {
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background-color: rgba(0, 0, 0, 0.5);
display: flex;
justify-content: center;
align-items: center;
z-index: 1000;
}

.dialog-container {
background-color: white;
padding: 25px;
border-radius: 8px;
width: 450px;
max-width: 90%;
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.dialog-container h2 {
margin-top: 0;
margin-bottom: 20px;
font-size: 1.3rem;
}

.dialog-buttons {
display: flex;
justify-content: flex-end;
gap: 10px;
margin-top: 20px;
}

.import-result {
margin: 15px 0;
}

.result-item {
display: flex;
align-items: center;
padding: 10px;
border-radius: 4px;
margin-bottom: 10px;
}

.format-hint {
    background: #f0f7ff;
    border-left: 4px solid #4a6fa5;
    border-radius: 4px;
    padding: 20px;
    margin-top: 25px;
    margin-bottom: 20px;
}

.format-hint h4 {
    color: #2c3e50;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
}

.format-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
    font-size: 14px;
}

.format-table th {
    background: #e6f0ff;
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    color: #2c3e50;
    border-bottom: 1px solid #d1d8e0;
}

.format-table td {
    padding: 12px 15px;
    border-bottom: 1px solid #eef2f7;
}

.format-table tr:nth-child(even) {
    background: #f9fbfd;
}

.format-table tr:hover {
    background: #f0f7ff;
}

.required {
    color: #e74c3c;
    font-weight: 600;
}

.optional {
    color: #7f8c8d;
}

.note {
    margin-top: 15px;
    padding: 15px;
    background: #fff8e6;
    border-left: 4px solid #ffc107;
    border-radius: 4px;
    font-size: 14px;
}

.note-title {
    font-weight: 600;
    margin-bottom: 5px;
    color: #2c3e50;
}

.note-content {
    color: #7f8c8d;
}

.note-content p {
    margin-bottom: 5px;
}

.example-row {
    font-family: monospace;
    font-size: 14px;
    color: #4a6fa5;
}
</style>