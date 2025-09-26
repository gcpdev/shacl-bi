import { createRouter, createWebHistory } from 'vue-router';
import Validation from './components/Validation.vue';
import Violations from './components/Violations.vue';
import ViolationDetails from './components/ViolationDetails.vue';

const routes = [
  {
    path: '/',
    components: {
      default: Validation,
      violations: Violations,
    },
  },
  {
    path: '/violations/:id',
    name: 'violation-details',
    component: ViolationDetails,
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
