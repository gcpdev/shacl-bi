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
import { ref, computed, onMounted } from 'vue';
import api from '../../utils/api';
import HistogramChart from './../Charts/HistogramChart.vue';
import ScatterPlotChart from './../Charts/ScatterPlotChart.vue';
import { useRouter } from 'vue-router';
import { calculateShannonEntropy } from "./../../utils/utils"; // Assume you have this utility function

const dashboardData = ref(null);
const router = useRouter();

onMounted(async () => {
  try {
    // Get session ID from localStorage if available
    const sessionId = localStorage.getItem('shacl_session_id');

    // Get basic dashboard data for tags
    const dashboardResponse = await api.getDashboardData(sessionId);
    dashboardData.value = dashboardResponse.data;

    // Get shapes-specific data
    if (sessionId) {
      try {
        // Get violations per node shape
        const shapesResponse = await api.get('/homepage/shapes/violations', {
          shapes_graph_uri: 'http://ex.org/ShapesGraph',
          validation_report_uri: `http://ex.org/ValidationReport/Session_${sessionId}`
        });

        // Get total shapes count
        const totalShapesResponse = await api.get('/homepage/shapes/graph/count', {
          graph_uri: 'http://ex.org/ShapesGraph'
        });

        // Transform shapes data for the component
        const violationsData = shapesResponse.data.violationsPerNodeShape || [];
        const totalShapes = totalShapesResponse.data || 0;

        // Create shapes array with sample additional data for demonstration
        const shapesArray = violationsData.map((shape, index) => ({
          id: index + 1,
          name: shape.NodeShapeName,
          violations: shape.NumViolations,
          propertyShapes: Math.floor(Math.random() * 10) + 1, // Sample data
          focusNodes: Math.floor(Math.random() * 20) + 1, // Sample data
          propertyPaths: Math.floor(Math.random() * 15) + 1, // Sample data
          mostViolatedConstraint: shape.NumViolations > 0 ? 'sh:datatype' : 'None',
          violationToConstraintRatio: shape.NumViolations > 0 ?
            (shape.NumViolations / (Math.floor(Math.random() * 10) + 1)).toFixed(2) : '0.00'
        }));

        // Add shapes data to dashboardData
        dashboardData.value.shapes = shapesArray;

      } catch (shapesError) {
        console.error('Error fetching shapes data:', shapesError);
        // Fallback: add empty shapes array
        dashboardData.value.shapes = [];
      }
    } else {
      // No session ID - add empty shapes array
      dashboardData.value.shapes = [];
    }

  } catch (error) {
    console.error('Error fetching dashboard data:', error);
  }
});

const tags = computed(() => dashboardData.value?.tags || []);
const normalizedHistogramViolationData = computed(() => {
  // Additional defensive checks
  if (!dashboardData.value) return { labels: [], datasets: [] };
  if (!dashboardData.value.shapeHistogramData) return { labels: [], datasets: [] };

  const histogramData = dashboardData.value.shapeHistogramData;
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
      label: 'Violations',
      data: histogramData.map(item => item[1]),
      backgroundColor: '#3498db',
      borderColor: '#2980b9',
      borderWidth: 1
    }]
  };
});
const coveragePlotData = computed(() => {
  // Additional defensive checks
  if (!dashboardData.value) return { datasets: [] };
  if (!dashboardData.value.shapes) return { datasets: [] };

  const shapes = dashboardData.value.shapes;
  if (!Array.isArray(shapes) || shapes.length === 0) return { datasets: [] };

  return {
    datasets: [
      {
        label: "Shapes",
        data: shapes.map((shape) => ({
          x: shape.propertyShapes || 1,
          y: shape.violations / (shape.propertyShapes || 1),
          label: shape.name,
          hasZeroViolations: shape.violations === 0,
        }))
      },
    ],
  };
});
const scatterPlotData = computed(() => {
  // Additional defensive checks
  if (!dashboardData.value) return { datasets: [] };
  if (!dashboardData.value.shapes) return { datasets: [] };

  const shapes = dashboardData.value.shapes;
  if (!Array.isArray(shapes) || shapes.length === 0) return { datasets: [] };

  return {
    datasets: [
      {
        label: "Shapes",
        data: shapes.map((shape) => ({
          x: Math.log2(shape.violations + 1), // Simple entropy calculation
          y: shape.violations / (shape.propertyShapes || 1),
          label: shape.name,
        }))
      },
    ],
  };
});
const shapes = computed(() => {
    const rawShapes = dashboardData.value?.shapes || [];

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

    // Transform shapes data to use short names
    return rawShapes.map(shape => ({
        ...shape,
        name: getShortName(shape.name)
    }));
});
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
  // Use the shape name as the ID since we don't have separate IDs
  router.push({ name: "ShapeView", params: { shapeId: shape.name || shape } });
};

const sortKey = ref("");
const sortOrder = ref("asc");

const columns = [
  { label: "Shape Name", field: "name" },
  { label: "Violations", field: "violations" },
  { label: "Property Shapes", field: "propertyShapes" },
  { label: "Focus Nodes", field: "focusNodes" },
  { label: "Property Paths", field: "propertyPaths" },
  { label: "Most Violated Constraint", field: "mostViolatedConstraint" },
  { label: "Violation/Constraint Ratio", field: "violationToConstraintRatio" }
];

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
