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
        fetchPredefinedGroups()
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

    const selectedPredefinedGroupId = ref(null)
    const predefinedGroups = ref([])
    const showChartType = ref('pred')

    const fetchPredefinedGroups = async () => {
        try {
            const response = await api.get('/groups/predefined')
            predefinedGroups.value = response.data
        } catch (error) {
            console.error('获取分组失败:', error);
        }
    } 

    const getPredefinedGroups = async () => {
        // 筛选符合分组条件的小鼠
        const response = await api.get(`/groups/predefined/${selectedPredefinedGroupId.value}/mice`)
        return response.data
    }

    const databaseNotChanged = ref(true)
    const trueCurrentDatabase = ref('')

    const showColumns = ref({
        id: true,
        genotype: true,
        strain: true,
        sex: true,
        birth_date: true,
        days_old: true,
        weeks_old: true,
        live_status: true,

        death_date: false,
        tests_planned: false,
        tests_done: false,
        cage: true
    })


    return {
        experiments,
        showedExperiments,
        experimentPresets,
        selectedPredefinedGroupId,
        predefinedGroups,
        showChartType,
        databaseNotChanged,
        trueCurrentDatabase,
        showColumns,

        fetchExperiments,
        loadInitialData,
        getPredefinedGroups,
        fetchPredefinedGroups
    }
})
