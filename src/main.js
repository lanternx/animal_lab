import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { StoreUtils } from './stores'

const app = createApp(App)
const pinia = createPinia()

function setFavicon() {
  // 移除现有的图标
    const existingIcon = document.querySelector('link[rel="icon"]')
    if (existingIcon) {
        existingIcon.remove()
    }
    
    // 创建新的图标链接
    const link = document.createElement('link')
    link.rel = 'icon'
    link.type = 'image/png'
    link.href = '/src/assets/logo.png' // 使用你的logo.png
    
    // 添加到head
    document.head.appendChild(link)
    
    // 设置页面标题
    document.title = '鼠管家MurisPro - 专业的动物房管理系统'
}

app.use(pinia).use(router)

// 在应用挂载前初始化 Store 数据
StoreUtils.initializeStores()
    .then(() => {
        console.log('内容初始化完成')
    })
    .catch(error => {
        console.error('内容初始化失败:', error)
    })
    .finally(()=>{
        setFavicon()
        app.mount('#app')
    })