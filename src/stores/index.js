import { useGeneStore } from './geneStore'
import { useCageStore } from './cageStore'
import { useExperimentStore } from './experimentStore'

// 统一导出所有 Store
export { useGeneStore, useCageStore, useExperimentStore }

// // 工具函数
// export const resetAllStores = () => {
//   // 重置所有 store 的状态
//   console.log('重置所有 store')
// }

export class StoreUtils {
  static async initializeStores() {
    // 初始化所有 store 的预加载数据
    const stores = [
      useGeneStore,
      useCageStore,
      useExperimentStore
    ]
  
    for (const Store of stores) {
      await Store().loadInitialData()
    }
  }
}