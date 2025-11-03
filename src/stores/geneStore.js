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
        await loadMice()
        await loadGenotypes()
        await loadAllGenotypes()
    }

    const mice = ref([])
    const loading = ref(false)
    const loadMice = async () => {
        loading.value = true
        try {
            const response = await api.get('/mice')
            mice.value = response.data
        } catch (error) {
            console.error('加载小鼠失败:', error)
        } finally {
            loading.value = false
        }
    }
    const loadSurvival = async () => {
        try {
            // 获取所有生存数据
            const miceResponse = await api.get('/api/survival');
            return miceResponse.data;
        } catch (error) {
            console.error('获取基因型数据失败:', error);
        }
    };
    
    const genotypes = ref([])
    const allGenotypes = ref([])

    const loadAllGenotypes = async () => {
        const genotypeResponse = await axios.get('/api/genotypes')
        allGenotypes.value = genotypeResponse.data
    }

    const loadGenotypes = async () => {
        try {
            const response = await api.get('/gene')
            genotypes.value = response.data
        } catch (error) {
            console.error('加载基因型失败:', error)
        }
    }


    // 分组数据
    const tempGroups = ref([{ sex: { M: true, F: true }, genotype: [] }])
    const groupLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    const colors = ['#F27970', '#BB9727', '#54B345', '#32B897', '#05B9E2', '#8983BF', '#C76DA2', "#743027"]

    // 添加分组
    const addGroup = () => {
        if (tempGroups.value.length >= 8) {
            toast.info('最多只能添加8个分组')
            return
        }
        tempGroups.value.push({ sex: { M: true, F: true }, genotype: [] })
    }

    // 移除分组
    const removeGroup = (index) => {
        if (tempGroups.value.length > 1) {
            tempGroups.value.splice(index, 1)
        }
    }

    // 清空分组
    const clearGroups = () => {
        tempGroups.value = []
    }

    const getTempGroups = async () => {
        // 筛选符合分组条件的小鼠
        const response = await api.get('/groups/temp', { params: { groups: JSON.stringify(tempGroups.value) } })
        return response.data.map((group, groupIndex) => ({ 
            name: `分组 ${groupLetters[groupIndex]}`,
            color: colors[groupIndex % colors.length],
            mice: group
        }))
    }

    const getPredefinedGroups = async (gIndex) => {
        // 筛选符合分组条件的小鼠
        const response = await api.get(`/groups/predefined/${gIndex}`)
        return response.data
    }

    // 处理位点选择
    const onLocusSelect = (index, locus) => {
        const isSelected = tempGroups.value[index].genotype.includes(locus)
        if (isSelected) {
        // 如果选择了位点，移除该位点下的所有组合
        tempGroups.value[index].genotype = tempGroups.value[index].genotype.filter(g => 
            !allGenotypes.value[locus].some(al => g === locus+'<sup>'+al+'</sup>')
        )
        } else {
        // 如果取消选择位点，不做额外处理
        }
    }

    // 处理组合选择
    const onCombinationSelect = (index, locus, combination) => {
        const isSelected = tempGroups.value[index].genotype.includes(locus+'<sup>'+combination+'</sup>')
        if (isSelected) {
        // 如果选择了组合，移除对应的位点
        tempGroups.value[index].genotype = tempGroups.value[index].genotype.filter(g => g !== locus)
        } else {
        // 如果取消选择组合，不做额外处理
        }
    }

    return {
        mice,
        loading,
        genotypes,
        allGenotypes,
        tempGroups,
        
        colors,
        groupLetters,

        loadMice,
        loadSurvival,
        loadGenotypes,
        loadInitialData,

        addGroup,
        removeGroup,
        clearGroups,
        getTempGroups,
        getPredefinedGroups,
        onLocusSelect,
        onCombinationSelect
    }
})
