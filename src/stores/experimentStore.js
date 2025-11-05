import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useExperimentStore = defineStore('experiment', () => {
    const api = axios.create({
            baseURL: '/api',
            timeout: 60000,
            headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-store, max-age=0', // 完全禁用缓存
            'Pragma': 'no-cache'
            }
        })

    const loadInitialData = async () => {
        fetchExperiments()
        fetchExperimentPresets()
    }

    const experiments = ref([])
    const showedExperiments = computed(() => {
        return experiments.value.filter(expr => expr.is_show)
    })
    const experimentPresets = ref({})
    
    // 实验类型相关方法
    const fetchExperiments = async () => {
        try {
            const response = await api.get('/experiment-types')
            experiments.value = response.data
        } catch (error) {
            console.error('获取实验类型列表失败:', error)
        }
    }

    const fetchExperimentPresets = async () => {
        try {
            const response = await api.get('/experiment-types/presets')
            experimentPresets.value = response.data
            } catch (error) {
            console.error('获取实验预设失败:', error)
        }
    }

    async function fetchCandidateMice() {
    try {
        const response = await axios.get(`/api/experiment/${experimentId.value}/candidate_mice`, {cancelToken: currentRequestToken.token});
        candidateMice.value = response.data;
    } catch (error) {
        console.error('获取候选小鼠失败:', error);
        toast.error('获取候选小鼠失败: ' + error.message);
    }
    }
    
    async function fetchGroups() {
        try {
            const response = await axios.get(`/api/experiment/${experimentId.value}/groups`, {cancelToken: currentRequestToken.token});
            groupedMice.value = { ...response.data }; 
        } catch (error) {
            console.error('获取分组失败:', error);
            toast.error('获取分组失败: ' + error.message);
        }
    }

    async function changeMouseGroup(mouseId, groupId, newGroupId) {
    try {
        await axios.post(`/api/experiment/${experimentId.value}/class_change`, {
            mouse_id: mouseId,
            class_id: groupId,
            class_new_id: newGroupId
        });
    } catch (error) {
        console.error(`添加小鼠 (ID: ${mouseId})到分组失败:`, error);
        toast.error(`添加小鼠 (ID: ${mouseId})到分组失败: ` + error.message);
    }
    }
    
    async function deleteGroup(groupId) {
    try {
        await axios.delete(`/api/experiment/${experimentId.value}/groups/${groupId}`);
        await fetchCandidateMice();
        await fetchGroups();
    } catch (error) {
        console.error('删除分组失败:', error);
        toast.error('删除分组失败: ' + error.message);
    }
    }
    
    async function clearAllGroups() {
    if (!confirm('确定要清除所有分组吗？此操作不可恢复。')) return;
    
    try {
        await axios.delete(`/api/experiment/${experimentId.value}/groups/clear`);
        await fetchCandidateMice();
        await fetchGroups();
    } catch (error) {
        console.error('清除所有分组失败:', error);
        toast.error('清除所有分组失败: ' + error.message);
    }
    }

    async function saveGroupName(oldGroupId) {
    const newGroupId = editingGroupNames.value[oldGroupId].trim();

    if (!newGroupId) {
        toast.error('分组名称不能为空');
        return;
    }

    if (newGroupId === oldGroupId) {
        cancelEditingGroup(oldGroupId);
        return;
    }

    if (Object.keys(groupedMice.value).includes(newGroupId)) {
        toast.error('分组名称已存在，请使用其他名称');
        return;
    }

    try {
        const response = await axios.put(`/api/experiment/${experimentId.value}/groups/${oldGroupId}`, {newGroupId:newGroupId});
        
        if (response.data && response.data.message) {
            groupedMice.value[newGroupId] = groupedMice.value[oldGroupId];
            delete groupedMice.value[oldGroupId];
            
            editingGroups.value[oldGroupId] = false;
            delete editingGroupNames.value[oldGroupId];
            
            toast.success(response.data.message);
        } else {
            toast.error('分组名称修改失败: ' + response.data.error);
        }
    } catch (error) {
        console.error('修改分组名称失败:', error);
        toast.error('修改分组名称失败: ' + error.message);
    }
}

function cancelEditingGroup(groupId) {
editingGroups.value[groupId] = false;
delete editingGroupNames.value[groupId];
}

    return {
        experiments,
        showedExperiments,
        experimentPresets,

        fetchExperiments,
        loadInitialData
    }
})
