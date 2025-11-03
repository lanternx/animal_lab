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

    return {
        experiments,
        showedExperiments,
        experimentPresets,

        fetchExperiments,
        loadInitialData
    }
})
