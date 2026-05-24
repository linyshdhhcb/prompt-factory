import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
    },
    {
      path: '/projects',
      name: 'ProjectList',
      component: () => import('@/views/ProjectList.vue'),
    },
    {
      path: '/projects/:id',
      name: 'ProjectDetail',
      component: () => import('@/views/ProjectDetail.vue'),
    },
    {
      path: '/personas',
      name: 'PersonaManage',
      component: () => import('@/views/PersonaManage.vue'),
    },
    {
      path: '/templates',
      name: 'TemplateManage',
      component: () => import('@/views/TemplateManage.vue'),
    },
    {
      path: '/postprocess',
      name: 'PostprocessManage',
      component: () => import('@/views/PostprocessManage.vue'),
    },
    {
      path: '/models',
      name: 'ModelManage',
      component: () => import('@/views/ModelManage.vue'),
    },
  ],
})

export default router
