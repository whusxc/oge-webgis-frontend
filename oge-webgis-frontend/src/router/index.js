import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/map'
  },
  {
    path: '/map',
    name: 'MapView',
    component: () => import('@/views/MapView.vue'),
    meta: {
      title: 'OGE-GA+ | 智能地理分析',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '登录 - OGE-GA+',
      requiresAuth: false
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: '控制台 - OGE-GA+',
      requiresAuth: true
    }
  },
  {
    path: '/tools',
    name: 'Tools',
    component: () => import('@/views/Tools.vue'),
    meta: {
      title: 'MCP工具 - OGE-GA+',
      requiresAuth: false
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到 - OGE-GA+'
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title
  }

  // 检查认证状态
  const token = localStorage.getItem('oge_token')
  
  if (to.meta.requiresAuth && !token) {
    // 需要认证但未登录，跳转到登录页
    next({
      name: 'Login',
      query: { redirect: to.fullPath }
    })
  } else if (to.name === 'Login' && token) {
    // 已登录用户访问登录页，跳转到地图页
    next({ name: 'MapView' })
  } else {
    next()
  }
})

router.afterEach((to, from) => {
  // 路由切换后的处理
  console.log(`路由切换: ${from.path} -> ${to.path}`)
})

export default router 