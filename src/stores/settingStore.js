import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useSettingStore = defineStore('setting', () => {
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
        loadSettings()
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

    const mouseColumns = [
        { key: 'id', label: '小鼠ID'},
        { key: 'genotype', label: '基因型'},
        { key: 'strain', label: '品系'},
        { key: 'sex', label: '性别'},
        { key: 'birth_date', label: '出生日期'},
        { key: 'death_date', label: '死亡日期'},
        { key: 'days_old', label: '日龄'},
        { key: 'weeks_old', label: '周龄'},
        { key: 'live_status', label: '存活状态'},
        { key: 'cage', label: '笼位'},
        { key: 'tests_planned', label: '计划实验'},
        { key: 'tests_done', label: '完成实验'},
    ]

    const selectedSetting = ref('')
    const settings = ref({'mouse': '小鼠列表'})

    const resetToDefault = (setting) => {
        if (setting === 'mouse') {
            showColumns.value = {
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
            }
        }
    }

    const loadSettings = async () => {
        try {
                const response = await api.get('/setting')
                if (response.data['success']) {
                    showColumns.value = response.data['show_columns']
                }
                console.log('加载显示设置:', showColumns.value)
            } catch (error) {
                console.error('获取显示设置失败:', error)
        }
    }

    const changeSettings = async (type) => {
        try {
                await api.post(`/setting/${type}`, showColumns.value)
                if (type === 'mouse') {
                    console.log('保存显示设置:', showColumns.value)
                }
            } catch (error) {
                console.error('保存显示设置失败:', error)
        }
    }

    return {
        databaseNotChanged,
        trueCurrentDatabase,
        showColumns,
        selectedSetting,
        settings,
        mouseColumns,

        loadInitialData,
        resetToDefault,
        changeSettings
    }
})
