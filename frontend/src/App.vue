<template>
  <v-app>
    <router-view :key="$route.fullPath" />
  </v-app>
</template>

<script setup>
// The router-view will automatically render the correct component based on the route
// No need for manual state management
</script>

<style scoped>
html, body, #app {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
}

v-app {
  height: 100%;
  width: 100%;
  padding: 0 !important;
  display: flex;
}

.v-application, .v-application-wrapper {
  width: 100vw !important;
  max-width: 100vw !important;
  min-height: 100vh;
}
</style>