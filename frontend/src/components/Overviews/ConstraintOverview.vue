<template>
  <div class="constraint-overview p-4">
    <!-- Tags Section -->
    <div class="grid grid-cols-4 gap-4 mb-4">
      <div
        v-for="(tag, index) in tags"
        :key="index"
        class="flex flex-row items-center bg-white rounded-lg shadow p-6 hover:shadow-md transition"
      >
      <div class="flex-grow">
          <h3 class="text-sm font-medium text-gray-600 mb-1">{{ tag.title }}</h3>
          <p class="text-3xl font-bold text-gray-800">{{ tag.value }}</p>
        </div>
        <div class="flex items-center justify-center bg-gray-200 rounded-full w-12 h-12">
          <!-- Replace with a relevant icon -->
          <font-awesome-icon :icon="['fas', 'chart-bar']" class="text-gray-600" />
        </div>
      </div>
    </div>

    <!-- Plots Section -->
    <div class="grid grid-cols-3 gap-4 mb-4">
      <BarChart
        :title="'Violations by Constraint Type'"
        :xAxisLabel="'Constraint Types'"
        :yAxisLabel="'Number of Violations'"
        :data="violationsByConstraintType"
      />

      <!-- Usage Distribution -->
      <PieChart
        :title="'Usage Distribution'"
        :data="usageDistributionData"
        :categories="usageLabels"
      />

      <!-- Violation Distribution by Constraint Component -->
      <HistogramChart
        :title="'Violation Distribution by Constraint Component'"
        :xAxisLabel="'Violation Count'"
        :yAxisLabel="'Number of Constraint Components'"
        :data="histogramData"
      />

    </div>

    <!-- Generate Tables for Each Category -->
    <div v-for="category in uniqueCategories" :key="category" class="category-section mb-4">

      <div class="bg-white border border-gray-200 p-6 rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold text-gray-700 mb-4">{{ category }}</h2>
        <table class="w-full border-collapse table-fixed">
          <thead class="bg-gray-200">
            <tr>
              <th class="text-left px-6 py-3 border-b border-gray-300 text-gray-600 font-medium w-1/4">
                Constraint Name
              </th>
              <th class="text-left px-6 py-3 border-b border-gray-300 text-gray-600 font-medium w-1/3">
                Description
              </th>
              <th class="text-left px-6 py-3 border-b border-gray-300 text-gray-600 font-medium w-1/6">
                Severity
              </th>
              <th class="text-left px-6 py-3 border-b border-gray-300 text-gray-600 font-medium w-1/6">
                Number of Violations
              </th>
              <th class="text-center px-6 py-3 border-b border-gray-300 text-gray-600 font-medium w-1/12"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="constraint in constraintsByCategory(category)"
              :key="constraint.id"
              class="even:bg-gray-50 hover:bg-blue-50 transition-colors"
              @click="goToConstraintView(constraint)"
            >
              <td class="px-6 py-4 border-b border-gray-300">{{ constraint.name }}</td>
              <td class="px-6 py-4 border-b border-gray-300">{{ constraint.description }}</td>
              <td class="px-6 py-4 border-b border-gray-300">{{ constraint.severity }}</td>
              <td class="px-6 py-4 border-b border-gray-300">{{ constraint.violations }}</td>
              <td class="px-6 py-4 border-b border-gray-300 text-center">
                <button class="text-blue-600 hover:text-blue-800">
                  <font-awesome-icon icon="arrow-right" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ConstraintOverview component
 *
 * Provides a comprehensive overview of SHACL constraints in the dataset.
 * Displays statistics, visualizations, and listings of constraints with their usage and violations.
 *
 * @example
 * // Basic usage in a parent component template:
 * // <ConstraintOverview />
 *
 * @prop {Array} [constraints=[]] - List of constraints to display
 * @prop {Boolean} [showViolations=true] - Whether to show violation data
 * @prop {Boolean} [showCharts=true] - Whether to show visualization charts
 *
 * @dependencies
 * - vue (Composition API)
 * - ../Charts/GroupedBarChart.vue
 * - ../ConstraintView/Metrics.vue
 *
 * @style
 * - Responsive layout with cards and data tables.
 * - Data visualization components for constraint statistics.
 * - Filterable and sortable constraint listings.
 * 
 * @returns {HTMLElement} A dashboard page showing constraint statistics in summary cards at the 
 * top, data visualizations in the middle (bar chart, pie chart, and histogram), and a categorized 
 * table listing all constraints with their properties and violation counts at the bottom.
 */
// Importing components
import BarChart from './../Charts/BarChart.vue';
import PieChart from './../Charts/PieChart.vue';
import HistogramChart from './../Charts/HistogramChart.vue';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from '../../store';

const store = useStore();

// Router for navigation
const router = useRouter();

const constraints = computed(() => store.mainContentData?.constraints || []);

// Tags for summary
const tags = computed(() => {
  const totalConstraints = constraints.value.length;
  const constraintsWithViolations = constraints.value.filter(c => c.violations > 0).length;
  const percentageViolations = totalConstraints > 0 ? Math.round((constraintsWithViolations / totalConstraints) * 100) : 0;
  const mostViolated = constraints.value.reduce((prev, current) => (prev.violations > current.violations) ? prev : current, {});
  const avgViolations = totalConstraints > 0 ? (constraints.value.reduce((sum, c) => sum + c.violations, 0) / totalConstraints).toFixed(2) : 0;

  return [
    { title: 'Total Constraint Types', value: totalConstraints },
    { title: 'Constraints with Violations', value: `${constraintsWithViolations} (${percentageViolations}%)` },
    { title: 'Most Violated Constraint Type', value: mostViolated.name },
    { title: 'Average Violations per Constraint', value: avgViolations },
  ];
});

// Helper function to categorize constraints dynamically
const categorizeConstraint = (constraint) => {
  if (constraint.name.includes('sh:class') || constraint.name.includes('sh:datatype') || constraint.name.includes('sh:nodeKind')) {
    return 'Value Type Constraint Components';
  }
  if (constraint.name.includes('sh:minCount') || constraint.name.includes('sh:maxCount')) {
    return 'Cardinality Constraint Components';
  }
  if (constraint.name.includes('sh:minExclusive') || constraint.name.includes('sh:minInclusive') || constraint.name.includes('sh:maxExclusive')) {
    return 'Value Range Constraint Components';
  }
  if (constraint.name.includes('sh:minLength') || constraint.name.includes('sh:maxLength')) {
    return 'String-based Constraint Components';
  }
  if (constraint.name.includes('sh:equals') || constraint.name.includes('sh:disjoint')) {
    return 'Property Pair Constraint Components';
  }
  if (constraint.name.includes('sh:not') || constraint.name.includes('sh:and') || constraint.name.includes('sh:or') || constraint.name.includes('sh:xone')) {
    return 'Logical Constraint Components';
  }
  if (constraint.name.includes('sh:node') || constraint.name.includes('sh:property')) {
    return 'Shape-based Constraint Components';
  }
  return 'Other Constraint Components';
};

// Categorize constraints
const constraintsWithCategory = computed(() => constraints.value.map(constraint => ({
  ...constraint,
  category: categorizeConstraint(constraint),
})));

// Unique categories
const uniqueCategories = computed(() => [...new Set(constraintsWithCategory.value.map(c => c.category))]);

// Get constraints by category
const constraintsByCategory = category =>
  constraintsWithCategory.value.filter(constraint => constraint.category === category);

// Charts data
const violationsByConstraintType = computed(() => ({
  labels: constraints.value.map(constraint => constraint.name),
  datasets: [
    {
      label: 'Number of Violations',
      data: constraints.value.map(constraint => constraint.violations),
      backgroundColor: '#FF5252',
    },
  ],
}));

const histogramData = computed(() => store.mainContentData?.constraintHistogramData || {});

const usageDistributionData = computed(() => constraints.value.map(c => c.violations));
const usageLabels = computed(() => constraints.value.map(c => c.name));

// Navigation
const goToConstraintView = (constraint) => {
  router.push({ 
    name: 'ConstraintView', 
    params: { 
      constraintId: constraint.id, 
      constraintName: constraint.name, 
      constraintViolations: constraint.violations,
      validationReport: JSON.stringify(store.mainContentData.report_graph),
      explanations: store.mainContentData.explanations
    } 
  });
};
</script>

<style scoped>
.category-section {
  margin-bottom: 30px;
}

.table-container {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.table-fixed {
  table-layout: fixed;
}

th,
td {
  padding: 12px;
}

th.w-1\/4,
td.w-1\/4 {
  width: 25%;
}

th.w-1\/3,
td.w-1\/3 {
  width: 33.33%;
}

th.w-1\/6,
td.w-1\/6 {
  width: 16.67%;
}

th.w-1\/12,
td.w-1\/12 {
  width: 8.33%;
}

tbody tr:hover {
  background-color: #f0f8ff;
}

tbody tr {
  cursor: pointer;
}


.constraint-overview {
    display: flex;
    flex-direction: column;
    gap: 1rem; /* Match the spacing between sections */
}

.grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem; /* Match the spacing for plots */
}

.grid-cols-3 {
    gap: 1rem; /* Match the gap in PropertyPathOverview */
}

.grid-cols-4 {
    grid-template-columns: repeat(4, 1fr);

}

.category-section {
    margin-bottom: 1.5rem; /* Ensure uniform spacing for tables */
}


.table-container {
    margin-bottom: 1.5rem; /* Consistent spacing for tables */
    padding: 1rem;
}
</style>
