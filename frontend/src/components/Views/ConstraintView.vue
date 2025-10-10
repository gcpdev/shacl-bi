<template>
  <div class="constraint-view p-4">
    <!-- Back Button Section -->
    <button @click="goBack" class="bg-blue-500 text-white px-4 py-2 rounded mb-4">
      Back to Overview
    </button>

    <!-- Header Section -->
    <div class="header-section mb-6">
      <h1 class="text-2xl font-bold mb-2 text-primary">Constraint: {{ currentConstraintName  }}</h1>
      <div class="header-content flex justify-between items-center bg-gray-100 p-4 rounded">
        <div>
          <p class="font-medium">Constraint Type:</p>
          <code class="text-sm bg-gray-200 p-1 rounded">{{ currentConstraintName  }}</code>
        </div>
        <div>
          <p class="font-medium">Total Violations: <span class="text-red-500 font-bold">{{ totalViolations }}</span></p>
        </div>
      </div>
    </div>

    <!-- Main Content Section -->
    <div class="main-content space-y-6">
      <!-- Key Metrics -->
      <div class="key-metrics grid grid-cols-4 gap-4">
        <Metrics />
      </div>

      <!-- Plots Section -->
      <div class="plots-section grid grid-cols-3 gap-4">
        <div class="plot bg-gray-100 p-4 rounded">
          <h3 class="text-md font-medium">1. Violation Distribution</h3>
          <BarChart
            :title="'Distribution of Violations'"
            :xAxisLabel="'Shapes'"
            :yAxisLabel="'Violations'"
            :data="barChartData"
          />
        </div>
        <div class="plot bg-gray-100 p-4 rounded">
          <h3 class="text-md font-medium">2. Violation Severity</h3>
          <BarChart
            :title="'Constraint Violation Breakdown'"
            :xAxisLabel="'Property Paths'"
            :yAxisLabel="'Violations'"
            :data="barChartData"
          />
        </div>
        <div class="plot bg-gray-100 p-4 rounded">
          <h3 class="text-md font-medium">3. Constraint Breakdown</h3>
          <BarChart
            :title="'Constraint Violation Breakdown'"
            :xAxisLabel="'Property Paths'"
            :yAxisLabel="'Violations'"
            :data="barChartData"
          />
        </div>
      </div>
    </div>

    <!-- Bottom Section -->
    <div class="bottom-section bg-gray-100 p-4 rounded mt-6">
      <h2 class="text-lg font-semibold mb-4">Example Violations</h2>
      <div class="violations-table">
        <table class="table-auto w-full text-left border-collapse border border-gray-300">
          <thead class="bg-gray-200">
            <tr>
              <th class="border border-gray-300 px-4 py-2">Focus Node</th>
              <th class="border border-gray-300 px-4 py-2">Property Path</th>
              <th class="border border-gray-300 px-4 py-2">Constraint</th>
              <th class="border border-gray-300 px-4 py-2">Message</th>
              <th class="border border-gray-300 px-4 py-2">Explanation</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(violation, index) in violations" :key="violation.id" class="hover:bg-gray-50">
              <td class="border border-gray-300 px-4 py-2">{{ violation.focusNode }}</td>
              <td class="border border-gray-300 px-4 py-2">{{ violation.propertyPath }}</td>
              <td class="border border-gray-300 px-4 py-2">{{ violation.constraint }}</td>
              <td class="border border-gray-300 px-4 py-2">{{ violation.message }}</td>
              <td class="border border-gray-300 px-4 py-2">{{ explanations[index]?.explanation_natural_language }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Metrics from "./../ConstraintView/Metrics.vue";
import BarChart from './../Charts/BarChart.vue';

import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const currentConstraintId = route.params.constraintId;
const currentConstraintName = route.params.constraintName || 'Unknown';
const totalViolations = route.params.constraintViolations;
const validationReport = route.params.validationReport;
const explanations = route.params.explanations;

const violations = ref([]);

const barChartData = ref({
  labels: ['Shape 1', 'Shape 2', 'Shape 3'],
  datasets: [
    {
      label: 'Violations',
      data: [5, 10, 15],
      backgroundColor: ['rgba(255, 99, 132, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(75, 192, 192, 0.2)'],
      borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(75, 192, 192, 1)'],
      borderWidth: 1,
    },
  ],
});

onMounted(() => {
  if (validationReport) {
    const report = JSON.parse(validationReport);
    violations.value = report['@graph'].map(v => ({
      id: v['@id'],
      focusNode: v['http://www.w3.org/ns/shacl#focusNode']['@id'],
      propertyPath: v['http://www.w3.org/ns/shacl#resultPath']['@id'],
      constraint: v['http://www.w3.org/ns/shacl#sourceConstraintComponent']['@id'],
      message: v['http://www.w3.org/ns/shacl#resultMessage'],
    }));
  }
});

// Go back to the overview page
const goBack = () => {
  router.push({ name: "ConstraintOverview" }); // Make sure the route name matches your route configuration
};
</script>
