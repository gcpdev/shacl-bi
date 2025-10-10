<template>
  <div class="sidebar flex flex-col w-64 bg-gray-800 text-white">
    <div class="flex items-center justify-center h-16 bg-gray-900">
      <img src="/logo.svg" alt="Logo" class="h-8 w-auto">
      <h1 class="text-lg font-semibold ml-2">SHACL-BI</h1>
    </div>
    <nav class="flex-1 px-2 py-4 space-y-2">
      <router-link v-for="item in menuItems" :key="item.name" :to="item.route" class="flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-700">
        <FontAwesomeIcon :icon="item.icon" class="w-6 h-6 mr-3" />
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
/**
 * SideBar component
 *
 * Side navigation component that provides secondary navigation.
 * Typically includes links to different sections or views of the application.
 *
 * @example
 * // Basic usage in a parent component template:
 * // <SideBar />
 *
 * @prop {Array} [menuItems=[]] - Items to display in the sidebar menu
 * @prop {Boolean} [collapsed=false] - Whether the sidebar is in collapsed state
 * @prop {Boolean} [showToggle=true] - Whether to show collapse/expand toggle
 *
 * @dependencies
 * - vue (Composition API)
 * - vue-router (for navigation)
 *
 * @style
 * - Vertical navigation panel with fixed or flexible width.
 * - Contains styling for navigation links and nested menus.
 * - Often includes collapsible functionality for responsive design.
 * 
 * @returns {HTMLElement} A collapsible sidebar navigation menu that expands on hover,
 * featuring menu items with icons and text labels for different application views,
 * highlighting the currently active item and providing smooth transitions between states.
 */
import { ref, defineProps, watch } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { faHome, faShapes, faProjectDiagram, faRoute, faPuzzlePiece, faPowerOff, faInfo } from '@fortawesome/free-solid-svg-icons';
import ConfirmationModal from './../Reusable/ConfirmationModal.vue';

const emit = defineEmits(['updateView', 'sidebarWidthChanged']);
const confirmationModal = ref(null);
const activeView = ref('Home');
const isExpanded = ref(false);
const sidebarWidth = ref(60);

const menuItems = [
  { name: 'Home', label: 'Home', icon: faHome, route: '/dashboard' },
  { name: 'Shape View', label: 'Shapes', icon: faShapes, route: '/dashboard/shapes' },
  { name: 'About Us', label: 'About Us', icon: faInfo, route: '/dashboard/about-us' }
];

// const menuItems = [
//   { name: 'Home', label: 'Home', icon: faHome, route: '/' },
//   { name: 'Shape View', label: 'Shapes', icon: faShapes, route: '/shapes' },
//   { name: 'Focus Node View', label: 'Focus Nodes', icon: faProjectDiagram, route: '/focus-nodes' },
//   { name: 'Property Path View', label: 'Property Paths', icon: faRoute, route: '/property-paths' },
//   { name: 'Constraint View', label: 'Constraints', icon: faPuzzlePiece, route: '/constraints' },
//   { name: 'About Us', label: 'About Us', icon: faInfo, route: '/about-us' }
// ];


const buttonClicked = (viewName, navigate) => {
  activeView.value = viewName;
  emit('updateView', viewName);
  navigate();
};

const handleLogout = () => {
  confirmationModal.value.show();
};

const logoutConfirmed = () => {
  emit('updateView', 'LandingPage');
};

watch(isExpanded, (newValue) => {
  sidebarWidth.value = newValue ? 250 : 60;
  emit('sidebarWidthChanged', sidebarWidth.value);
});
</script>

<style scoped>
.sidebar {
  transition: width 0.3s ease-in-out;
}

.router-link-exact-active {
  background-color: #4a5568;
}
</style>
