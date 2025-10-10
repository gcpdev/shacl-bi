<template>
  <div class="shape-overview p-4">
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
      </div>
    </div>

    <!-- Plots Section -->
    <div class="grid grid-cols-3 gap-4 mb-4">
      <HistogramChart
        :title="'Distribution of Violations per Constraint'"
        :xAxisLabel="'Number of Violations per Constraint'"
        :yAxisLabel="'Number of Node Shapes'"
        :data="normalizedHistogramViolationData"
        :explanationText="'This scatter plot shows how violations correlate with the number of constraints 1.'"
      />
      <ScatterPlotChart
        :title="'Correlation Between Constraints and Violations'"
        :xAxisLabel="'Number of Constraints'"
        :yAxisLabel="'Violations / Constraint'"
        :data="coveragePlotData"
        :showQuadrants="true"
        :explanationText="'This scatter plot shows how violations correlate with the number of constraints 1.'"
      />
      <ScatterPlotChart
        :title="'Violation Diversity and Intensity'"
        :xAxisLabel="'Entropy of Constraint Violations'"
        :yAxisLabel="'Violations / Constraints'"
        :data="scatterPlotData"
        :showQuadrants="true"
        :explanationText="'This scatter plot shows how violations correlate with the number of constraints 2.'"

      />
    </div>

    <!-- Table Section -->
    <div class="bg-white border border-gray-200 p-6 rounded-lg shadow-lg">
      <h2 class="text-2xl font-bold text-gray-700 mb-4">Shape Details</h2>
      <table class="w-full border-collapse">
        <thead class="bg-gray-200">
          <tr>
            <th 
              v-for="(column, index) in columns" 
              :key="index" 
              class="text-left px-6 py-3 border-b border-gray-300 text-gray-600 font-medium cursor-pointer"
              @click="sortColumn(column)">
              {{ column.label }}
              <span class="sort-indicator" >
                {{ sortKey === column.field ? (sortOrder === 'asc' ? ' ▲' : ' ▼') : '' }}
              </span>
            </th>
            <th class="text-center px-6 py-3 border-b border-gray-300 text-gray-600 font-medium"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="shape in sortedPaginatedData" 
            :key="shape.id" 
            class="even:bg-gray-50 hover:bg-blue-50 transition-colors"
            @click="goToShape(shape)">
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.name }}</td>
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.violations }}</td>
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.propertyShapes }}</td>
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.focusNodes }}</td>
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.propertyPaths }}</td>
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.mostViolatedConstraint }}</td>
            <td class="px-6 py-4 border-b border-gray-300">{{ shape.violationToConstraintRatio }}</td>
            <td class="px-6 py-4 border-b border-gray-300 text-center">
              <button class="text-blue-600 hover:text-blue-800">
                <font-awesome-icon icon="arrow-right" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="flex justify-between items-center mt-4">
        <button
          :disabled="currentPage === 1"
          @click="prevPage"
          class="px-4 py-2 bg-gray-200 text-gray-600 rounded hover:bg-gray-300 disabled:opacity-50">
          Previous
        </button>
        <span class="text-gray-700">Page {{ currentPage }} of {{ totalPages }}</span>
        <button
          :disabled="currentPage === totalPages"
          @click="nextPage"
          class="px-4 py-2 bg-gray-200 text-gray-600 rounded hover:bg-gray-300 disabled:opacity-50">
          Next
        </button>
      </div>
    </div>
  </div>
</template>


<script setup>
/**
 * ShapeOverview component
 *
 * Provides a comprehensive overview of SHACL shapes in the dataset.
 * Displays statistics, visualizations, and listings of shapes with their constraints and validation results.
 *
 * @example
 * // Basic usage in a parent component template:
 * // <ShapeOverview />
 *
 * @prop {Array} [shapes=[]] - List of shapes to display
 * @prop {Boolean} [showViolations=true] - Whether to show violation data
 * @prop {Boolean} [showCharts=true] - Whether to show visualization charts
 *
 * @dependencies
 * - vue (Composition API)
 * - ../Charts/PieChart.vue
 * - ../Charts/GroupedBarChart.vue
 *
 * @style
 * - Responsive layout with cards and data tables.
 * - Data visualization components for shape statistics.
 * - Filterable and sortable shape listings with expandable details.
 * 
 * @returns {HTMLElement} A dashboard page showing shape statistics in summary cards at the top,
 * three data visualizations (histogram and scatter plots) in the middle, and a sortable, paginated 
 * data table listing all node shapes with their metrics and violation details at the bottom.
 */
// Importing components
import HistogramChart from './../Charts/HistogramChart.vue';
import ScatterPlotChart from './../Charts/ScatterPlotChart.vue';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from '../../store';

const store = useStore();

const coveragePlotData = computed(() => store.mainContentData?.coveragePlotData || {});
const scatterPlotData = computed(() => store.mainContentData?.scatterPlotData || {});

// Router for navigation
const router = useRouter();

const tags = computed(() => {
  const shapes = store.mainContentData?.shapes || [];
  const totalShapes = shapes.length;
  const shapesWithViolations = shapes.filter(shape => shape.violations > 0).length;
  const percentageViolations = totalShapes > 0 ? Math.round((shapesWithViolations / totalShapes) * 100) : 0;
  const maxViolations = Math.max(...shapes.map(shape => shape.violations));
  const avgViolations = totalShapes > 0 ? (shapes.reduce((acc, shape) => acc + shape.violations, 0) / totalShapes).toFixed(2) : 0;

  return [
    { title: "Total Node Shapes", value: totalShapes },
    { title: "Node Shapes with Violations (%)", value: `${percentageViolations}%` },
    { title: "Max Violations per Node Shape", value: maxViolations },
    { title: "Avg Violations per Node Shape", value: avgViolations },
  ];
});

const normalizedHistogramViolationData = computed(() => store.mainContentData?.shapeConstraintHistogram || {});

const columns = ref([
  { label: "Node Shape Name", field: "name" },
  { label: "Violations", field: "violations" },
  { label: "Number of Property Shapes", field: "propertyShapes" },
  { label: "Focus Nodes Affected", field: "focusNodes" },
  { label: "Property Paths", field: "propertyPaths" },
  { label: "Most Violated Constraint Component", field: "mostViolatedConstraint" },
  { label: "Violation-to-Constraint Ratio", field: "violationToConstraintRatio" },
]);

const shapes = computed(() => store.mainContentData?.shapes || []);

const currentPage = ref(1);
const pageSize = ref(10);
const totalPages = computed(() => Math.ceil(shapes.value.length / pageSize.value));

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return shapes.value.slice(start, start + pageSize.value);
});

const sortedPaginatedData = computed(() => {
  const data = paginatedData.value;
  if (sortKey.value) {
    return [...data].sort((a, b) => {
      const result = a[sortKey.value].toString().localeCompare(b[sortKey.value].toString(), undefined, { numeric: true });
      return sortOrder.value === "asc" ? result : -result;
    });
  }
  return data;
});

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--;
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++;
};

const goToShape = (shape) => {
  router.push({ name: "ShapeView", params: { shapeId: shape.id } });
};

const sortKey = ref("");
const sortOrder = ref("asc");

const sortColumn = (column) => {
  if (sortKey.value === column.field) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = column.field;
    sortOrder.value = "asc";
  }
};
</script>


<style scoped>
.grid-cols-4 {
  grid-template-columns: repeat(4, 1fr);
}

th, td {
  padding: 12px;
}

tbody tr:hover {
  background-color: #f0f8ff;
}

tbody tr {
  cursor: pointer;
}

.grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.chart-container {
  height: 100%;
  width: 100%;
  background: white;
  border-radius: 8px;
  padding: 10px;
}

.shape-overview {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sort-indicator {
  font-size: 0.8em; /* Makes the triangle smaller */
  margin-left: 5px;
  opacity: 0.8; /* Optional: makes it slightly faded */
}
</style>
