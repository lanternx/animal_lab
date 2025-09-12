import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/DashBoard.vue'
import MiceView from '../views/MiceView.vue';


const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  }
  ,
  {
    path: '/mice',
    name: 'mice',
    component: MiceView
  },
  // 添加404处理
  { 
    path: '/:pathMatch(.*)*', 
    component: () => import('../views/NotFound.vue') 
  },
  {
  path: '/mouse/:id',
  name: 'MouseDetail',
  component: () => import('../views/MouseDetailView.vue')
},
  {
  path: '/weight',
  name: 'BodyWeight',
  component: () => import('../views/BodyWeight.vue')
},
  {
  path: '/survival',
  name: 'Survivalplot',
  component: () => import('../views/Survival.vue')
},
  {
  path: '/setting',
  name: 'SystemSettings',
  component: () => import('../views/Setting.vue')
}
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
