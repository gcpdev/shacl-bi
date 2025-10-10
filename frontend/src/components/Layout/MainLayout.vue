<script setup>
/**
 * MainLayout component
 *
 * Root layout component that structures the overall application layout.
 * Typically includes navigation, sidebar, and main content areas.
 *
 * @example
 * // Basic usage in a parent component template:
 * // <MainLayout>
 * //   <template #sidebar>
 * //     <SideBar />
 * //   </template>
 * //   <template #content>
 * //     <MainContent />
 * //   </template>
 * // </MainLayout>
 *
 * @slot sidebar - Content for the sidebar area
 * @slot navigation - Content for the navigation area
 * @slot content - Main content area
 * @slot footer - Footer content area
 *
 * @dependencies
 * - vue (Composition API)
 *
 * @style
 * - CSS grid or flexbox layout for positioning main application sections.
 * - Responsive design that adjusts for different screen sizes.
 * - Contains basic structure styling for the application layout.
 * 
 * @returns {HTMLElement} The primary application layout structure with a top app bar displaying
 * the application title, a collapsible sidebar on the left for navigation, and a main content
 * area on the right that displays the current route's view.
 */
import { ref, onMounted } from 'vue';
import SideBar from './SideBar.vue'; // Import the SideBar component

const isMobile = ref(false); // Track screen size for responsiveness
const activeView = ref("Home"); // Track the currently selected view
const sidebarWidth = ref(60); // Default collapsed sidebar width
const emit = defineEmits(['updateView']);

const handleViewUpdate = (view) => {
  // Emit the selected view to the parent to update the content dynamically
  activeView.value = view;
  emit('updateView', view);
};

const updateSidebarWidth = (width) => {
  sidebarWidth.value = width;
};

// Watch window resize to toggle between mobile and desktop
onMounted(() => {
  const handleResize = () => {
    isMobile.value = window.innerWidth <= 600; // Adjust breakpoint as needed
  };

  window.addEventListener("resize", handleResize);
  handleResize(); // Initial check
});
</script>

<template>
  <div class="flex h-screen bg-gray-100">
    <SideBar />
    <div class="flex-1 flex flex-col overflow-hidden">
      <header class="flex justify-between items-center p-4 bg-white border-b">
        <h1 class="text-2xl font-semibold text-gray-800">SHACL-BI Dashboard</h1>
      </header>
      <main class="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200 p-4">
        <router-view :key="$route.fullPath" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.flex {
  display: flex;
}

.h-screen {
  height: 100vh;
}

.bg-gray-100 {
  background-color: #f4f7f6;
}

.flex-1 {
  flex: 1 1 0%;
}

.flex-col {
  flex-direction: column;
}

.overflow-hidden {
  overflow: hidden;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}

.p-4 {
  padding: 1rem;
}

.bg-white {
  background-color: #fff;
}

.border-b {
  border-bottom-width: 1px;
  border-color: #dee2e6;
}

.text-2xl {
  font-size: 1.5rem;
}

.font-semibold {
  font-weight: 600;
}

.text-gray-800 {
  color: #212529;
}

.overflow-x-hidden {
  overflow-x: hidden;
}

.overflow-y-auto {
  overflow-y: auto;
}

.bg-gray-200 {
  background-color: #f8f9fa;
}
</style>
