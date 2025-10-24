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
    <h2 class="section-title">基因型管理系统</h2>
    
    <!-- 添加新基因位点 -->
    <div class="form-section">
        <h3>添加新基因位点</h3>
        <form @submit.prevent="addGeneLocus" class="form-group-row">
        <div class="form-group">
            <label>基因组位点 *</label>
            <input type="text" v-model="newGeneLocus.symbol" placeholder="例如: TP53" required>
        </div>
        
        <div class="form-group">
            <label>描述</label>
            <input type="text" v-model="newGeneLocus.description" placeholder="例如: 该基因编码一种肿瘤抑制蛋白，含有转录激活、DNA结合和寡聚化结构域。编码的蛋白能响应多种细胞应激，调控靶基因的表达，从而诱导细胞周期阻滞、凋亡、衰老、DNA修复或代谢变化。">
        </div>
        
        <div class="form-group">
            <button type="submit" class="btn btn-primary">添加基因位点</button>
        </div>
        </form>
    </div>
    
    <!-- 基因位点与等位基因表格 -->
    <div class="form-section">
        <h3>基因位点与等位基因</h3>
        <div class="table-container">
        <table class="settings-table">
            <thead>
            <tr>
                <th>基因符号</th>
                <th>描述</th>
                <th>等位基因数量</th>
                <th>操作</th>
            </tr>
            </thead>
            <tbody>
            <template v-for="locus in genotypes" :key="locus.id">
                <!-- 基因位点行 -->
                <tr class="locus-row">
                <td>{{ locus.symbol }}</td>
                <td>{{ locus.description }}</td>
                <td>{{ locus.alleles.length }}</td>
                <td class="action-cell">
                    <button class="action-btn" @click="editGeneLocus(locus)">编辑</button>
                    <button class="action-btn btn-danger" @click="deleteGeneLocus(locus.id)">删除</button>
                    <button v-if="locus.symbol !== 'WT'" class="action-btn btn-success" @click="toggleAlleles(locus.id)">
                    {{ expandedLoci.includes(locus.id) ? '收起' : '展开' }}
                    </button>
                </td>
                </tr>
                
                <!-- 等位基因子表格 -->
                <tr v-if="expandedLoci.includes(locus.id)" class="alleles-subtable">
                <td colspan="4">
                    <div class="subtable-container">
                    <table class="subtable">
                        <thead>
                        <tr>
                            <th>等位基因符号</th>
                            <th>描述</th>
                            <th>是否为野生型</th>
                            <th>操作</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr v-for="allele in locus.alleles" :key="allele.id">
                            <td>{{ allele.symbol }}</td>
                            <td>{{ allele.description }}</td>
                            <td>{{ allele.is_wildtype ? '是' : '否' }}</td>
                            <td class="action-cell">
                            <button class="action-btn" @click="editAllele(allele)">编辑</button>
                            <button class="action-btn btn-danger" @click="deleteAllele(allele.id)">删除</button>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    
                    <!-- 添加新等位基因表单 -->
                    <div class="add-allele-form">
                        <h4>添加新等位基因</h4>
                        <form @submit.prevent="addAllele(locus.id)" class="form-group-row">
                        <div class="form-group">
                            <label>符号 *</label>
                            <input type="text" v-model="newAllele.symbol" placeholder="例如: KO" required>
                        </div>
                        
                        <div class="form-group">
                            <label>描述</label>
                            <input type="text" v-model="newAllele.description" placeholder="例如: 基因敲除">
                        </div>
                        
                        <div class="form-group">
                            <label>是否为野生型</label>
                            <input type="checkbox" v-model="newAllele.is_wildtype"> 
                        </div>
                        
                        <div class="form-group">
                            <button type="submit" class="btn btn-primary">添加</button>
                        </div>
                        </form>
                    </div>
                    </div>
                </td>
                </tr>
            </template>
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
                <button class="action-btn btn-danger" @click="deleteLocation(location.id)">删除</button>
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
            <button class="btn btn-primary" 
                v-for="option in exportOptions" 
                :key="option.id" @click="exportData(option.id)" 
                :class="{ active: currentExportType === option.id }">
                    {{ option.title }}
            </button>
        </div>
        
        <div v-if="exportOptionsVisible" class="export-options">
        <div v-if="currentExportType !== 'survival' && currentExportType !== 'experiment'" class="form-group">
            <label>时间范围</label>
            <div class="date-range">
            <input type="date" v-model="exportStartDate">
            <span>至</span>
            <input type="date" v-model="exportEndDate">
            </div>
        </div>
        <table class="settings-table" v-if="currentExportType === 'experiment'" >
            <thead>
                <tr>
                <th>实验类型名称</th>
                <th>描述</th>
                <th>字段数量</th>
                <th>操作</th>
                </tr>
            </thead>
            <tbody>
            <template v-for="experimentType in experimentTypes" :key="experimentType.id">
                <tr :class="{ selected: selectedExperiments.includes(experimentType.id) }">
                    <td>{{ experimentType.name }}</td>
                    <td>{{ experimentType.description }}</td>
                    <td>{{ experimentType.fields ? experimentType.fields.length : 0 }}</td>
                    <td class="action-cell">
                        <button class="action-btn btn-info" @click="toggleSelect(experimentType.id)">
                            {{ selectedExperiments.includes(experimentType.id) ? '取消' : '选择' }}
                        </button>
                    </td>
                </tr>
            </template>
            </tbody>   
        </table> 
        <div class="form-group">
            <label>文件格式</label>
            <select v-model="exportFormat">
            <option v-if="currentExportType !== 'experiment'" value="csv">CSV</option>
            <option value="xlsx">Excel</option>
            </select>
        </div>
        
        <div class="form-group">
            <button class="btn btn-primary" @click="confirmExport">确认导出</button>
        </div>
        </div>
    </div>
    </div>
    
    <!-- 导入设置 -->
    <div v-if="activeTab === 'import'" class="form-container">
    <h2 class="section-title">导入数据</h2>
    <p class="section-description">从Excel文件导入小鼠数据</p>
    
    <div class="form-section">
        <div class="import-options">
            <div class="form-group">
                <label>导入类型</label>
                <select v-model="importType">
                    <option value="mice">小鼠信息</option>
                    <option value="weights">体重数据</option>
                    <option value="record">小鼠状态记录数据</option>
                    <!-- <option value="pedigree">血统关系</option>功能尚未实现 -->
                </select>
            </div>
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
            <div v-if="selectedFile" class="form-group">
                <label>处理重复数据</label>
                <select v-model="importConflictResolution">
                <option value="skip">跳过重复项</option>
                <option value="overwrite">覆盖现有数据</option>
                </select>
            </div>
            <div v-if="selectedFile" class="form-group">
                <button class="btn btn-primary" @click="importData" :disabled="isImporting">
                <span v-if="isImporting">导入中...</span>
                <span v-else>开始导入</span>
                </button>
            </div>
        </div>
        <!-- 数据格式提示 - 根据导入类型动态显示 -->
        <div class="format-hint">
            <h4>
                <i class="material-icons">info</i>
                数据格式要求 - {{ importType === 'mice' ? '小鼠信息' : importType === 'weights' ? '体重数据' : importType === 'record' ? '小鼠状态记录数据' : '血统关系' }}
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
                            <td>存活状态（1=存活，0=死亡，2=解剖，3=失踪，4=丢弃，5=处理后死亡）</td>
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
                            <td>笼位名称</td>
                            <td class="example-row">CAGE-01</td>
                        </tr>
                        <tr>
                            <td><span class="optional">location</span></td>
                            <td>字符串</td>
                            <td><span class="optional">否</span></td>
                            <td>区域名称</td>
                            <td class="example-row">本部动物房</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="note">
                    <div class="note-title">重要提示：</div>
                    <div class="note-content">
                        <p>1. 列名一定要按照要求填写，否则无法识别</p>
                        <p>2. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
                        <p>3. 性别字段只接受'M'（雄性）或'F'（雌性）</p>
                        <p>4. 基因型如果不存在会自动创建新基因型</p>
                        <p>5. 当live_status!=1（不为存活）时，必须提供death_date</p>
                        <p>6. 区域名称只有在存在笼位名称时才生效</p>
                        <p>7. 若无区域名称，新笼位自动添加到新创建的区域，后续可调整（通过笼位设置）</p>
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
                        <p>1. 列名一定要按照要求填写，否则无法识别</p>
                        <p>2. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
                        <p>3. 体重值应为数值类型，最多保留两位小数</p>
                        <p>4. 记录日期必须晚于出生日期</p>
                        <p>5. 系统会自动计算生存天数 = (记录日期 - 出生日期)</p>
                    </div>
                </div>
            </div>

            <!-- 状态数据导入格式 -->
            <div v-if="importType === 'record'">
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
                            <td><span class="required">record</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>每条记录</td>
                            <td class="example-row">脱毛</td>
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
                        <p>1. 列名一定要按照要求填写，否则无法识别</p>
                        <p>2. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
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
                        <p>1. 列名一定要按照要求填写，否则无法识别</p>
                        <p>2. 日期格式必须为YYYY-MM-DD（例如：2023-05-15）</p>
                        <p>3. 父鼠ID和母鼠ID如不存在，必须填写字符串'None'（区分大小写）</p>
                        <p>4. 所有小鼠ID必须已在系统中存在</p>
                        <p>5. 父鼠和母鼠的出生日期必须早于当前小鼠的出生日期</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </div>

    <!-- 实验类型设置 -->
    <div v-if="activeTab === 'experiment'" class="form-container">
        <h2 class="section-title">实验类型设置</h2>
        
        <div class="form-section">
            <h3>可选择预设实验类型</h3>
            <div class="preset-selector">
            <label>选择预设：</label>
            <select v-model="selectedPreset" @change="applyPreset">
                <option value="">-- 请选择预设 --</option>
                <option v-for="(preset, key) in experimentPresets" :key="key" :value="key">
                {{ preset.name }}
                </option>
            </select>
            <span class="preset-description" v-if="selectedPreset">
                {{ experimentPresets[selectedPreset].description }}
            </span>
            </div>
        </div>
        
        <div class="form-section">
        <h3>{{ editingExperimentType.id ? '编辑实验类型' : '新增实验类型' }}</h3>
        <form @submit.prevent="saveExperimentType" class="form-group-row">
            <div class="form-group">
            <label>实验类型名称 *</label>
            <input type="text" v-model="editingExperimentType.name" placeholder="例如: 肿瘤测量" required>
            </div>
            
            <div class="form-group">
            <label>描述</label>
            <input type="text" v-model="editingExperimentType.description" placeholder="例如: 测量裸鼠肿瘤尺寸">
            </div>
            
            <div class="form-group">
            <button type="submit" class="btn btn-primary">
                {{ editingExperimentType.id ? '更新' : '添加' }}
            </button>
            <button v-if="editingExperimentType.id" type="button" class="btn btn-outline" @click="cancelEdit">
                取消
            </button>
            <button type="button" class="btn btn-outline" @click="resetForm">
                重置表单
            </button>
            </div>
        </form>
        
        <div class="fields-section">
            <h4>字段定义</h4>
            <div class="table-container">
            <table class="settings-table">
                <thead>
                <tr>
                    <th>字段名称</th>
                    <th>数据类型</th>
                    <th>单位</th>
                    <th>必填</th>
                    <th>可视化</th>
                    <th>操作</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="(field, index) in editingExperimentType.fields" :key="index">
                    <td>
                    <input type="text" v-model="field.field_name" placeholder="字段名称" required>
                    </td>
                    <td>
                    <select v-model="field.data_type" required>
                        <option value="INTEGER">整数</option>
                        <option value="REAL">小数</option>
                        <option value="TEXT">文本</option>
                        <option value="BOOLEAN">布尔值</option>
                        <option value="DATE">日期</option>
                    </select>
                    </td>
                    <td>
                    <input type="text" v-model="field.unit" placeholder="单位">
                    </td>
                    <td>
                    <input type="checkbox" v-model="field.is_required">
                    </td>
                    <td>
                    <select v-model="field.visualize_type" required>
                        <option value="">不进行可视化</option>
                        <option v-if="field.data_type === 'INTEGER' || 'REAL' || 'DATE'" value="x">作为横坐标</option>
                        <option v-if="field.data_type === 'INTEGER' || 'REAL'" value="y">作为纵坐标</option>
                        <option v-if="field.data_type === 'INTEGER' || 'REAL'" value="column">作为柱状图</option>
                    </select>
                    </td>
                    <td class="action-cell">
                        <button class="action-btn btn-danger" @click="removeField(index)">
                        <i class="material-icons">delete</i>
                        </button>
                        <button class="action-btn btn-outline" @click="moveFieldUp(index)" :disabled="index === 0">
                        <i class="material-icons">arrow_upward</i>
                        </button>
                        <button class="action-btn btn-outline" @click="moveFieldDown(index)" :disabled="index === editingExperimentType.fields.length - 1">
                        <i class="material-icons">arrow_downward</i>
                        </button>
                    </td>
                </tr>
                </tbody>
            </table>
            </div>
            
            <div class="field-actions">
            <button class="btn btn-outline" @click="addField">
                <i class="material-icons">add</i> 添加字段
            </button>
            </div>
        </div>
        </div>
        
        <div class="form-section">
        <h3>实验类型列表</h3>
        <div class="table-container">
            <table class="settings-table">
            <thead>
                <tr>
                <th>实验类型名称</th>
                <th>描述</th>
                <th>字段数量</th>
                <th>操作</th>
                </tr>
            </thead>
            <tbody>
            <template v-for="experimentType in experimentTypes" :key="experimentType.id">
                <tr>
                    <td>{{ experimentType.name }}</td>
                    <td>{{ experimentType.description }}</td>
                    <td>{{ experimentType.fields ? experimentType.fields.length : 0 }}</td>
                    <td class="action-cell">
                        <button class="action-btn" @click="editExperimentType(experimentType)">
                            编辑
                        </button>
                        <button class="action-btn btn-danger" @click="deleteExperimentType(experimentType.id)">
                            删除
                        </button>
                        <button class="action-btn btn-outline" @click="duplicateExperimentType(experimentType)">
                            复制
                        </button>
                        <button class="action-btn btn-info" @click="toggleDetails(experimentType.id)">
                            {{ expandedExperimentType === experimentType.id ? '收起' : '详情' }}
                        </button>
                    </td>
                </tr>
                <!-- 详情展开行 -->
                <tr v-if="expandedExperimentType === experimentType.id" class="detail-row" :key="'detail-'+experimentType.id">
                    <td colspan="4">
                        <div class="detail-content">
                            <div class="detail-header">
                                <h3 class="detail-title">{{ experimentType.name }} - 详情</h3>
                                <button class="btn btn-outline" @click="expandedExperimentType = null">
                                    <i class="material-icons">close</i> 收起
                                </button>
                            </div>
                            
                            <div class="detail-section">
                                <h4>描述</h4>
                                <p>{{ experimentType.description || '暂无描述' }}</p>
                            </div>
                            
                            <div class="detail-section">
                                <h4>字段定义</h4>
                                <div v-if="experimentType.fields && experimentType.fields.length > 0" class="field-list">
                                    <div v-for="(field, index) in experimentType.fields" :key="index" class="field-item">
                                        <div class="field-name">{{ field.field_name }}</div>
                                        <div class="field-props">
                                            <span>{{ field.data_type }}</span>
                                            <span v-if="field.unit">{{ field.unit }}</span>
                                            <span v-else>无单位</span>
                                        </div>
                                        <div class="field-props">
                                            <span v-if="field.is_required" class="required-badge">必填</span>
                                            <span v-else>可选</span>
                                            <span v-if="field.visualize_type" class="visualized-badge">可视化 {{ field.visualize_type }}</span>
                                            <span v-else class="not-visualized-badge">不可视化</span>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="no-fields">
                                    <i class="material-icons">inbox</i>
                                    <p>此实验类型尚未定义任何字段</p>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
                </template>
            </tbody>
            </table>
        </div>
        </div>
    </div>

    <!-- 数据库管理 -->
    <div v-if="activeTab === 'database'" class="form-container">
    <h2 class="section-title">数据库管理</h2>
    <p class="section-description">管理数据库文件和程序日志</p>
    
    <!-- 数据库信息 -->
    <div class="form-section">
        <h3>数据库信息</h3>
        <div class="info-container">
        <div class="info-item">
            <span class="info-label">数据库文件:</span>
            <span class="info-value">{{ dbInfo.fileName || 'mice.db' }}</span>
        </div>
        <div class="info-item">
            <span class="info-label">文件大小:</span>
            <span class="info-value">{{ formatFileSize(dbInfo.fileSize) }}</span>
        </div>
        <div class="info-item">
            <span class="info-label">最后修改:</span>
            <span class="info-value">{{ dbInfo.lastModified || '未知' }}</span>
        </div>
        <div class="info-item">
            <span class="info-label">记录数量:</span>
            <span class="info-value">{{ dbInfo.totalRecords }} 条</span>
        </div>
        </div>
        
        <div class="form-group">
        <button class="btn btn-outline" @click="refreshDbInfo">
            <i class="material-icons">refresh</i> 刷新信息
        </button>
        </div>
    </div>

    <!-- 数据库导入 -->
    <div class="form-section">
        <h3>导入数据库</h3>
        <div class="import-options">
        <div class="file-upload" @dragover.prevent @drop="handleDbDrop">
            <input type="file" accept=".db" @change="handleDbFileUpload">
            <div class="upload-area" :class="{ 'dragover': isDbDragging }">
            <i class="material-icons">cloud_upload</i>
            <p v-if="!selectedDbFile">点击或拖拽数据库文件(.db)到此处上传</p>
            <p v-else class="file-info">
                <span>{{ selectedDbFile.name }}</span>
                <span>({{ formatFileSize(selectedDbFile.size) }})</span>
            </p>
            <button v-if="selectedDbFile" class="btn btn-outline" @click="clearDbFile">清除</button>
            </div>
        </div>
        
        <div v-if="selectedDbFile" class="warning-message">
            <i class="material-icons">warning</i>
            <span>警告：导入数据库将覆盖当前所有数据，请谨慎操作！</span>
        </div>
        
        <div v-if="selectedDbFile" class="form-group">
            <button class="btn btn-primary" @click="importDatabase" :disabled="isImportingDb">
            <span v-if="isImportingDb">导入中...</span>
            <span v-else>确认导入数据库</span>
            </button>
        </div>
        </div>
    </div>
    
    <!-- 数据库导出 -->
    <div class="form-section">
        <h3>导出数据库</h3>
        <div class="export-options">
        <p>导出当前工作目录的数据库文件</p>
        <div class="form-group">
            <button class="btn btn-primary" @click="exportDatabase" :disabled="isExportingDb">
            <span v-if="isExportingDb">导出中...</span>
            <span v-else>导出数据库文件</span>
            </button>
        </div>
        </div>
    </div>

    <!-- 数据库清空 -->
    <div class="form-section">
    <h3>清空数据库</h3>
    <div class="export-options">
        <p class="warning-text">警告：此操作将删除所有数据，包括小鼠信息、基因型、位置、实验记录等，且无法恢复！</p>
        
        <div class="form-group">
        <div class="confirmation-input">
            <label>请输入确认文字 "<strong>DELETE ALL DATA</strong>" 以继续：</label>
            <input type="text" v-model="deleteConfirmation" placeholder="DELETE ALL DATA" 
                class="confirmation-field" :class="{ 'error': deleteConfirmationError }">
            <div v-if="deleteConfirmationError" class="error-message">
            {{ deleteConfirmationError }}
            </div>
        </div>
        </div>
        
        <div class="form-group">
        <button class="btn btn-danger" @click="clearDatabase" :disabled="!isDeleteConfirmed || isClearingDb">
            <span v-if="isClearingDb">清空中...</span>
            <span v-else>清空数据库</span>
        </button>
        </div>
    </div>
    </div>
    
    <!-- 日志导出 -->
    <div class="form-section">
        <h3>导出程序日志</h3>
        <div class="export-options">
        <p>导出当前工作目录的程序日志文件</p>
        <div class="form-group">
            <button class="btn btn-outline" @click="exportLogFile" :disabled="isExportingLog">
            <span v-if="isExportingLog">导出中...</span>
            <span v-else>导出日志文件</span>
            </button>
        </div>
        </div>
    </div>
    </div>

    <!-- 编辑基因位点对话框 -->
    <div v-if="editLocusDialogVisible" class="dialog-overlay">
    <div class="dialog-container">
        <h2>编辑基因位点</h2>
        <div class="form-group">
        <label>基因符号</label>
        <input type="text" v-model="editingLocus.symbol" required>
        </div>
        <div class="form-group">
        <label>描述</label>
        <textarea v-model="editingLocus.description"></textarea>
        </div>
        <div class="dialog-buttons">
        <button class="btn btn-outline" @click="editLocusDialogVisible = false">取消</button>
        <button class="btn btn-primary" @click="saveGeneLocus">保存</button>
        </div>
    </div>
    </div>

    <!-- 编辑等位基因对话框 -->
    <div v-if="editAlleleDialogVisible" class="dialog-overlay">
    <div class="dialog-container">
        <h2>编辑等位基因</h2>
        <div class="form-group">
        <label>符号</label>
        <input type="text" v-model="editingAllele.symbol" required>
        </div>
        <div class="form-group">
        <label>描述</label>
        <input type="text" v-model="editingAllele.description">
        </div>
        <div class="form-group">
        <label>是否为野生型</label>
        <input type="checkbox" v-model="editingAllele.is_wildtype">
        </div>
        <div class="dialog-buttons">
        <button class="btn btn-outline" @click="editAlleleDialogVisible = false">取消</button>
        <button class="btn btn-primary" @click="saveAllele">保存</button>
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
    <div v-if="importResultDialogVisible" @click.self="importResultDialogVisible=false" class="dialog-overlay">
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

    <!-- 数据库导入结果对话框 -->
    <div v-if="dbImportResultDialogVisible" @click.self="dbImportResultDialogVisible=false" class="dialog-overlay">
    <div class="dialog-container">
        <h2>数据库结果</h2>
        <div class="import-result">
        <div v-if="dbImportResult.success" class="result-item success">
            <i class="material-icons">check_circle</i>
            <span>数据库成功！</span>
        </div>
        <div v-else class="result-item error">
            <i class="material-icons">error</i>
            <span>数据库失败</span>
        </div>
        
        <div v-if="dbImportResult.message" class="result-message">
            {{ dbImportResult.message }}
        </div>
        
        <div v-if="dbImportResult.details" class="error-details">
            <h4>详细信息:</h4>
            <pre>{{ dbImportResult.details }}</pre>
        </div>
        </div>
        <div class="dialog-buttons">
        <button class="btn btn-primary" @click="handleDbImportComplete">确定</button>
        </div>
    </div>
    </div>
</div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

import { useGeneStore, useCageStore } from '@/stores'
import { storeToRefs } from 'pinia'

const geneStore = useGeneStore()
const cageStore = useCageStore()

const {genotypes} = storeToRefs(geneStore)
const {loadGenotypes} = geneStore

const {locations} = storeToRefs(cageStore)

// UI状态
const activeTab = ref('genotype')
const tabs = ref([
{ id: 'genotype', title: '基因型设置' },
{ id: 'location', title: '位置设置' },
{ id: 'experiment', title: '实验类型设置' },
{ id: 'export', title: '导出设置' },
{ id: 'import', title: '导入数据' },
{ id: 'database', title: '数据库管理' } 
])

// 基因型相关状态
const newGeneLocus = reactive({ symbol: '', description: '' })
const newAllele = reactive({ symbol: '', description: '', is_wildtype: false })
const expandedLoci = ref([])
const editingLocus = reactive({ id: null, symbol: '', description: '' })
const editLocusDialogVisible = ref(false)
const editingAllele = reactive({ id: null, symbol: '', description: '', is_wildtype: false })
const editAlleleDialogVisible = ref(false)

// 位置相关状态
const newLocation = reactive({ identifier: '', description: '' })
const editingLocation = reactive({ id: null, identifier: '', description: '' })
const editLocationDialogVisible = ref(false)

// 导出设置相关状态
const exportOptionsVisible = ref(false)
const exportStartDate = ref('')
const exportEndDate = ref('')
const exportFormat = ref('xlsx')
const currentExportType = ref('')
const selectedExperiments = ref([])
const exportOptions = ref([
{ id: 'mice', title: '导出小鼠表' },
{ id: 'weights', title: '导出体重表' },
{ id: 'survival', title: '导出生存表' },
{ id: 'records', title: '导出状态信息表' },
{ id: 'experiment', title: '导出实验记录表' }
])

// 导入设置相关状态
const selectedFile = ref(null)
const isDragging = ref(false)
const importType = ref('mice')
const importConflictResolution = ref('skip')
const isImporting = ref(false)
const importResultDialogVisible = ref(false)
const importResult = reactive({
successCount: 0,
skippedCount: 0,
errors: []
})

// 实验类型相关状态
const experimentTypes = ref([])
const experimentPresets = ref({})
const editingExperimentType = reactive({
id: null,
name: '',
description: '',
fields: []
})
const selectedPreset = ref('')
const expandedExperimentType = ref(null)

// 数据库管理相关状态
const selectedDbFile = ref(null)
const isDbDragging = ref(false)
const isImportingDb = ref(false)
const isExportingDb = ref(false)
const isExportingLog = ref(false)
const dbImportResultDialogVisible = ref(false)
const dbImportResult = reactive({
success: false,
message: '',
details: ''
})
const dbInfo = ref({
fileName: '',
fileSize: 0,
lastModified: '',
recordCount: 0
})
const deleteConfirmation = ref('')
const deleteConfirmationError = ref('')
const isClearingDb = ref(false)

// 计算属性：检查是否确认删除
const isDeleteConfirmed = computed(() => {
  return deleteConfirmation.value === 'DELETE ALL DATA'
})

// 监听确认输入框的变化
watch(deleteConfirmation, (newValue) => {
  if (newValue && newValue !== 'DELETE ALL DATA') {
    deleteConfirmationError.value = '确认文字不匹配'
  } else {
    deleteConfirmationError.value = ''
  }
})

const toggleAlleles = (id) => {
    const index = expandedLoci.value.indexOf(id)
    if (index === -1) {
    expandedLoci.value.push(id)
    } else {
    expandedLoci.value.splice(index, 1)
    }
}

const addGeneLocus = async () => {
    if (!newGeneLocus.symbol) {
    toast.info('请填写基因位点名称')
    return
    }

    try {
    const response = await axios.post('/api/gene', newGeneLocus)
    genotypes.value.push(response.data)
    newGeneLocus.symbol = ''
    newGeneLocus.description = ''
    toast.success('添加基因位点成功')
    } catch (error) {
    console.error('添加基因位点失败:', error)
    toast.error('添加基因位点失败，请重试')
    }
}

const addAllele = async (locus_id) => {
    if (!newAllele.symbol) {
    toast.info('请填写基因位点修饰名称')
    return
    }

    try {
    await axios.post(`/api/${locus_id}/gene_allele`, newAllele)
    await loadGenotypes()
    newAllele.symbol = ''
    newAllele.description = ''
    newAllele.is_wildtype = false
    toast.success('添加基因位点编辑方式成功')
    } catch (error) {
    console.error('添加基因位点修饰失败:', error)
    toast.error('添加基因位点修饰失败，请重试')
    }
}

const editGeneLocus = (genotype) => {
Object.assign(editingLocus, { ...genotype })
editLocusDialogVisible.value = true
}

const editAllele = (genotype) => {
Object.assign(editingAllele, { ...genotype })
editAlleleDialogVisible.value = true
}

const saveGeneLocus = async () => {
try {
await axios.put(`/api/gene/${editingLocus.id}`, editingLocus)
await loadGenotypes()
editLocusDialogVisible.value = false
toast.success('修改基因位点成功')
} catch (error) {
console.error('更新基因位点失败:', error)
toast.error('更新基因位点失败，请重试')
}
}

const saveAllele = async () => {
try {
await axios.put(`/api/gene_allele/${editingAllele.id}`, editingAllele)
await loadGenotypes()
editAlleleDialogVisible.value = false
toast.success('修改基因位点编辑方式成功')
} catch (error) {
console.error('更新等位基因失败:', error)
toast.error('更新等位基因失败，请重试')
}
}

const deleteGeneLocus = async (id) => {
if (!confirm('确定要删除这个基因位点吗？')) return

try {
await axios.delete(`/api/gene/${id}`)
genotypes.value = genotypes.value.filter(g => g.id !== id)
toast.success('删除基因位点成功')
} catch (error) {
console.error('删除基因型失败:', error)
toast.error('删除基因型失败，请重试')
}
}

const deleteAllele = async (id) => {
    if (!confirm('确定要删除这个基因型吗？')) return

    try {
    await axios.delete(`/api/gene_allele/${id}`)
    await loadGenotypes()
    toast.success('删除基因位点编辑方式成功')
    } catch (error) {
    console.error('删除基因型失败:', error)
    toast.error('删除基因型失败，请重试')
    }
}

const addLocation = async () => {
if (!newLocation.identifier) {
toast.info('请填写位置标识')
return
}

try {
const response = await axios.post('/api/locations', newLocation)
locations.value.push(response.data)
newLocation.identifier = ''
newLocation.description = ''
} catch (error) {
console.error('添加位置失败:', error)
toast.error('添加位置失败，请重试')
}
}

const editLocation = (location) => {
Object.assign(editingLocation, { ...location })
editLocationDialogVisible.value = true
}

const saveLocation = async () => {
try {
const response = await axios.put(`/api/locations/${editingLocation.id}`, editingLocation)
const index = locations.value.findIndex(l => l.id === editingLocation.id)
if (index !== -1) {
    locations.value[index] = response.data
}
editLocationDialogVisible.value = false
} catch (error) {
console.error('更新位置失败:', error)
toast.error('更新位置失败，请重试')
}
}

const deleteLocation = async (id) => {
if (!confirm('确定要删除这个位置吗？')) return

try {
await axios.delete(`/api/locations/${id}`)
locations.value = locations.value.filter(l => l.id !== id)
} catch (error) {
console.error('删除位置失败:', error)
toast.error('删除位置失败，请重试')
}
}

// 导出相关方法
const exportData = (type) => {
currentExportType.value = type
selectedExperiments.value = []
exportOptionsVisible.value = true
}

const toggleSelect = (id) => {
const index = selectedExperiments.value.indexOf(id)
if (index === -1) {
selectedExperiments.value.push(id)
} else {
selectedExperiments.value.splice(index, 1)
}
}

const confirmExport = async () => {
const params = {
start_date: exportStartDate.value,
end_date: exportEndDate.value,
experiment_ids: selectedExperiments.value,
format: exportFormat.value
}

try {
const response = await axios.get(`/api/export/${currentExportType.value}`, { 
    params,
    responseType: 'blob'
})

// 使用 PyWebview 的保存文件对话框
if (window.pywebview && window.pywebview.api) {
    const filename = `${currentExportType.value}_export.${exportFormat.value}`
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
    link.setAttribute('download', `${currentExportType.value}_export.${exportFormat.value}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    toast.success("导出成功")
}
} catch (error) {
console.error('导出数据失败:', error)
toast.error('导出数据失败，请重试')
} finally {
    exportOptionsVisible.value = false
    currentExportType.value = ""
    exportStartDate.value = ""
    exportEndDate.value = ""
}
}

// 导入相关方法
const handleFileUpload = (event) => {
selectedFile.value = event.target.files[0]
event.target.value = null
}

const handleDrop = (event) => {
event.preventDefault()
isDragging.value = false

if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
selectedFile.value = event.dataTransfer.files[0]
}
}

const clearFile = () => {
selectedFile.value = null
}

const formatFileSize = (bytes) => {
if (bytes === 0) return '0 Bytes'
const k = 1024
const sizes = ['Bytes', 'KB', 'MB', 'GB']
const i = Math.floor(Math.log(bytes) / Math.log(k))
return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const importData = async () => {
if (!selectedFile.value) {
toast.info('请选择要导入的文件')
return
}

isImporting.value = true

const formData = new FormData()
formData.append('file', selectedFile.value)
formData.append('type', importType.value)
formData.append('conflict_resolution', importConflictResolution.value)

try {
const response = await axios.post('/api/import', formData, {
    headers: {
    'Content-Type': 'multipart/form-data'
    }
})
Object.assign(importResult, response.data)
importResultDialogVisible.value = true
} catch (error) {
console.error('导入失败:', error)
toast.error(`导入失败: ${error.response?.data?.error || '服务器错误'}`)
} finally {
isImporting.value = false
}
}

// 实验类型相关方法
const fetchExperimentTypes = async () => {
try {
const response = await axios.get('/api/experiment-types')
experimentTypes.value = response.data
} catch (error) {
console.error('获取实验类型列表失败:', error)
toast.error('获取实验类型列表失败')
}
}

const fetchExperimentPresets = async () => {
try {
const response = await axios.get('/api/experiment-types/presets')
experimentPresets.value = response.data
} catch (error) {
console.error('获取实验预设失败:', error)
}
}

const addField = () => {
editingExperimentType.fields.push({
field_name: '',
data_type: 'TEXT',
unit: '',
is_required: false,
visualize_type: "",
display_order: editingExperimentType.fields.length
})
}

const removeField = (index) => {
editingExperimentType.fields.splice(index, 1)
}

const saveExperimentType = async () => {
if (!editingExperimentType.name) {
toast.info('请填写实验类型名称')
return
}

if (editingExperimentType.fields.length === 0) {
toast.info('请至少添加一个字段')
return
}

updateFieldOrders()

// 验证字段
for (let i = 0; i < editingExperimentType.fields.length; i++) {
const field = editingExperimentType.fields[i]
if (!field.field_name) {
    toast.info(`第${i + 1}个字段缺少名称`)
    return
}
if (!field.data_type) {
    toast.info(`字段"${field.field_name}"缺少数据类型`)
    return
}
}

if (editingExperimentType.id && !confirm('调整属性后，这个实验的分组不受影响，但已有数据会被删除（建议及时导出），是否继续？')) return

const url = editingExperimentType.id 
? `/api/experiment-types/${editingExperimentType.id}`
: '/api/experiment-types'

const method = editingExperimentType.id ? 'put' : 'post'

const dataToSend = {
...editingExperimentType,
fields: editingExperimentType.fields.map((field, index) => ({
    ...field,
    display_order: field.display_order !== undefined ? field.display_order : index
}))
}

try {
await axios[method](url, dataToSend)
toast.success('保存成功')
cancelEdit()
await fetchExperimentTypes()
window.experimentTypesUpdated = true
} catch (error) {
console.error('保存实验类型失败:', error)
toast.error(error.response?.data?.error || '保存实验类型失败')
}
}

const editExperimentType = (experimentType) => {
// 深拷贝实验类型
const copy = JSON.parse(JSON.stringify(experimentType))
copy.id = experimentType.id
copy.name = experimentType.name
copy.description = experimentType.description

Object.assign(editingExperimentType, copy)
selectedPreset.value = ''

// 滚动到表单顶部
nextTick(() => {
const formElement = document.querySelector('.form-section')
if (formElement) {
    formElement.scrollIntoView({ behavior: 'smooth' })
}
})
}

const cancelEdit = () => {
editingExperimentType.id = null
editingExperimentType.name = ''
editingExperimentType.description = ''
editingExperimentType.fields = []
}

const deleteExperimentType = async (id) => {
if (!confirm('确定要删除这个实验类型吗？')) return

try {
await axios.delete(`/api/experiment-types/${id}`)
toast.success('删除成功')
await fetchExperimentTypes()
window.experimentTypesUpdated = true
} catch (error) {
console.error('删除实验类型失败:', error)
toast.error(error.response?.data?.error || '删除实验类型失败')
}
}

const applyPreset = () => {
if (selectedPreset.value && experimentPresets.value[selectedPreset.value]) {
const preset = experimentPresets.value[selectedPreset.value]

// 保留当前已编辑的内容，只添加预设的字段
const currentFields = editingExperimentType.fields || []
const presetFields = JSON.parse(JSON.stringify(preset.fields))

// 设置显示顺序
const maxOrder = currentFields.length > 0 ? 
    Math.max(...currentFields.map(f => f.display_order)) : -1

presetFields.forEach((field, index) => {
    field.display_order = maxOrder + index + 1
})

// 合并字段
editingExperimentType.fields = [...currentFields, ...presetFields]

// 如果名称和描述为空，则使用预设的值
if (!editingExperimentType.name) {
    editingExperimentType.name = preset.name
}
if (!editingExperimentType.description) {
    editingExperimentType.description = preset.description
}
}
}

const resetForm = () => {
editingExperimentType.id = null
editingExperimentType.name = ''
editingExperimentType.description = ''
editingExperimentType.fields = []
selectedPreset.value = ''
}

const moveFieldUp = (index) => {
if (index > 0) {
const fields = editingExperimentType.fields
;[fields[index], fields[index - 1]] = [fields[index - 1], fields[index]]
updateFieldOrders()
}
}

const moveFieldDown = (index) => {
if (index < editingExperimentType.fields.length - 1) {
const fields = editingExperimentType.fields
;[fields[index], fields[index + 1]] = [fields[index + 1], fields[index]]
updateFieldOrders()
}
}

const updateFieldOrders = () => {
editingExperimentType.fields.forEach((field, index) => {
field.display_order = index
})
}

const duplicateExperimentType = (experimentType) => {
// 深拷贝实验类型
const copy = JSON.parse(JSON.stringify(experimentType))
copy.id = null
copy.name = copy.name + ' (副本)'

Object.assign(editingExperimentType, copy)
selectedPreset.value = ''

// 滚动到表单顶部
nextTick(() => {
const formElement = document.querySelector('.form-section')
if (formElement) {
    formElement.scrollIntoView({ behavior: 'smooth' })
}
})
}

const toggleDetails = (id) => {
if (expandedExperimentType.value === id) {
expandedExperimentType.value = null
} else {
expandedExperimentType.value = id
}
}

// 数据库管理相关方法
const handleDbFileUpload = (event) => {
  selectedDbFile.value = event.target.files[0]
  event.target.value = null
}

const handleDbDrop = (event) => {
  event.preventDefault()
  isDbDragging.value = false

  if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0]
    if (file.name.endsWith('.db')) {
      selectedDbFile.value = file
    } else {
      toast.error('请选择.db格式的数据库文件')
    }
  }
}

const clearDbFile = () => {
  selectedDbFile.value = null
}

const importDatabase = async () => {
  if (!selectedDbFile.value) {
    toast.info('请选择要导入的数据库文件')
    return
  }

  if (!confirm('警告：此操作将覆盖当前所有数据，且不可恢复！确定要继续吗？')) {
    return
  }

  isImportingDb.value = true

  const formData = new FormData()
  formData.append('file', selectedDbFile.value)

  try {
    const response = await axios.post('/api/database/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    Object.assign(dbImportResult, {
      success: true,
      message: response.data.message,
      details: response.data.details
    })
    
    dbImportResultDialogVisible.value = true
    toast.success('数据库导入成功')
  } catch (error) {
    console.error('数据库导入失败:', error)
    Object.assign(dbImportResult, {
      success: false,
      message: error.response?.data?.error || '数据库导入失败',
      details: error.response?.data?.details || ''
    })
    dbImportResultDialogVisible.value = true
    toast.error('数据库导入失败')
  } finally {
    isImportingDb.value = false
  }
}

const exportDatabase = async () => {
  isExportingDb.value = true

  try {
    const response = await axios.get('/api/database/export', {
      responseType: 'blob'
    })

    // 使用 PyWebview 的保存文件对话框
    if (window.pywebview && window.pywebview.api) {
      const filename = `mice_backup_${new Date().toISOString().split('T')[0]}.db`
      const arrayBuffer = await response.data.arrayBuffer()
      const uint8array = new Uint8Array(arrayBuffer)
      const dataArray = Array.from(uint8array)
      const state = await window.pywebview.api.save_file_dialog(dataArray, filename)
      if(state.success){
        toast.success(`数据库导出成功，文件路径：${state.path}`)
      } else {
        toast.info(state.message || "导出失败")
      }
    } else {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `mice_backup_${new Date().toISOString().split('T')[0]}.db`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success("数据库导出成功")
    }
  } catch (error) {
    console.error('导出数据库失败:', error)
    toast.error('导出数据库失败，请重试')
  } finally {
    isExportingDb.value = false
  }
}

const exportLogFile = async () => {
  isExportingLog.value = true

  try {
    const response = await axios.get('/api/database/export-log', {
      responseType: 'blob'
    })

    // 使用 PyWebview 的保存文件对话框
    if (window.pywebview && window.pywebview.api) {
      const filename = `app_log_${new Date().toISOString().split('T')[0]}.log`
      const arrayBuffer = await response.data.arrayBuffer()
      const uint8array = new Uint8Array(arrayBuffer)
      const dataArray = Array.from(uint8array)
      const state = await window.pywebview.api.save_file_dialog(dataArray, filename)
      if(state.success){
        toast.success(`日志文件导出成功，文件路径：${state.path}`)
      } else {
        toast.info(state.message || "导出失败")
      }
    } else {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `app_log_${new Date().toISOString().split('T')[0]}.log`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success("日志文件导出成功")
    }
  } catch (error) {
    console.error('导出日志文件失败:', error)
    toast.error('导出日志文件失败，请重试')
  } finally {
    isExportingLog.value = false
  }
}

const refreshDbInfo = async () => {
  try {
    const response = await axios.get('/api/database/info')
    dbInfo.value = response.data
  } catch (error) {
    console.error('获取数据库信息失败:', error)
    toast.error('获取数据库信息失败')
  }
}

const handleDbImportComplete = () => {
  dbImportResultDialogVisible.value = false
  selectedDbFile.value = null
  // 刷新数据库信息
  refreshDbInfo()
}

// 清空数据库方法
const clearDatabase = async () => {
  if (!isDeleteConfirmed.value) {
    deleteConfirmationError.value = '请正确输入确认文字'
    return
  }
  
  if (!confirm('最后确认：这将永久删除所有数据，此操作不可逆！确定要继续吗？')) {
    return
  }
  
  isClearingDb.value = true
  deleteConfirmationError.value = ''
  
  try {
    const response = await axios.post('/api/database/clear')
    toast.success('数据库清空成功')
    deleteConfirmation.value = ''
    
    // 刷新数据库信息
    await refreshDbInfo()
    
    // 显示清空结果
    Object.assign(dbImportResult, {
      success: true,
      message: '数据库已成功清空，所有数据已被删除',
      details: `清空时间: ${new Date().toLocaleString()}\n删除记录数: ${response.data.deleted_records || '未知'}`
    })
    dbImportResultDialogVisible.value = true
    
  } catch (error) {
    console.error('清空数据库失败:', error)
    const errorMsg = error.response?.data?.error || '清空数据库失败'
    toast.error(errorMsg)
    
    Object.assign(dbImportResult, {
      success: false,
      message: errorMsg,
      details: error.response?.data?.details || ''
    })
    dbImportResultDialogVisible.value = true
  } finally {
    isClearingDb.value = false
  }
}

// 初始化数据
onMounted(() => {
fetchExperimentTypes()
fetchExperimentPresets()
refreshDbInfo()
})
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

.settings-table tbody tr.selected {
background-color: #d3f1d9;
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
margin-right: 8px;
}

.action-btn:hover {
background-color: #e0e0e0;
}

.btn-group {
display: flex;
gap: 15px;
margin-top: 20px;
}

.btn-group .btn.active {
    /* 激活状态样式 */
    background-color: #2ecc71;
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
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

.preset-selector {
display: flex;
align-items: center;
gap: 10px;
margin-bottom: 15px;
flex-wrap: wrap;
}

.preset-selector select {
width: 200px;
padding: 8px;
border: 1px solid #ddd;
border-radius: 4px;
}

.preset-description {
color: #666;
font-style: italic;
}

.fields-section {
margin-top: 20px;
padding: 15px;
border: 1px solid #e0e0e0;
border-radius: 5px;
background-color: #f9f9f9;
}

.fields-section h4 {
margin-top: 0;
margin-bottom: 15px;
color: #333;
}

.field-actions {
margin-top: 15px;
}

.settings-table input[type="text"],
.settings-table input[type="number"],
.settings-table select {
width: 100%;
padding: 5px;
border: 1px solid #ddd;
border-radius: 3px;
}


.btn-outline:disabled {
opacity: 0.5;
cursor: not-allowed;
}

.btn-outline:disabled:hover {
background-color: transparent;
}

/* 详情展开区域样式 */
.detail-row {
    background-color: #f9fafb;
}

.detail-content {
    padding: 20px;
    border-top: 1px solid #e0e0e0;
}

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.detail-title {
    font-size: 1.1rem;
    color: #2c3e50;
    font-weight: 500;
}

.detail-section {
    margin-bottom: 20px;
}

.detail-section h4 {
    font-size: 1rem;
    color: #2c3e50;
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 1px solid #eee;
}

.field-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
}

.field-item {
    background: white;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #eef2f7;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

.field-name {
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 5px;
}

.field-props {
    display: flex;
    justify-content: space-between;
    color: #666;
    font-size: 0.9rem;
}

.required-badge {
    background-color: #ffecb3;
    color: #7d6608;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
}

.no-fields {
    grid-column: 1 / -1;
    text-align: center;
    padding: 20px;
    color: #7f8c8d;
    background: #f9fafb;
    border-radius: 6px;
    border: 1px dashed #ddd;
}

.btn-info {
    background-color: #17a2b8;
    color: white;
}

.btn-info:hover {
    background-color: #138496;
}

.btn-danger {
background-color: #e53935;
color: white;
}

.btn-danger:hover:not(:disabled) {
background-color: #c62828;
}

.btn-danger:disabled {
  background-color: #f5b7b1;
  cursor: not-allowed;
}

/* 可视化徽章样式 */
.visualized-badge {
    background-color: #d4edda;
    color: #155724;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
    margin-left: 8px;
}

.not-visualized-badge {
    background-color: #f8d7da;
    color: #721c24;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
    margin-left: 8px;
}

/* 数据库管理特定样式 */
.warning-message {
  display: flex;
  align-items: center;
  padding: 10px;
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  margin: 15px 0;
  color: #856404;
}

.warning-message i {
  margin-right: 10px;
  color: #f39c12;
}

.info-container {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e9ecef;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 500;
  color: #495057;
}

.info-value {
  color: #6c757d;
}

.result-message {
  margin: 15px 0;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

.error-details pre {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.warning-text {
  color: #e74c3c;
  font-weight: 500;
  background-color: #fdedec;
  padding: 10px;
  border-radius: 4px;
  border-left: 4px solid #e74c3c;
}

.confirmation-input {
  margin-bottom: 15px;
}

.confirmation-field {
  width: 100%;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 5px;
}

.confirmation-field.error {
  border-color: #e74c3c;
  background-color: #fdedec;
}

.confirmation-field:focus {
  outline: none;
  border-color: #3498db;
}

.confirmation-input label {
  font-weight: 500;
  color: #2c3e50;
}

.confirmation-input label strong {
  color: #e74c3c;
}

.error-message {
  color: #e74c3c;
  font-size: 12px;
  margin-top: 5px;
}

/* 基因位点行样式 */
.locus-row {
  background-color: #f8f9fa;
  font-weight: bold;
}

/* 等位基因子表格容器 */
.alleles-subtable {
  background-color: #f0f8ff;
}

.subtable-container {
  padding: 15px;
  background-color: #fff;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  margin: 10px 0;
}

/* 子表格样式 */
.subtable {
  width: 100%;
  margin-bottom: 15px;
}

.subtable th {
  background-color: #e9ecef;
}

.subtable tr:nth-child(even) {
  background-color: #f8f9fa;
}

/* 添加等位基因表单 */
.add-allele-form {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 5px;
  border: 1px dashed #ced4da;
}

.add-allele-form h4 {
  margin-top: 0;
  color: #495057;
}

.btn-success {
  background-color: #28a745;
  color: white;
}
</style>