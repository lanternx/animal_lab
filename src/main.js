import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { StoreUtils } from './stores'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router)

// 在应用挂载前初始化 Store 数据
StoreUtils.initializeStores()
    .then(() => {
        console.log('内容初始化完成')
        app.mount('#app')
    })
    .catch(error => {
        console.error('内容初始化失败:', error)
        app.mount('#app') // 即使失败也继续挂载应用
    })