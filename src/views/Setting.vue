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
                    <div class="btn-group">
                        <button class="action-btn" @click="editGeneLocus(locus)">编辑</button>
                        <button v-if="locus.symbol !== 'WT'" class="action-btn btn-danger" @click="deleteGeneLocus(locus.id)">删除</button>
                        <button v-if="locus.symbol !== 'WT'" class="action-btn btn-success" @click="toggleAlleles(locus.id)">
                        {{ expandedLoci.includes(locus.id) ? '收起' : '展开并为该位点添加等位基因' }}
                        </button>
                    </div>
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
                                <div class="btn-group">
                                    <button class="action-btn" @click="editAllele(allele)">编辑</button>
                                    <button class="action-btn btn-danger" @click="deleteAllele(allele.id)">删除</button>
                                </div>
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
                    <div class="btn-group">
                    <button class="action-btn" @click="editLocation(location)">编辑</button>
                    <button class="action-btn btn-danger" @click="deleteLocation(location.id)">删除</button>
                    </div>
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
            <template v-for="experimentType in experiments" :key="experimentType.id">
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
                            <td>基因型描述，格式为：{位点1}[等位基因1]/[等位基因2]&{位点2}[等位基因3]/[等位基因4]</td>
                            <td class="example-row">{Trp53}[KO]/[+]或{WT}</td>
                        </tr>
                        <tr>
                            <td><span class="required">sex</span></td>
                            <td>字符串</td>
                            <td><span class="required">是</span></td>
                            <td>性别：M/F</td>
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
                            <td>存活状态：1=存活，0=死亡，2=解剖，3=失踪，4=丢弃，5=处理后死亡</td>
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
                        <tr>
                            <td><span class="optional">strain</span></td>
                            <td>字符串</td>
                            <td><span class="optional">否</span></td>
                            <td>小鼠品系</td>
                            <td class="example-row">C57BL/6J</td>
                        </tr>
                        <tr>
                            <td><span class="optional">record</span></td>
                            <td>字符串</td>
                            <td><span class="optional">否</span></td>
                            <td>导入时备注信息</td>
                            <td class="example-row">2025.1.1 被咬</td>
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
                        <p>5. 基因型的位点和等位基因中不能出现特殊字符，示例：{p53}[S46A]/[-]&{p21}[-]/[-]</p>
                        <p>6. 当live_status!=1（不为存活）时，必须提供death_date</p>
                        <p>7. 区域名称只有在存在笼位名称时才生效</p>
                        <p>8. 若无区域名称，新笼位自动添加到新创建的区域，后续可调整（通过笼位设置）</p>
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
                <label>是否展示</label>
                <div class="checkbox-group">
                    <input type="checkbox" v-model="editingExperimentType.is_show" id="edit-show-checkbox">
                    <label for="edit-show-checkbox">在侧边栏显示</label>
                </div>
            </div>
            
            <div class="btn-group">
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
                    <select v-model="field.data_type" required @change="chooseDataType(field)">
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
                        <option v-if="field.data_type === 'INTEGER' || field.data_type === 'REAL' || field.data_type === 'DATE'" value="x">作为横坐标</option>
                        <option v-if="field.data_type === 'INTEGER' || field.data_type === 'REAL'" value="y">作为纵坐标</option>
                        <option v-if="field.data_type === 'INTEGER' || field.data_type === 'REAL'" value="column">作为柱状图</option>
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
                <th>是否展示</th>
                <th>操作</th>
                </tr>
            </thead>
            <tbody>
            <template v-for="experimentType in experiments" :key="experimentType.id">
                <tr>
                    <td>{{ experimentType.name }}</td>
                    <td>{{ experimentType.description }}</td>
                    <td>{{ experimentType.fields ? experimentType.fields.length : 0 }}</td>
                    <td>{{ experimentType.is_show ? '是' : '否' }}</td>
                    <td class="action-cell">
                        <div class="btn-group">
                        <button class="action-btn" @click="editExperimentType(experimentType.id)">
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
                        </div>
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

    <!-- 在template中添加分组设置的内容 -->
    <div v-if="activeTab === 'group'" class="form-container">
        <h2 class="section-title">预设分组逻辑</h2>
        
        <!-- 添加新分组 -->
        <div class="form-section">
            <h3>{{ editingGroup.id ? '编辑分组' : '添加新分组' }}</h3>
            <form class="form-group-row">
                <div class="form-group">
                    <label>是否为实验预设分组？</label>
                    <div class="group-type-selector">
                        <select v-model="editingGroup.experiment_id" @change="changeGroupExperiment(editingGroup.experiment_id)" :disabled="editingGroup.id">
                            <option :value=null>不为实验预设分组</option>
                            <option v-for="experiment in experiments" :value="experiment.id" :key="experiment.id" >
                            {{ experiment.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="form-group" style="gap: 20px;display: flex;">
                    <button @click="saveGroup" class="btn btn-primary" :disabled="isSaving">
                        {{ editingGroup.id ? '更新' : '添加' }}
                    </button>
                    <button type="button" class="btn btn-outline" @click="cancelEditGroup">
                        取消
                    </button>
                </div>
            </form>
            <form class="form-group-row">
                <div class="form-group">
                    <label>分组名称 *</label>
                    <input type="text" v-model="editingGroup.name" placeholder="例如: WT vs TP53 ♀" required>
                </div>
                
                <div class="form-group">
                    <label>描述</label>
                    <input type="text" v-model="editingGroup.description" placeholder="例如: WT雌性小鼠 vs TP53敲除雌性小鼠">
                </div>

                <div class="form-group">
                    <label>分组类型</label>
                    <select v-model="editingGroup.Gtype" @change="changeGroupType" class="group-type-selector" :disabled="editingGroup.experiment_id">
                        <option class="radio-label" value="" disabled selected>--请选择分组--</option>
                        <option value="rule" class="radio-label">
                            规则分组
                        </option>
                        <option value="id" class="radio-label">
                            ID分组
                        </option>
                    </select>
                </div>
            </form>
            <!-- 规则配置 -->
            <div v-if="editingGroup.Gtype" class="form-section-rule">
                <!-- 规则分组小组管理 -->
                <div v-if="editingGroup.Gtype === 'rule'" class="subgroups-container">
                    <h4>规则设置</h4>
                    <div v-for="(subgroup, subgroupIndex) in editingGroup.rules" 
                        :key="subgroupIndex" 
                        class="subgroup-item">
                        <div class="subgroup-header">
                            <div class="subgroup-title">
                                <h5>小组 {{ subgroupIndex + 1 }}</h5>
                                <input type="text" v-model="subgroup.name" placeholder="小组名称" class="subgroup-name-input">
                                <div class="color-picker-container">
                                    <label>主题色:</label>
                                    <div v-for="color in colors" 
                                        :key="color"
                                        class="color-option"
                                        :class="{ selected: subgroup.color === color }"
                                        :style="{ backgroundColor: color }"
                                        @click="subgroup.color = color"
                                    >
                                        <i v-if="subgroup.color === color" class="material-icons">check</i>
                                    </div>
                                    <input type="color" v-model="subgroup.color" class="color-input">
                                </div>
                            </div>
                            <div class="subgroup-actions">
                                <button class="action-btn btn-danger" @click="removeGroup(subgroupIndex)">
                                    <i class="material-icons">delete</i>
                                </button>
                                <button class="action-btn btn-outline" @click="toggleSubgroupRules(subgroupIndex)">
                                    {{ subgroup.expanded ? '收起规则' : '展开规则' }}
                                </button>
                            </div>
                        </div>
                        
                        <!-- 规则分组 -->
                        <div v-if="subgroup.expanded" class="subgroup-rules">
                            <div class="rules-container">
                                <div v-for="(rule, ruleIndex) in subgroup.rules" :key="ruleIndex" class="rule-item">
                                    <div class="rule-header">
                                        <span>规则 {{ ruleIndex + 1 }}</span>
                                        <button class="action-btn btn-danger" @click="removeRule(subgroupIndex, ruleIndex)">
                                            <i class="material-icons">delete</i>
                                        </button>
                                    </div>
                                    
                                    <div class="rule-content">
                                        <!-- 保持原有的规则设置界面不变 -->
                                        <div class="form-group-row">
                                            <div class="form-group">
                                                <label>规则类型</label>
                                                <select v-model="rule.Rtype" @change="resetRuleValues(rule)">
                                                    <option value="genotype">基因型</option>
                                                    <option value="sex">性别</option>
                                                    <option value="strain">品系</option>
                                                    <option value="cage">笼位</option>
                                                    <option value="live_status">存活状态</option>
                                                    <option value="test_planned">计划实验</option>
                                                </select>
                                            </div>
                                                <button class="action-btn" v-if="rule.Rtype === 'genotype'" :disabled="!genotypeAddable" @click="addGenotype(subgroupIndex, ruleIndex)">
                                                    添加基因型
                                                </button>
                                        </div>

                                        <!-- 基因型规则 -->
                                        <div v-if="rule.Rtype === 'genotype'" class="form-group-row" style="width: 100%;">
                                            <div v-for="(gene, geneIndex) in rule.genes">
                                                <!-- 基因型选择 -->
                                                <div class="gene-form-group">
                                                    <div class="form-header">
                                                    <label>基因型:
                                                        <span class="selected-gene" v-if="!gene?.selectedGeneName" v-html="geneStore.selectedGeneName"></span>
                                                        <span class="selected-gene" v-else v-html="gene.selectedGeneName"></span>
                                                    </label>
                                                    <button v-if="!gene?.selectedGeneName" class="" @click="addGene" :disabled="!geneStore.addable">
                                                        <i class="material-icons">add</i>
                                                    </button>
                                                    <button v-else class="btn-remove" @click="removeGeneSelection(subgroupIndex, ruleIndex, geneIndex)">
                                                        <i class="material-icons">close</i>
                                                    </button>
                                                    </div>

                                                    <div v-if="!gene?.selectedGeneName" v-for="(gene, index) in selectedGenes" class="genotype-select-container" :key="gene">
                                                    <div class="locus-control">
                                                        <div class="locus-select">
                                                        <select v-model="gene.locus" @change="onFormLocusChange(index, gene.locus)">
                                                        <option v-for="locus in geneStore.locusSuggestions[index]" :key="locus.id" :value="locus.symbol">
                                                            {{ locus.symbol }}
                                                        </option>
                                                        </select>
                                                        </div>
                                                        <button class="action-btn btn-remove" @click="deleteGene(index)">
                                                        <i class="material-icons">delete</i>
                                                        </button>
                                                    </div>

                                                    <div class="allele-controls">
                                                        <div class="allele-group" v-if="gene.locus && gene.locus !== 'WT'">
                                                        <label>等位基因 1</label>
                                                        <select v-model="gene.allele1" :disabled="!gene.locus" @change="onFormAlleleChange(true, index, gene.allele1)">
                                                        <option v-for="allele in alleleSuggestions[index][0]" :key="allele.id" :value="allele.id">
                                                            {{ allele.symbol }}
                                                        </option>
                                                        </select>
                                                        </div>
                                                        <div class="allele-group" v-if="gene.locus && gene.locus !== 'WT'">
                                                        <label>等位基因 2</label>
                                                        <select v-model="gene.allele2" :disabled="!gene.locus" @change="onFormAlleleChange(false, index, gene.allele2)">
                                                        <option v-for="allele in alleleSuggestions[index][1]" :key="allele.id" :value="allele.id">
                                                            {{ allele.symbol }}
                                                        </option>
                                                        </select>
                                                        </div>
                                                    </div>
                                                    </div>
                                                    <div v-if="selectedGenes.length>0 && !gene?.selectedGeneName" class="form-group-row">
                                                        <button class="primary-btn btn-clear-all" @click="deleteGenes">
                                                        <i class="material-icons">delete_forever</i>
                                                        全部删除
                                                        </button>
                                                        <button class="primary-btn" @click="saveGenes(subgroupIndex, ruleIndex, geneIndex)">
                                                        <i class="material-icons">archive</i>
                                                        确定基因型
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <!-- 性别规则 -->
                                        <div v-if="rule.Rtype === 'sex'" class="form-group">
                                            <label>性别</label>
                                            <select v-model="rule.value">
                                                <option value="M">雄性</option>
                                                <option value="F">雌性</option>
                                            </select>
                                        </div>
                                        
                                        <!-- 品系规则 -->
                                        <div v-if="rule.Rtype === 'strain'" class="form-group">
                                            <label>品系</label>
                                            <input type="text" v-model="rule.value" placeholder="例如: C57BL/6">
                                        </div>
                                        
                                        <!-- 笼位规则 -->
                                        <div v-if="rule.Rtype === 'cage'" class="form-group-location">
                                            <label>笼位标识</label>
                                            <div class="genotype-tree">
                                                <div v-for="section in locations" :key="section.id" class="locus-item">
                                                <div class="locus-header">
                                                    <label class="locus-label">
                                                    <input 
                                                        type="checkbox" 
                                                        :value="section.identifier" 
                                                        v-model="rule.locations"
                                                        class="locus-checkbox"
                                                    >
                                                    <span class="locus-name">{{section.identifier}}</span>
                                                    </label>
                                                </div>
                                                <div class="combinations-list">
                                                    <div v-for="cage in calculateCages(section.identifier)" :key="cage.id" class="combination-item">
                                                    <label class="combination-label">
                                                        <input 
                                                        type="checkbox" 
                                                        :value="cage.id"
                                                        v-model="rule.cages"
                                                        class="combination-checkbox"
                                                        >
                                                        <span class="combination-name">{{ cage.cage_id }}</span>
                                                    </label>
                                                    </div>
                                                </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <!-- 存活状态规则 -->
                                        <div v-if="rule.Rtype === 'live_status'" class="form-group">
                                            <label>存活状态</label>
                                            <select v-model="rule.value">
                                                <option value="1">存活</option>
                                                <option value="0">死亡</option>
                                                <option value="2">解剖</option>
                                                <option value="3">意外消失</option>
                                                <option value="4">丢弃</option>
                                            </select>
                                        </div>

                                        <!-- 存活状态规则 -->
                                        <div v-if="rule.Rtype === 'test_planned'" class="form-group-location">
                                            <label>计划实验</label>
                                                <div class="genotype-tree">
                                                <div v-for="test in experiments" :key="test.id" class="locus-item">
                                                <div class="locus-header">
                                                    <label class="locus-label">
                                                    <input 
                                                        type="checkbox" 
                                                        :value="test.id" 
                                                        v-model="rule.test_planned"
                                                        class="locus-checkbox"
                                                    >
                                                    <span class="locus-name">{{test.name}}</span>
                                                    </label>
                                                </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <button @click="addRule(subgroupIndex)" :disabled="showIDList" class="btn btn-outline">
                                <i class="material-icons">add</i> 添加规则
                            </button>
                        </div>
                    </div>
                    <div class="form-group-row">
                    <button :disabled="showIDList" @click="addGroup" class="btn btn-outline add-subgroup-btn">
                        <i class="material-icons">add</i> 添加小组
                    </button>
                    <button v-if="!showIDList" @click="reviewRules" class="btn btn-primary add-subgroup-btn">
                        <i class="material-icons">book</i> 预览规则
                    </button>
                    <button v-else @click="reviewRulesClose" class="btn btn-danger add-subgroup-btn">
                        <i class="material-icons">book</i> 取消预览
                    </button>
                    <button @click="saveGroup" class="btn btn-success add-subgroup-btn">
                        <i class="material-icons">save</i> 按规则存储
                    </button>
                    </div>
                </div>
                <!-- ID分组 -->
                <div v-if="showIDList || editingGroup.Gtype === 'id'">
                        <IdGroupingManager
                            :candidate-mice="candidateMice"
                            :editing-group="editingGroup"
                            :colors="colors"
                            v-model:is-saving="isSaving"
                            @update:editing-group="handleGroupUpdate"
                            @save-group="saveGroup"
                        />
                </div>
            </div>
        </div>
        
        <!-- 分组列表 -->
        <div class="form-section">
            <h3>分组列表</h3>
            <div class="table-container">
                <table class="settings-table">
                    <thead>
                        <tr>
                            <th>分组名称</th>
                            <th>描述</th>
                            <th>分组类型</th>
                            <th>小组数量</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template v-for="group in predefinedGroups" :key="group.id">
                        <tr >
                            <td>{{ group.name }}</td>
                            <td>{{ group.description }}</td>
                            <td>
                                <span class="group-type-badge" :class="group.Gtype === 'id' ? 'id-group' : 'rule-group'">
                                    {{ group.Gtype === 'id' ? 'ID分组' : '规则分组' }}
                                </span>
                            </td>
                            <td>{{ group.rules ? group.rules.length : 0 }}</td>
                            <td class="action-cell">
                                <div class="btn-group">
                                <button class="action-btn" @click="editGroup(group)">编辑</button>
                                <button class="action-btn btn-danger" @click="deleteGroup(group.id)">删除</button>
                                <button class="action-btn btn-success" @click="toggleGroupDetails(group.id)">
                                    {{ expandedGroup.includes(group.id) ? '收起' : '详情' }}
                                </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="expandedGroup.includes(group.id)" class="alleles-subtable">
                        <td colspan="5">
                            <div class="subtable-container">
                            <table class="subtable">
                                <thead>
                                <tr>
                                    <th>组名</th>
                                    <th>主题色</th>
                                    <th v-if="group.Gtype === 'id'">组内小鼠数量</th>
                                    <th v-else>规则数量</th>
                                </tr>
                                </thead>
                                <tbody>
                                <tr v-for="g in group.rules" :key="g.name">
                                    <td>{{ g.name }}</td>
                                    <td :style="{ backgroundColor: g.color }"></td>
                                    <td>{{ group.Gtype === 'id' ? g.mouseId?.length : g.rules?.length }}</td>
                                </tr>
                                </tbody>
                            </table>
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
        <div class="section-header">
            <h3>数据库信息</h3>
            <div class="btn-group">
                <button v-if="!addingDatabase" class="btn btn-outline" @click="addDatabase">创建新数据库</button>
                <button class="btn btn-primary" @click="importDatabase">导入数据库</button>
            </div>
        </div>
        <div class="database-list">
            <div 
                v-for="(db, key) in databases" 
                :key="key"
                class="database-card"
                :class="{ 'current': currentDatabase === key }"
            >
                <div class="database-header">
                    <div class="database-name">
                        <template v-if="editingIndex === key && editingField === 'projectName'">
                            <input 
                                v-model="editingValue" 
                                class="editing-input"
                                @keyup.enter="saveEdit(key)"
                                @blur="saveEdit(key)"
                                autofocus
                            >
                        </template>
                        <template v-else>
                            <span @dblclick="startEdit(key, 'projectName', db.projectName)">
                                {{ db.projectName || '未命名项目' }}
                            </span>
                        </template>
                    </div>
                    <div class="info-value">
                        <span 
                            class="status-badge" 
                            :class="getStatusClasses(db, key)"
                            @click="toggleReadOnly(key)"
                            :title="db.readOnly ? '点击设为可写' : '点击设为只读'"
                        >
                            <span class="status-icon">
                                <template v-if="currentDatabase === key">★</template>
                                <template v-else-if="db.readOnly">🔒</template>
                                <template v-else>✓</template>
                            </span>
                            {{ getDatabaseStatus(db.readOnly, key) }}
                        </span>
                    </div>
                </div>
                
                <div class="database-details">
                    <div class="detail-item">
                        <span class="detail-label">项目开始时间：</span>
                        <span class="detail-value">
                            <template v-if="editingIndex === key && editingField === 'startAt'">
                                <input 
                                    v-model="editingValue" 
                                    class="editing-input"
                                    type="date"
                                    @keyup.enter="saveEdit(key)"
                                    @blur="saveEdit(key)"
                                    autofocus
                                >
                            </template>
                            <template v-else>
                                <span @dblclick="startEdit(key, 'startAt', db.startAt)">
                                    {{ db.startAt || '未知' }}
                                </span>
                            </template>
                        </span>
                    </div>
                    <div v-if="db.readOnly" class="detail-item">
                        <span class="detail-label">项目结束时间：</span>
                        <span class="detail-value">
                            <template v-if="editingIndex === key && editingField === 'endAt'">
                                <input 
                                    v-model="editingValue" 
                                    class="editing-input"
                                    type="date"
                                    @keyup.enter="saveEdit(key)"
                                    @blur="saveEdit(key)"
                                    autofocus
                                >
                            </template>
                            <template v-else>
                                <span @dblclick="startEdit(key, 'endAt', db.endAt)">
                                    {{ db.endAt || '未知' }}
                                </span>
                            </template>
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">文件大小:</span>
                        <span class="detail-value">{{ formatFileSize(db.fileSize) }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">最后修改:</span>
                        <span class="detail-value">{{ db.lastModified || '未知' }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">记录数量:</span>
                        <span class="detail-value">{{ db.totalRecords }} 条</span>
                    </div>
                </div>
                
                <div class="actions">
                    <button
                        class="action-btn primary" 
                        @click="selectDatabase(key)"
                        :disabled="currentDatabase === key || databaseNotChanged === false"
                    >
                        设为当前
                    </button>
                    <button
                        class="action-btn secondary" 
                        @click="exportDatabase(key)"
                        :disabled="(!db.totalRecords && db.totalRecords !== 0) || databaseNotChanged === false"
                    >
                        导出
                    </button>
                    <button
                        class="action-btn btn-danger" 
                        @click="deleteDatabase(key)"
                        :disabled="currentDatabase === key || databaseNotChanged === false"
                    >
                        删除
                    </button>
                </div>
            </div>
            <div v-if="addingDatabase" class="database-card">
                <div class="database-header">
                    <span class="detail-label">项目名称：</span>
                    <div class="database-name">
                        <input 
                            v-model="editingDatabase.projectName" 
                            class="editing-input"
                            autofocus
                        >
                    </div>
                </div>
                
                <div class="database-details">
                    <div class="detail-item">
                        <span class="detail-label">项目开始时间：</span>
                        <span class="detail-value">
                            <input 
                                v-model="editingDatabase.startAt" 
                                class="editing-input"
                                type="date"
                            >
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">项目结束时间：</span>
                        <span class="detail-value">
                            <input 
                                v-model="editingDatabase.endAt" 
                                class="editing-input"
                                type="date"
                            >
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">只读模式</span>
                        <div class="checkbox-group">
                            <input type="checkbox" v-model="editingDatabase.readOnly" id="edit-readonly-checkbox">
                            <label for="edit-readonly-checkbox">启用只读模式</label>
                        </div>
                    </div>
                </div>
                <div class="actions">
                    <button
                        class="action-btn btn-primary" 
                        @click="createDatabase">确认
                    </button>
                    <button
                        class="action-btn btn-danger" 
                        @click="cancelCreateDatabase">取消
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- 数据库清空 -->
    <div class="form-section">
    <h3>清空当前数据库</h3>
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
    <div v-if="dbImportResultDialogVisible" @click.self="cancelImportDatabase" class="dialog-overlay">
    <div class="dialog-container">
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
            <span>警告：导入数据库将添加到数据库列表中！</span>
        </div>
        
        <div v-if="selectedDbFile">
            <h2>编辑数据库信息</h2>
            <div class="form-group">
                <label>项目名称 *</label>
                <input type="text" v-model="editingDatabase.projectName" required>
            </div>
            <div class="form-group">
                <label>开始时间</label>
                <input type="date" v-model="editingDatabase.startAt">
            </div>
            <div class="form-group">
                <label>结束时间</label>
                <input type="date" v-model="editingDatabase.endAt">
            </div>
            <div class="form-group">
                <label>只读模式</label>
                <div class="checkbox-group">
                    <input type="checkbox" v-model="editingDatabase.readOnly" id="edit-readonly-checkbox">
                    <label for="edit-readonly-checkbox">启用只读模式</label>
                </div>
            </div>
            <div class="detail-item">
                <span class="detail-label">数据库升级</span>
                <div class="checkbox-group">
                    <input type="checkbox" v-model="editingDatabase.databaseUpdate" id="edit-update-checkbox">
                    <label for="edit-update-checkbox">从V2.X版本升级（基因型无法更新）</label>
                </div>
            </div>
        </div>
        </div>
        <div class="dialog-buttons">
            <button class="btn btn-primary" @click="handleDbImportComplete">确定</button>
            <button class="btn btn-primary" @click="cancelImportDatabase">取消</button>
        </div>
    </div>
    </div>
</div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed, nextTick } from 'vue'
import axios from 'axios'
import { toast } from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'
import IdGroupingManager from '@/components/IdGroupingManager.vue'

import { useGeneStore, useCageStore, useExperimentStore } from '@/stores'
import { storeToRefs } from 'pinia'

const geneStore = useGeneStore()
const cageStore = useCageStore()
const experimentStore = useExperimentStore()

const { genotypes, selectedGenes, alleleSuggestions, mice } = storeToRefs(geneStore)
const { loadGenotypes, colors, onFormLocusChange, onFormAlleleChange, deleteGene, addGene, deleteGenes } = geneStore

const {locations, section_key} = storeToRefs(cageStore)
const {calculateCages, fetchCages} = cageStore

const {experiments, experimentPresets, predefinedGroups, trueCurrentDatabase, databaseNotChanged} = storeToRefs(experimentStore)
const {fetchExperiments, fetchPredefinedGroups} = experimentStore

// UI状态
const activeTab = ref('genotype')
const tabs = ref([
{ id: 'genotype', title: '基因型设置' },
{ id: 'location', title: '位置设置' },
{ id: 'experiment', title: '实验类型设置' },
{ id: 'group', title: '预设分组' },
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
const editingExperimentType = reactive({
id: null,
name: '',
description: '',
is_show: true,
fields: []
})
const selectedPreset = ref('')
const expandedExperimentType = ref(null)

// 数据库管理相关状态
const selectedDbFile = ref(null)
const isDbDragging = ref(false)
const isExportingLog = ref(false)
const dbImportResultDialogVisible = ref(false)
const deleteConfirmation = ref('')
const deleteConfirmationError = ref('')
const isClearingDb = ref(false)
const editingDatabase = ref({
projectName: '',
startAt: '',
endAt: '',
readOnly: false,
databaseUpdate: false
})
const currentDatabase = ref('')
const databases = ref({})
const addingDatabase = ref(false)

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

// 分组设置相关状态
const editingGroup = reactive({
    id: null,
    name: '',
    description: '',
    Gtype: '',
    experiment_id: null,
    rules: []
})
const expandedGroup = ref([])
const genotypeAddable = ref(false)
const candidateMice = ref([])//候选小鼠
const showIDList = ref(false)
const isSaving = ref(false)

const handleGroupUpdate = (updatedGroup) => {
    Object.assign(editingGroup, updatedGroup)
}

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
toast.success("区域编辑成功")
editLocationDialogVisible.value = false
section_key.value = false
await fetchCages()
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
        if (importType.value === 'mice') {
            await geneStore.loadInitialData()
            await cageStore.loadInitialData()
        }
    } catch (error) {
        console.error('导入失败:', error)
        toast.error(`导入失败: ${error.response?.data?.error || '服务器错误'}`)
    } finally {
        isImporting.value = false
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
    toast.success('实验设置保存成功，请前往分组预设中设置分组')
    cancelEdit()
    await fetchExperiments()
    } catch (error) {
    console.error('保存实验类型失败:', error)
    toast.error(error.response?.data?.error || '保存实验类型失败')
    }
}

const editExperimentType = (experimentID) => {
    // 深拷贝实验类型
    const experimentType = experiments.value.find(et => et.id === experimentID)
    const copy = JSON.parse(JSON.stringify(experimentType))

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
editingExperimentType.is_show = true
editingExperimentType.fields = []
}

const deleteExperimentType = async (id) => {
if (!confirm('确定要删除这个实验类型吗？')) return

try {
await axios.delete(`/api/experiment-types/${id}`)
toast.success('删除成功')
await fetchExperiments()
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
editingExperimentType.is_show = preset.is_show
}
}

const resetForm = () => {
    if (editingExperimentType.id) {
        editExperimentType(editingExperimentType.id)
    } else {
        editingExperimentType.id = null
        editingExperimentType.name = ''
        editingExperimentType.description = ''
        editingExperimentType.fields = []
        editingExperimentType.is_show = true
        selectedPreset.value = ''
    }
}

const chooseDataType = (field) => {
    field.visualize_type = ''
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

const importDatabase = () => {
    dbImportResultDialogVisible.value = true
    selectedDbFile.value = null
    editingDatabase.value = {
        projectName: '',
        startAt: '',
        endAt: '',
        readOnly: false,
        databaseUpdate: false
    }
}

const cancelImportDatabase = () => {
    dbImportResultDialogVisible.value = false
    selectedDbFile.value = null
    editingDatabase.value = {
        projectName: '',
        startAt: '',
        endAt: '',
        readOnly: false,
        databaseUpdate: false
    }
}

const handleDbImportComplete = async () => {
    if (!selectedDbFile.value) {
        toast.info('请选择要导入的数据库文件')
        return
    }
    dbImportResultDialogVisible.value = false
    const formData = new FormData()
    formData.append('file', selectedDbFile.value)
    formData.append('project_info', JSON.stringify(editingDatabase.value))

    try {
        const response = await axios.post('/api/database/import', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
        })
        
        toast.success('数据库导入成功')
    } catch (error) {
        console.error('数据库导入失败:', error)
        toast.error('数据库导入失败')
    }
    selectedDbFile.value = null
}

const exportDatabase = async (key) => {
    const db = databases.value[key]
    if (!db) return

    try {
        const response = await axios.get(`/api/database/export/${key}`, {
            responseType: 'blob'
        })

    // 使用 PyWebview 的保存文件对话框
    if (window.pywebview && window.pywebview.api) {
        const filename = `${db.projectName}_backup_${new Date().toISOString().split('T')[0]}.db`
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
        link.setAttribute('download', `${db.projectName}_backup_${new Date().toISOString().split('T')[0]}.db`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        toast.success("数据库导出成功")
    }
    } catch (error) {
        console.error('导出数据库失败:', error)
        toast.error('导出数据库失败，请重试')
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
        const dbInfo = response.data
        
        if (databaseNotChanged.value) {
            databases.value[currentDatabase.value] = {...databases.value[currentDatabase.value], ...dbInfo}
        } else {
            databases.value[trueCurrentDatabase.value] = {...databases.value[trueCurrentDatabase.value], ...dbInfo}
        }
    } catch (error) {
        console.error('获取数据库信息失败:', error)
        toast.error('获取数据库信息失败')
    }
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
    
  } catch (error) {
    console.error('清空数据库失败:', error)
    const errorMsg = error.response?.data?.error || '清空数据库失败'
    toast.error(errorMsg)
  } finally {
    isClearingDb.value = false
  }
}

// 编辑状态
const editingIndex = ref('')
const editingField = ref('')
const editingValue = ref('')

// 创建数据库
const addDatabase = async () => {
    editingDatabase.value = {
        projectName: '',
        startAt: '',
        endAt: '',
        readOnly: false,
        databaseUpdate: false
    }
    addingDatabase.value = true
}

const createDatabase = async () => {
    const response = await axios.post('/api/database/create', editingDatabase.value)
    editingDatabase.value = {
        projectName: '',
        startAt: '',
        endAt: '',
        readOnly: false,
        databaseUpdate: false
    }
    if (response.status === 201) {
        // 确保响应包含必要的数据
        if (response.data.key && response.data.database) {
            const updatedDatabases = { ...databases.value }
            updatedDatabases[response.data.key] = response.data.database
            databases.value = updatedDatabases
            toast.success(response.data.message || '数据库创建成功')
        } else {
            toast.error('服务器返回的数据格式不正确')
        }
    }
    addingDatabase.value = false
}

const cancelCreateDatabase = () => {
    editingDatabase.value = {
        projectName: '',
        startAt: '',
        endAt: '',
        readOnly: false,
        databaseUpdate: false
    }
    addingDatabase.value = false
}

// 双击编辑功能
const startEdit = (index, field, value) => {
    editingIndex.value = index
    editingField.value = field
    editingValue.value = value
}

const saveEdit = async (index) => {
    if (editingIndex.value === index && editingField.value) {
        databases.value = {
            ...databases.value,
            [index]: {
                ...databases.value[index],
                [editingField.value]: editingValue.value
            }
        }
        const response = await axios.post(`/api/database/${index}`, databases.value[index])
        resetEdit()
        toast.success('修改成功')
    }
}

const resetEdit = () => {
    editingIndex.value = ''
    editingField.value = ''
    editingValue.value = ''
}

// 获取数据库状态文本
const getDatabaseStatus = (readOnly, key) => {
    if (currentDatabase.value === key) {
        return readOnly ? '当前(只读)' : '当前使用中'
    }
    return readOnly ? '只读' : '可用'
}

// 获取状态徽章的CSS类
const getStatusClasses = (db, key) => {
    const classes = {}
    if (currentDatabase.value === key) {
        classes.current = true
        classes.readonly = db.readOnly
    } else {
        if (db.readOnly) {
            classes['readonly-only'] = true
        } else {
            classes.available = true
        }
    }
    return classes
}

// 选择数据库
const selectDatabase = async (key) => {
    trueCurrentDatabase.value = currentDatabase.value
    currentDatabase.value = key
    await axios.put(`/api/database/${key}`)
    toast.success('数据库切换成功，重新启动应用后生效')
    databaseNotChanged.value = false
}

// 切换只读状态
const toggleReadOnly = async (key) => {
    const db = databases.value[key]
    if (db) {
        if (currentDatabase.value === key) {
            const message = db.readOnly 
                ? "当前数据库正在使用中，确定要将其设为可写吗？" 
                : "当前数据库正在使用中，确定要将其设为只读吗？设为只读后可能无法进行写操作。"
            
            if (!confirm(message)) return
        }
        
        db.readOnly = !db.readOnly
        const response = await axios.post(`/api/database/${key}`, db)
        toast.success(`数据库已设为${db.readOnly ? '只读' : '可写'}`)
    }
}

// 删除数据库
const deleteDatabase = async (key) => {
    if (currentDatabase.value === key) {
        toast.error('不能删除当前正在使用的数据库')
        return
    }
    
    if (confirm('确定要删除这个数据库吗？此操作不可恢复！')) {
        delete databases.value[key];
        await axios.delete(`/api/database/${key}`)
        toast.success('数据库删除成功')
    }
}

const fetchDbInfo = async () => {
    try {
        const response = await axios.get('/api/database')
        databases.value = response.data.databases
        currentDatabase.value = response.data.current_database
    } catch (error) {
        console.error('获取数据库列表失败:', error)
        toast.error('获取数据库列表失败')
    }
}

// 删除分组
const removeGroup = (index) => {
    editingGroup.rules.splice(index, 1)
}

// 分组设置相关方法
const addGroup = () => {
    // 找到一个未使用的颜色
    const usedColors = new Set(editingGroup.rules.map(g => g.color))
    const availableColor = colors.find(color => !usedColors.has(color)) || colors[0]

    editingGroup.rules.push({name: `新分组${editingGroup.rules.length + 1}`, color: availableColor, rules:[], expanded: true})
    genotypeAddable.value = true
}

const changeGroupExperiment = async (experimentID) => {
    editingGroup.Gtype = ''
    editingGroup.rules = []
    showIDList.value = false
    editingGroup.Gtype = 'id'
    editingGroup.name = (experiments.value.find(et => et.id === experimentID)?.name || "未知实验") + "-分组"
    if (editingGroup.experiment_id) {
        const miceExperiment = await axios.get(`/api/experiments/${editingGroup.experiment_id}/mice`)
        candidateMice.value = miceExperiment.data
    }
}

const changeGroupType = async () => {
    if (editingGroup.Gtype === 'id') {
        candidateMice.value = mice.value
    } else if (editingGroup.Gtype === 'rule') {
        showIDList.value = false
        selectedGenes.value = []
        alleleSuggestions.value = []
        genotypeAddable.value = true
    }
    editingGroup.rules = []
    showIDList.value = false
}

const toggleSubgroupRules = (subgroupIndex) => {
    editingGroup.rules[subgroupIndex].expanded = !editingGroup.rules[subgroupIndex].expanded
}

const addRule = (subgroupIndex) => {
    editingGroup.rules[subgroupIndex].rules.push({
        Rtype: 'genotype',
        genes:[],
    })
}

const removeRule = (subgroupIndex, index) => {
    editingGroup.rules[subgroupIndex].rules.splice(index, 1)
}

const removeGeneSelection = (subgroupIndex, ruleIndex, geneIndex) => {
    editingGroup.rules[subgroupIndex].rules[ruleIndex].genes.splice(geneIndex, 1)
}

const addGenotype = (subgroupIndex, ruleIndex) => {
    editingGroup.rules[subgroupIndex].rules[ruleIndex].genes.push([])
    genotypeAddable.value = false
}

const saveGenes = (subgroupIndex, ruleIndex, index) => {
    if (selectedGenes.value.some(g=> !g.locus)) {
        toast.info("请完善基因型")
        return
    }
    editingGroup.rules[subgroupIndex].rules[ruleIndex].genes[index] = {
        gene: [...selectedGenes.value],
        selectedGeneName: geneStore.selectedGeneName
    }
    selectedGenes.value = []
    alleleSuggestions.value = []
    genotypeAddable.value = true
}

const reviewRules = async () => {
    candidateMice.value = mice.value
    if (editingGroup.rules.length === 0) {
        toast.info("预览前请设定组别")
        return 
    }
    const response = await axios.post(`/api/groups/predefined/review`, { editing : editingGroup, candidate: candidateMice.value.map(m => m.tid)})
    response.data.forEach((g, gIndex) => {
        if (editingGroup.rules[gIndex]) {
            Object.assign(editingGroup.rules[gIndex], { mouseId: g })
        }
    })
    showIDList.value = true
    editingGroup.rules.forEach(g => g.expanded = false)
}

const reviewRulesClose = () => {
    showIDList.value = false
    editingGroup.rules.forEach(g => g.expanded = true)
}

const saveGroup = async () => {
    if (selectedGenes.value && selectedGenes.value.length !== 0) {
        toast.info('请完成基因选择')
        return
    }

    if (!editingGroup.name) {
        toast.info('请填写预设分组名称')
        return
    }

    if(!editingGroup.id && predefinedGroups.value.some(g => g.name == editingGroup.name)) {
        toast.info('预设分组不能重名')
        return
    }

    if(predefinedGroups.value?.some(g => {
        if (g?.experiment_id) {
            g?.experiment_id == editingGroup?.experiment_id
        }}) ?? false) {
        toast.info('同一实验只能有一个预设分组')
        return
    }

    isSaving.value = true
    const url = editingGroup.id 
        ? `/api/groups/predefined/${editingGroup.id}`
        : '/api/groups/predefined'

    const method = editingGroup.id ? 'put' : 'post'

    try {
        if (editingGroup.Gtype === 'id') {
            await axios[method](url, editingGroup)
            toast.success('预设ID分组保存成功')
        } else {
            await axios[method](url, editingGroup)
            toast.success('预设规则分组保存成功')
        }
        cancelEditGroup()
        fetchPredefinedGroups()
    } catch (error) {
        console.error('保存分组失败:', error)
        toast.error(error.response?.data?.error || '保存分组失败')
    } finally {
        isSaving.value = false
    }
}

const editGroup = (group) => {
    cancelEditGroup()
    Object.assign(editingGroup, group)
    const tempRules = editingGroup.rules
    changeGroupType()
    editingGroup.rules = tempRules
}

const cancelEditGroup = () => {
    editingGroup.id = null
    editingGroup.name = ''
    editingGroup.description = ''
    editingGroup.Gtype = ''
    editingGroup.experiment_id = null
    editingGroup.rules = []
    showIDList.value = false
}

const deleteGroup = async (id) => {
    if (!confirm('确定要删除这个分组吗？')) return

    try {
        await axios.delete(`/api/groups/predefined/${id}`)
        toast.success('删除成功')
        fetchPredefinedGroups()
        cancelEditGroup()
    } catch (error) {
        console.error('删除分组失败:', error)
        toast.error('删除分组失败')
    }
}

const resetRuleValues = (rule) => {
    // 根据规则类型重置值
    if (rule.Rtype === 'genotype') {
        rule.genes = []
        genotypeAddable.value = true
    } else if (rule.Rtype === 'sex') {
        rule.value = 'M'
    } else if (rule.Rtype === 'strain') {
        rule.value = ''
    } else if (rule.Rtype === 'cage') {
        rule.cages = []
    } else if (rule.Rtype === 'live_status') {
        rule.value = '1'
    } else if (rule.Rtype === 'test_planned') {
        rule.test_planned = []
    }
}

const toggleGroupDetails = (groupId) => {
    const index = expandedGroup.value.indexOf(groupId)
    if (index === -1) {
        expandedGroup.value.push(groupId)
    } else {
        expandedGroup.value.splice(index, 1)
    }
}

// 初始化数据
onMounted(() => {
fetchDbInfo()
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
align-items: center;
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

.btn-group {
display: flex;
gap: 15px;
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
max-width: 100%;
max-height: 80%;
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
overflow-y: auto;
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

.database-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.database-card {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    border: 1px solid #e0e0e0;
}

.database-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.database-card.current {
    border: 2px solid var(--primary);
    background-color: #f0fff4;
}

.database-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.database-name {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.database-name:hover {
    background-color: #e3f2fd;
}

.info-value {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-badge {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
}

.status-badge:hover {
    opacity: 0.9;
    transform: scale(1.05);
}

.status-badge.current {
    background-color: #4CAF50;
    color: white;
}

.status-badge.readonly {
    background-color: #FF9800;
    color: white;
}

.status-badge.available {
    background-color: #2196F3;
    color: white;
}

.status-badge.readonly-only {
    background-color: #9E9E9E;
    color: white;
}

.status-icon {
    margin-right: 4px;
    font-size: 14px;
}

.database-details {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
    margin-top: 10px;
}

.detail-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 2px;
}

.detail-value {
    font-size: 14px;
    color: #333;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 3px;
    transition: background-color 0.2s;
}

.detail-value:hover {
    background-color: #f5f5f5;
}

.actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
}

.action-btn.primary {
    background-color: #2196F3;
    color: white;
}

.action-btn.secondary {
    background-color: #e0e0e0;
    color: #333;
}

.action-btn:disabled {
    background-color: #f0f0f0;
    color: #aaa;
    cursor: not-allowed;
}

.editing-input {
    width: 100%;
    padding: 4px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

.section-header h3 {
    font-size: 1.3rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
}

/* 分组设置特定样式 */
.rules-container {
    margin-top: 15px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-bottom: 20px;
    align-items: center;
}

.rule-item {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-bottom: 15px;
    background: #fafafa;
    width: 45%;
}

.rule-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background: #e8f4fd;
    border-bottom: 1px solid #e0e0e0;
    font-weight: 600;
    color: #2c3e50;
}

.rule-content {
    padding: 15px;
}

.allele-requirements {
    margin-top: 8px;
}

.allele-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.allele-item select {
    flex: 1;
}

.allele-item .btn {
    padding: 4px 8px;
    min-width: auto;
}

/* 规则详情样式 */
.rules-list {
    display: grid;
    gap: 10px;
}

.rule-detail {
    background: white;
    padding: 12px 15px;
    border-radius: 4px;
    border-left: 4px solid #3498db;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.rule-type {
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 5px;
    font-size: 14px;
}

.rule-conditions {
    color: #666;
    font-size: 13px;
    line-height: 1.4;
}

.no-rules {
    text-align: center;
    padding: 30px;
    color: #7f8c8d;
    background: #f9fafb;
    border-radius: 6px;
    border: 1px dashed #ddd;
}

/* 测试区域样式 */
.test-section {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #e9ecef;
}

.test-result {
    margin-top: 15px;
    padding: 15px;
    background: white;
    border-radius: 4px;
    border: 1px solid #dee2e6;
}

.result-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 4px;
    margin-bottom: 10px;
}

.result-indicator.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.result-indicator.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.result-indicator i {
    font-size: 18px;
}

/* 分组表格样式增强 */
.settings-table tr:hover .rule-detail {
    background-color: #f0f7ff;
}

/* 动画效果 */
.rule-item {
    transition: all 0.3s ease;
}

.rule-item-enter-active, .rule-item-leave-active {
    transition: all 0.3s ease;
}

.rule-item-enter-from, .rule-item-leave-to {
    opacity: 0;
    transform: translateX(-30px);
}


/* 小组管理样式 */
.subgroups-container {
    margin-top: 20px;
}

.subgroup-item {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 20px;
    background: #fafafa;
}

.subgroup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background: #e8f4fd;
    border-bottom: 1px solid #e0e0e0;
}

.subgroup-title {
    display: flex;
    align-items: center;
    gap: 15px;
}

.subgroup-title h5 {
    margin: 0;
    color: #2c3e50;
    font-size: 16px;
}

.subgroup-name-input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    min-width: 200px;
}

.subgroup-actions {
    display: flex;
    gap: 10px;
}

.subgroup-rules {
    padding: 15px;
    background: white;
}

.add-subgroup-btn {
    width: 30%;
    padding: 12px;
    margin-top: 10px;
}

/* 详情展示样式 */
.subgroups-list {
    display: grid;
    gap: 15px;
}

.subgroup-detail {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 15px;
}

.subgroup-header-detail {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f0f0f0;
}

.subgroup-header-detail h5 {
    margin: 0;
    color: #2c3e50;
}

.rule-count {
    background: #3498db;
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
}

.no-subgroups {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
    background: #f9fafb;
    border-radius: 6px;
    border: 1px dashed #ddd;
}

.matched-info {
    background: #e8f5e8;
    padding: 10px;
    border-radius: 4px;
    margin: 10px 0;
    border-left: 4px solid #4CAF50;
}

.matched-info h5 {
    margin: 0;
    color: #2e7d32;
}

.group-type-selector {
    display: flex;
    gap: 20px;
}

.radio-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
}

.radio-custom {
    width: 16px;
    height: 16px;
    border: 2px solid #ddd;
    border-radius: 50%;
    display: inline-block;
    position: relative;
}

.radio-label input:checked + .radio-custom {
    border-color: #3498db;
}

.radio-label input:checked + .radio-custom::after {
    content: '';
    width: 8px;
    height: 8px;
    background: #3498db;
    border-radius: 50%;
    position: absolute;
    top: 2px;
    left: 2px;
}

.group-type-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

.group-type-badge.rule-group {
    background: #e3f2fd;
    color: #1976d2;
}

.group-type-badge.id-group {
    background: #f3e5f5;
    color: #7b1fa2;
}

.color-picker-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

.color-input {
    width: 30px;
    height: 30px;
    border: none;
    cursor: pointer;
}

.btn-remove {
    background: none;
    border: none;
    cursor: pointer;
    color: #666  !important;
    padding: 2px;
}

.btn-remove:hover {
    color: #ff4757;
}

.preview-section {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
    display: flex;
    gap: 10px;
}

.add-id-group-btn {
    width: 100%;
    margin-top: 10px;
}

.gene-form-group {
    width: 100%;
    padding: 10px 15px;
    border-radius: 8px;
    border: 1px solid #c5e6e6;
    background: rgb(255, 255, 255);
    font-size: 1rem;
    color: #020c17;
    appearance: none;
    background-position: right 15px center;
    background-size: 16px;
    transition: all 0.2s;
}

.form-group-location {
margin-bottom: 1rem;
}

.form-section-rule {
    padding: 10px;
    background: beige;
}

.action-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.btn i {
  margin-right: 5px;
}
</style>