<template>
  <div class="main-content bg-image">
    <!-- 主内容区 -->
    <main class="promotion-content">
      <div class="buttons-container">
        <!-- 四个主要按钮 -->
        <a 
          href="https://www.bilibili.com/video/BV1Q12xB6Ep5/" 
          target="_blank" 
          class="promo-button primary"
        >
          <i class="material-icons">play_circle</i>
          <span>视频教程</span>
        </a>

        <a 
          class="promo-button secondary"
        >
          <i class="material-icons">menu_book</i>
          <span>使用文档</span>
        </a>

        <a 
          href="https://github.com/lanternx/MurisPro" 
          target="_blank" 
          class="promo-button accent"
        >
          <i class="material-icons">code</i>
          <span>GitHub仓库</span>
        </a>

        <button 
          class="promo-button qr-button"
          @click="showQrModal = true"
        >
          <i class="material-icons">qr_code_2</i>
          <span>实验动物交流群</span>
        </button>
      </div>
    </main>
    <!-- 二维码弹窗 -->
    <div v-if="showQrModal" class="modal-overlay" @click="showQrModal = false">
      <div class="qr-modal" @click.stop>
        <button class="close-btn" @click="showQrModal = false">
          <i class="material-icons">close</i>
        </button>
        <h3>扫码联系</h3>
        <div class="qr-code-container">
          <img src="@/assets/qrcode.png" alt="qrcode" style="max-height: 450px;">
        </div>
        <p class="qr-tip">使用手机QQ扫描二维码</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 控制二维码弹窗显示
const showQrModal = ref(false)
</script>

<style scoped>

/* 主内容区 */
.promotion-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  text-align: center;
}

.bg-image {
  background: url('@/assets/background.jpg') no-repeat center center fixed;
  background-size: cover;
}

.buttons-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
  max-width: 800px;
  margin-bottom: 3rem;
}

/* 按钮样式 */
.promo-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  text-decoration: none;
  color: #333;
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  min-height: 120px;
}

.promo-button:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 1);
}

.promo-button i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.promo-button span {
  font-size: 1.2rem;
  font-weight: 600;
}

/* 不同按钮颜色 */
.promo-button.primary i { color: #2196F3; }
.promo-button.secondary i { color: #FF9800; }
.promo-button.accent i { color: #9C27B0; }
.promo-button.qr-button i { color: #4CAF50; }

/* 二维码弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.qr-modal {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  position: relative;
  max-height: 700px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalAppear 0.3s ease-out;
}

@keyframes modalAppear {
  from {
    opacity: 0;
    transform: scale(0.8) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background 0.3s;
}

.close-btn:hover {
  background: #f5f5f5;
}

.qr-modal h3 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.5rem;
}

.qr-code-container {
  padding: 1rem;
  background: #f8f8f8;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.qr-tip {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

</style>