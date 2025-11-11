import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
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
            const miceResponse = await api.get('/survival');
            return miceResponse.data;
        } catch (error) {
            console.error('获取基因型数据失败:', error);
        }
    };
    
    const genotypes = ref([])
    const allGenotypes = ref([])

    // 基因型选择
    const selectedGenes = ref([])
    const selectedGeneName = computed(() => {
        return selectedGenes.value.map(g => {
            // 处理野生型情况
            if (g.locus === "WT") {
            return "WT"
            }
            if (g.locus) {
            const alleles = genotypes.value.find(gt => gt.symbol === g.locus).alleles
            const allele1 = g.allele1 ? alleles.find(a => a.id === g.allele1)?.symbol : ""
            const allele2 = g.allele2 ? alleles.find(a => a.id === g.allele2)?.symbol : ""
            return `${g.locus}<sup>${allele1}/${allele2}</sup>`
            } else {
            return ''
            }
        }).join(";")
    })
    const locusSuggestions = computed(() => {
        const hasWT = selectedGenes.value.some(g => g.locus === "WT");
        return selectedGenes.value.map((gene, index) => {
            
            const selectedLoci = selectedGenes.value
            .filter((_, i) => i !== index)
            .map(g => g.locus);
            
            if (hasWT) {
            if (gene.locus === "WT") {
                return genotypes.value.filter(genotype => 
                !selectedLoci.includes(genotype.symbol)
                );
            } else {
                return [genotypes.value.find(genotype => genotype.symbol === "WT")];
            }
            } else {
            return genotypes.value.filter(genotype => 
                !selectedLoci.includes(genotype.symbol)
                );
            }
        });
    });
    const alleleSuggestions = ref([])
    const addable = ref(true)

    const loadAllGenotypes = async () => {
        const genotypeResponse = await api.get('/genotypes')
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

    const onFormLocusChange = (index, locus) => {
        // 查找匹配的基因位点
        const matchedLocus = genotypes.value.find(g => g.symbol === locus);
        // 更新等位基因建议
        alleleSuggestions.value[index] = matchedLocus ? [matchedLocus.alleles, matchedLocus.alleles] : [[], []];
        if (matchedLocus.alleles.length == 1) {
            selectedGenes.value[index].allele1 = matchedLocus.alleles[0].id
            selectedGenes.value[index].allele2 = matchedLocus.alleles[0].id
        } else {
            selectedGenes.value[index].allele1 = null
            selectedGenes.value[index].allele2 = null
        }
        if (locus === "WT") {
            selectedGenes.value = [{'locus': 'WT', 'allele1': null, 'allele2': null}]
            addable.value = false
        } else {
            addable.value = true
        }
    };

    const onFormAlleleChange = (isFirstAllele, index, allele) => {
        const locus = genotypes.value.find(g => g.symbol === selectedGenes.value[index].locus)
        if (!locus) {
            return
        }
        const selectedAllele = locus.alleles.find(a => a.id === allele);
        if (!selectedAllele) {
            return
        }
        const targetArray = isFirstAllele 
            ? alleleSuggestions.value[index][1] 
            : alleleSuggestions.value[index][0];
        if (selectedAllele.is_wildtype) {
            const newArray = targetArray.filter(a => !a.is_wildtype);
            if (isFirstAllele) {
            alleleSuggestions.value[index][1] = newArray;
            } else {
            alleleSuggestions.value[index][0] = newArray;
            }
        } else {
            const alls = locus.alleles
            if (isFirstAllele) {
            alleleSuggestions.value[index][1] = alls
            } else {
            alleleSuggestions.value[index][0] = alls
            }
        }

        if (isFirstAllele && alleleSuggestions.value[index][1].length === 1) {
            selectedGenes.value[index].allele2 = alleleSuggestions.value[index][1][0].id
        }
    }

    const deleteGene = (index) => {
        if ( selectedGenes.value[index].locus === "WT") {
            addable.value = true
        }
        selectedGenes.value.splice(index, 1)
    }

    const addGene = () => {
        selectedGenes.value.push({"locus":'', "allele1":null, "allele2":null})
        alleleSuggestions.value.push([])
    }

    const deleteGenes = () => {
        selectedGenes.value = []
        addable.value = true
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
        selectedGenes,
        selectedGeneName,
        locusSuggestions,
        alleleSuggestions,
        addable,
        
        colors,
        groupLetters,

        loadMice,
        loadSurvival,
        loadGenotypes,
        loadInitialData,
        onFormLocusChange,
        onFormAlleleChange,
        deleteGene,
        addGene,
        deleteGenes,

        addGroup,
        removeGroup,
        clearGroups,
        getTempGroups,
        onLocusSelect,
        onCombinationSelect
    }
})
