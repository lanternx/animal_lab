import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useCageStore = defineStore('cage', () => {
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
        await fetchLocations()
        await fetchCages()
    }

    // 位置相关方法
    const locations = ref([])
    
    const fetchLocations = async () => {
        try {
            const response = await api.get('/locations')
            locations.value = response.data
        } catch (error) {
            console.error('获取位置列表失败:', error)
        }
    }

    // 笼位相关方法
    const cages = ref([])
    const activeSection = ref('')
    const section_key = ref(false)
    // 计算属性 - 过滤笼位
    const filteredCages = computed(() => {
        if (!activeSection.value) return cages.value
        return cages.value.filter(cage => cage.section === activeSection.value)
    })
    // 获取所有笼位数据
    async function fetchCages() {
    try {
        console.log('开始获取笼位数据...')
        
        const response = await api.get('/cages')
        console.log('获取到cages数据:', response.data)
        cages.value = response.data
        
        // 设置默认选中的section为第一个
        if (locations.value.length > 0 && section_key.value) {
        activeSection.value = locations.value[0].identifier
        section_key.value = false
        console.log('设置默认section为:', activeSection.value)
        }
        console.log('笼位数据获取完成')
    } catch (error) {
        console.error('获取笼位信息失败:', error)
    }
    }

    const calculateCages = (section) => {
        if (!section) return cages.value
        return cages.value.filter(cage => cage.section === section)
    }

    return {
        locations,
        cages,
        filteredCages,
        activeSection,
        section_key,

        fetchLocations,
        fetchCages,
        calculateCages,
        loadInitialData
    }
})
