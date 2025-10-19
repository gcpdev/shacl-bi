<template>
  <div class="main-content p-4">
    <!-- Tags Section -->
    <div class="grid gap-6 mb-6"
     style="grid-template-columns: minmax(150px, 0.2fr) 1fr 1fr 1fr 1fr;">
     <div
  v-for="(tag, index) in tags"
  :key="index"
  class="card flex flex-col sm:flex-row items-center justify-center text-center bg-white shadow rounded-lg p-6 hover:shadow-md transition"
>
  <div class="flex-grow flex flex-col items-center text-center">
    <h3 class="text-xs sm:text-sm md:text-base font-medium text-gray-500 mb-1">
      {{ tag.title }}
    </h3>
    <p class="font-bold text-[18px] text-gray-800">
      {{ tag.value }}
    </p>
      <!-- Added spacing here -->
    <div class="h-4 sm:h-5"></div> <!-- Spacer div for consistent spacing -->
    <h3 v-if="tag.titleMaxViolated" class="text-xs sm:text-sm md:text-base font-medium text-gray-500 mb-1">
      {{ tag.titleMaxViolated }}
    </h3>
    <p v-if="tag.maxViolated && tag.titleMaxViolated" class="font-bold text-[18px]" :style="{ color: 'rgb(227,114,34)' }">
      {{ tag.maxViolated }}
    </p>
  </div>
</div>
</div>

    <!-- Plots Section -->
    <!-- <div class="grid grid-cols-3 gap-6 mb-6">
      <BoxPlot
        title="Violation distribution over shapes"
        x-axis-label=""
        y-axis-label="Violations"
        :data="[1, 2, 2, 3, 4, 4, 4, 5, 5, 6, 7, 8, 9, 20]"
        class="card bg-white shadow-lg rounded-lg p-6"
      />
      <BoxPlot
        title="Violation distribution over paths"
        x-axis-label=""
        y-axis-label="Violations"
        :data="[1, 2, 2, 3, 4, 4, 4, 5, 5, 6, 7, 8, 9, 10]"
        class="card bg-white shadow-lg rounded-lg p-6"
      />
      <BoxPlot
        title="Violation distribution over focus nodes"
        x-axis-label=""
        y-axis-label="Violations"
        :data="[1, 2, 2, 3, 4, 4, 4, 5, 5, 6, 7, 8, 9, 50]"
        class="card bg-white shadow-lg rounded-lg p-6"
      />
    </div> -->
<!-- 
    <div class="grid grid-cols-3 gap-6 mb-6">
      <PieChart
        :title="'Violations per Shape'"
        :data="[72895, 83152, 80072, 39881, 14234, 7881, 86552, 98522, 79683, 13240]"
        :categories="['Shape A', 'Shape B', 'Shape C', 'Shape D', 'Shape E', 'Shape F', 'Shape G', 'Shape H', 'Shape I', 'Shape J']"
        class="card bg-white shadow-lg rounded-lg p-6"
      />
      <PieChart
        :title="'Violations per Path'"
        :data="[71491, 64036, 89818, 98656, 99242, 81159, 97923, 11101, 76166, 96080]"
        :categories="['Path A', 'Path B', 'Path C', 'Path D', 'Path E', 'Path F', 'Path G', 'Path H', 'Path I', 'Path J']"
        class="card bg-white shadow-lg rounded-lg p-6"
      />
      <PieChart
        :title="'Violations per Focus Node'"
        :data="[10496, 53213, 34641, 92937, 97444, 92112, 66890, 49144, 1061, 11078]"
        :categories="['Focus Node A', 'Focus Node B', 'Focus Node C', 'Focus Node D', 'Focus Node E', 'Focus Node F', 'Focus Node G', 'Focus Node H', 'Focus Node I', 'Focus Node J']"
        class="card bg-white shadow-lg rounded-lg p-6"
      />
    </div> -->
<!-- Histograms Section -->
<div class="grid grid-cols-4 gap-4 mb-4 w-full max-w-full overflow-hidden transition">
      <!-- Histogram for Violations per Shape -->
      <HistogramChart
        :title="`<span style='color: rgba(154, 188, 228);; font-weight: bold;'>Violations per Node Shape</span>`"
        titleAlign="center"
        :xAxisLabel="'Number of Violations (Bins)'"
        :yAxisLabel="'Frequency'"
        :data="shapeHistogramData"
      />

      <!-- Histogram for Violations per Path -->
      <HistogramChart
        :title="`<span style='color: rgba(94, 148, 212, 1);; font-weight: bold;'>Violations per Path</span>`"
        :xAxisLabel="'Number of Violations (Bins)'"
        :yAxisLabel="'Frequency'"
        :data="pathHistogramData"
      />

      <!-- Histogram for Violations per Focus Node -->
      <HistogramChart
        :title="`<span style='color: rgba(22, 93, 177, 1);; font-weight: bold;'>Violations per Focus Node</span>`"
        :xAxisLabel="'Number of Violations (Bins)'"
        :yAxisLabel="'Frequency'"
        :data="focusNodeHistogramData"
      />

      <HistogramChart
        :title="`<span style='color: rgba(10, 45, 87);; font-weight: bold;'>Violations per Constraint Component</span>`"
        :xAxisLabel="'Number of Violations (Bins)'"
        :yAxisLabel="'Frequency'"
        :data="constraintComponentHistogramData"
      />
    </div>

    <!-- Table Section -->
    <ViolationTable class="card bg-white shadow-lg rounded-lg p-6 w-full max-w-full overflow-hidden" style="grid-column: span 3;" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import HistogramChart from "./../Charts/HistogramChart.vue";
import PieChart from "./../Charts/PieChart.vue";
import Tag from "./../Reusable/Tag.vue";
import ViolationTable from "./../Reusable/ViolationTable.vue";
import api from "@/utils/api";

const dashboardData = ref(null);

onMounted(async () => {
    try {
        // Get session ID from localStorage if available
        const sessionId = localStorage.getItem('shacl_session_id');
        const response = await api.getDashboardData(sessionId);
        dashboardData.value = response.data;
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
        dashboardData.value = {
            tags: [
                { "title": "Total Violations", "value": 0, "titleMaxViolated": "", "maxViolated": "" },
                { "title": "Violated Node Shapes", "value": "0/0", "titleMaxViolated": "Most Violated Node Shape", "maxViolated": "No data" },
                { "title": "Violated Paths", "value": "0/0", "titleMaxViolated": "Most Violated Path", "maxViolated": "No data" },
                { "title": "Violated Focus Nodes", "value": 0, "titleMaxViolated": "Most Violated Focus Node", "maxViolated": "No data" },
                { "title": "Violated Constraint Components", "value": "0/0", "titleMaxViolated": "Most Violated Constraint Component", "maxViolated": "No data" },
            ],
            shapeHistogramData: [],
            pathHistogramData: [],
            focusNodeHistogramData: [],
            constraintComponentHistogramData: []
        };
    }
});

const tags = computed(() => {
    const rawTags = dashboardData.value?.tags || [];

    // Helper function to extract short name from URI
    const getShortName = (uri) => {
        if (!uri) return 'No data';
        if (uri.startsWith('nodeID://')) return uri.replace('nodeID://', 'Node ');
        if (uri.startsWith('http://')) {
            const parts = uri.split(/[/#]/);
            return parts[parts.length - 1] || parts[parts.length - 2] || 'Unknown';
        }
        return uri;
    };

    // Transform tags to use short names for maxViolated fields
    return rawTags.map(tag => ({
        ...tag,
        maxViolated: getShortName(tag.maxViolated)
    }));
});

const shapeHistogramData = computed(() => {
    if (!dashboardData.value) return { labels: [], datasets: [] };
    if (!dashboardData.value.shapeHistogramData) return { labels: [], datasets: [] };

    const histogramData = dashboardData.value.shapeHistogramData;

    // Check if data is already in Chart.js format or needs conversion
    if (histogramData.labels && histogramData.datasets) {
        // Already in Chart.js format - just return it
        return histogramData;
    }

    // Convert from [[label, count], ...] format to Chart.js format
    if (!Array.isArray(histogramData) || histogramData.length === 0) return { labels: [], datasets: [] };

    // Helper function to extract short name from URI
    const getShortName = (uri) => {
        if (!uri) return 'Unknown';
        if (uri.startsWith('nodeID://')) return uri.replace('nodeID://', 'Node ');
        if (uri.startsWith('http://')) {
            const parts = uri.split(/[/#]/);
            return parts[parts.length - 1] || parts[parts.length - 2] || 'Unknown';
        }
        return uri;
    };

    return {
        labels: histogramData.map(item => getShortName(item[0])),
        datasets: [{
            label: 'Frequency',
            data: histogramData.map(item => item[1]),
            backgroundColor: 'rgba(154, 188, 228, 0.6)',
            borderColor: 'rgba(154, 188, 228, 1)',
            borderWidth: 1
        }]
    };
});

const pathHistogramData = computed(() => {
    if (!dashboardData.value) return { labels: [], datasets: [] };
    if (!dashboardData.value.pathHistogramData) return { labels: [], datasets: [] };

    const histogramData = dashboardData.value.pathHistogramData;

    // Check if data is already in Chart.js format or needs conversion
    if (histogramData.labels && histogramData.datasets) {
        // Already in Chart.js format - just return it
        return histogramData;
    }

    // Convert from [[label, count], ...] format to Chart.js format
    if (!Array.isArray(histogramData) || histogramData.length === 0) return { labels: [], datasets: [] };

    // Helper function to extract short name from URI
    const getShortName = (uri) => {
        if (!uri) return 'Unknown';
        if (uri.startsWith('nodeID://')) return uri.replace('nodeID://', 'Node ');
        if (uri.startsWith('http://')) {
            const parts = uri.split(/[/#]/);
            return parts[parts.length - 1] || parts[parts.length - 2] || 'Unknown';
        }
        return uri;
    };

    return {
        labels: histogramData.map(item => getShortName(item[0])),
        datasets: [{
            label: 'Frequency',
            data: histogramData.map(item => item[1]),
            backgroundColor: 'rgba(94, 148, 212, 0.6)',
            borderColor: 'rgba(94, 148, 212, 1)',
            borderWidth: 1
        }]
    };
});

const focusNodeHistogramData = computed(() => {
    if (!dashboardData.value) return { labels: [], datasets: [] };
    if (!dashboardData.value.focusNodeHistogramData) return { labels: [], datasets: [] };

    const histogramData = dashboardData.value.focusNodeHistogramData;

    // Check if data is already in Chart.js format or needs conversion
    if (histogramData.labels && histogramData.datasets) {
        // Already in Chart.js format - just return it
        return histogramData;
    }

    // Convert from [[label, count], ...] format to Chart.js format
    if (!Array.isArray(histogramData) || histogramData.length === 0) return { labels: [], datasets: [] };

    // Helper function to extract short name from URI
    const getShortName = (uri) => {
        if (!uri) return 'Unknown';
        if (uri.startsWith('nodeID://')) return uri.replace('nodeID://', 'Node ');
        if (uri.startsWith('http://')) {
            const parts = uri.split(/[/#]/);
            return parts[parts.length - 1] || parts[parts.length - 2] || 'Unknown';
        }
        return uri;
    };

    return {
        labels: histogramData.map(item => getShortName(item[0])),
        datasets: [{
            label: 'Frequency',
            data: histogramData.map(item => item[1]),
            backgroundColor: 'rgba(22, 93, 177, 0.6)',
            borderColor: 'rgba(22, 93, 177, 1)',
            borderWidth: 1
        }]
    };
});

const constraintComponentHistogramData = computed(() => {
    if (!dashboardData.value) return { labels: [], datasets: [] };
    if (!dashboardData.value.constraintComponentHistogramData) return { labels: [], datasets: [] };

    const histogramData = dashboardData.value.constraintComponentHistogramData;

    // Check if data is already in Chart.js format or needs conversion
    if (histogramData.labels && histogramData.datasets) {
        // Already in Chart.js format - just return it
        return histogramData;
    }

    // Convert from [[label, count], ...] format to Chart.js format
    if (!Array.isArray(histogramData) || histogramData.length === 0) return { labels: [], datasets: [] };

    // Helper function to extract short name from URI
    const getShortName = (uri) => {
        if (!uri) return 'Unknown';
        if (uri.startsWith('nodeID://')) return uri.replace('nodeID://', 'Node ');
        if (uri.startsWith('http://')) {
            const parts = uri.split(/[/#]/);
            return parts[parts.length - 1] || parts[parts.length - 2] || 'Unknown';
        }
        return uri;
    };

    return {
        labels: histogramData.map(item => getShortName(item[0])),
        datasets: [{
            label: 'Frequency',
            data: histogramData.map(item => item[1]),
            backgroundColor: 'rgba(10, 45, 87, 0.6)',
            borderColor: 'rgba(10, 45, 87, 1)',
            borderWidth: 1
        }]
    };
});
</script>

<style scoped>
.main-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.grid-cols-3 {
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.card {
  transition: box-shadow 0.2s ease-in-out;
}

.card:hover {
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

</style>
