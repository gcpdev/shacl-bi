<script setup>
import { computed } from 'vue';
import { useStore } from '../../store';
import HistogramChart from '../Charts/HistogramChart.vue';
import ViolationTable from '../Reusable/ViolationTable.vue';

const store = useStore();

const mainContentData = computed(() => store.mainContentData);

const tags = computed(() => [
  {
    title: 'Total violations',
    value: (mainContentData.value?.violations || []).length,
    maxViolated: 'N/A',
  },
  {
    title: 'Constraint Components',
    value: (mainContentData.value?.constraints || []).length,
    maxViolated: 'N/A',
  },
  {
    title: 'Validation Status',
    value: mainContentData.value?.conforms ? 'Conforms' : 'Violations',
    maxViolated: mainContentData.value?.conforms ? '✅' : '❌',
  },
]);

const constraintComponentHistogramData = computed(() => {
  return {
    labels: (mainContentData.value?.constraints || []).map(c => c.name || 'Unknown'),
    datasets: [
      {
        label: 'Violations',
        backgroundColor: '#EF5350',
        data: (mainContentData.value?.constraints || []).map(c => c.violations || 0),
      },
    ],
  };
});

// Create empty data for other charts since phoenix doesn't provide shapes, paths, or focus nodes
const emptyHistogramData = computed(() => {
  return {
    labels: [],
    datasets: [
      {
        label: 'No Data',
        backgroundColor: '#e0e0e0',
        data: [],
      },
    ],
  };
});

const shapeHistogramData = computed(() => emptyHistogramData.value);
const pathHistogramData = computed(() => emptyHistogramData.value);
const focusNodeHistogramData = computed(() => emptyHistogramData.value);
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- Show loading state if no data -->
    <div v-if="!mainContentData" class="bg-white p-8 rounded-lg shadow text-center">
      <h3 class="text-lg font-semibold text-gray-800 mb-2">No Validation Data</h3>
      <p class="text-gray-600">Please upload files and run validation to see results.</p>
    </div>

    <!-- Show validation results when data is available -->
    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(tag, index) in tags" :key="index" class="bg-white p-4 rounded-lg shadow">
          <h3 class="text-sm font-medium text-gray-500">{{ tag.title }}</h3>
          <p class="text-2xl font-semibold text-gray-800">{{ tag.value }}</p>
          <p class="text-sm font-medium text-gray-500 mt-2">Status</p>
          <p class="text-lg font-semibold" :class="tag.maxViolated === '✅' ? 'text-green-500' : 'text-red-500'">
            {{ tag.maxViolated }}
          </p>
        </div>
      </div>

      <!-- Constraint Component Chart -->
      <div v-if="constraintComponentHistogramData.labels.length > 0" class="bg-white p-4 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-800 mb-2">Violations per Constraint Component</h3>
        <HistogramChart :data="constraintComponentHistogramData" />
      </div>

      <!-- Validation Results Table -->
      <div class="bg-white p-4 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-800 mb-2">Validation Results</h3>
        <div v-if="mainContentData.violations && mainContentData.violations.length > 0">
          <ViolationTable />
        </div>
        <div v-else class="text-center py-8 text-gray-600">
          <p>✅ No violations found. Data conforms to all constraints.</p>
        </div>
      </div>

      </template>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.sm\:grid-cols-2 {
  @media (min-width: 640px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.lg\:grid-cols-2 {
  @media (min-width: 1024px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.lg\:grid-cols-5 {
  @media (min-width: 1024px) {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

.gap-4 {
  gap: 1rem;
}

.p-4 {
  padding: 1rem;
}

.space-y-4 > :not([hidden]) ~ :not([hidden]) {
  --tw-space-y-reverse: 0;
  margin-top: calc(1rem * calc(1 - var(--tw-space-y-reverse)));
  margin-bottom: calc(1rem * var(--tw-space-y-reverse));
}

.bg-white {
  background-color: #fff;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.shadow {
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.text-sm {
  font-size: 0.875rem;
}

.font-medium {
  font-weight: 500;
}

.text-gray-500 {
  color: #6c757d;
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

.mt-2 {
  margin-top: 0.5rem;
}

.text-lg {
  font-size: 1.125rem;
}

.text-orange-500 {
  color: #fd7e14;
}

.mb-2 {
  margin-bottom: 0.5rem;
}
</style>
