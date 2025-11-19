import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { StoreUtils } from './stores'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router)

// 在应用启动时检查是否在pywebview环境中
const startApp = async () => {
    try {
        // 先初始化store
        await StoreUtils.initializeStores();
        console.log('内容初始化完成');
        
        // 挂载应用
        app.mount('#app');
    } catch (error) {
        console.error('应用启动失败:', error);
    } finally {
        // 通知后端前端已准备好
        new Promise((resolve) => {
            let attempts = 0;
            const maxAttempts = 50; // 最多尝试5秒（50 * 100ms）
            
            const tryNotify = () => {
                attempts++;
                
                if (window.pywebview && window.pywebview.api) {
                    console.log(`pywebview API就绪 (尝试次数: ${attempts})`);
                    window.pywebview.api.notify_frontend_ready();
                    resolve();
                } else if (attempts < maxAttempts) {
                    setTimeout(tryNotify, 100);
                } else {
                    console.error('❌ 无法连接到pywebview API');
                    resolve(); // 仍然继续，不阻塞应用
                }
            };
            
            tryNotify();
        });
    }
};

// 立即开始启动流程
startApp();