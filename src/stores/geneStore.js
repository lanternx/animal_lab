import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useGeneStore = defineStore('genotype', () => {
    const api = axios.create({
            baseURL: '/api',
            timeout: 60000,
            headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
            }
        })

    const loadInitialData = async () => {
        loadGenotypes()
    }
    
    const genotypes = ref([])

    const loadGenotypes = async () => {
        try {
            const response = await api.get('/gene')
            genotypes.value = response.data
        } catch (error) {
            console.error('加载基因型失败:', error)
            toast.error(`加载基因型失败: ${error.message || '请检查网络连接'}`)
        }
    }

    return {
        genotypes,

        loadGenotypes,
        loadInitialData
    }
})
