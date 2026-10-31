import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/tokens.css'
import './styles/base.css'
import { initDataSource } from './composables/useDataSource'

const app = createApp(App)
app.use(createPinia()).use(router).mount('#app')

// 首屏先用内置样例渲染，后端探测在挂载之后异步进行，
// 探到了就整包换源并刷新页面数据，探不到什么都不发生。
void initDataSource()
