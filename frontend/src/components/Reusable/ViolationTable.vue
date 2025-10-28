<template>
  <div class="bg-white border border-gray-200 p-6 rounded-lg shadow-lg relative">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-4">
        <h1 class="text-2xl font-bold text-gray-700 mb-4">Validation Results</h1>
        <button
          @click="togglePrefixes"
          class="px-2 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 text-sm mb-4"
        >
          {{ showPrefixes ? 'Hide Prefixes' : 'Show Prefixes' }}
        </button>

      </div>
      <div class="flex gap-4">
        <button
          @click="toggleFilterBox"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 mb-4"
        >
          Filter
        </button>
        <button
          @click="downloadCSV"
          class="px-2 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 mb-4 flex items-center gap-2"
        >
          <font-awesome-icon :icon="['fas', 'download']" />
          Download CSV
        </button>
      </div>
    </div>

    <!-- Filter Box -->
    <div
      v-if="isFilterBoxVisible"
      class="absolute bg-white p-6 border shadow-lg rounded-lg z-50"
      style="top: 4.4rem; right: 1.5rem;"
    >
      <Filter
        :filters="filters"
        @update:filters="applyFilters"
        @set-options="setDropdownOptions"
        @reset="resetAllFilters"
      />
      <button 
          @click="toggleFilterBox" 
          class="mt-4 px-4 py-2 text-white font-medium rounded-lg shadow-md transition-all duration-200 
                bg-gray-500 border border-gray-600 hover:bg-gray-600 hover:border-gray-700 hover:shadow-lg"
          style="width: 250px;"
        >
          Close
        </button>
    </div>

    <!-- Table to display combined details and messages -->
    <table class="w-full border-collapse">
      <thead class="bg-gray-200">
        <tr>
          <th class="text-left px-4 py-2 border-b border-gray-300 text-gray-600 font-medium w-20">
            ID
          </th>
          <th class="text-left px-4 py-2 border-b border-gray-300 text-gray-600 font-medium w-1/3">
            Violated Triple
          </th>
          <th class="text-left px-4 py-2 border-b border-gray-300 text-gray-600 font-medium w-1/3">
            Error Message
          </th>
          <th class="text-left px-4 py-2 border-b border-gray-300 text-gray-600 font-medium w-20">
          </th>
        </tr>
      </thead>
      <tbody>
        <ViolationTableRowIntegrated
          v-for="(item, index) in paginatedData"
          :key="index"
          :rowNumber="(currentPage - 1) * itemsPerPage + index + 1"
          v-bind="item"
          @violation-fixed="handleViolationFixed"
          @violation-rejected="handleViolationRejected"
        />
      </tbody>
    </table>

    <div class="flex justify-between items-center mt-4">
      <button
        :disabled="currentPage === 1"
        @click="prevPage"
        class="px-4 py-2 bg-gray-200 text-gray-600 rounded hover:bg-gray-300 disabled:opacity-50"
      >
        Previous
      </button>
      <span class="text-gray-700">Page {{ currentPage }} of {{ totalPages }}</span>
      <button
        :disabled="currentPage === totalPages"
        @click="nextPage"
        class="px-4 py-2 bg-gray-200 text-gray-600 rounded hover:bg-gray-300 disabled:opacity-50"
      >
        Next
      </button>
    </div>
    <!-- Prefix List -->
    <div v-if="showPrefixes" class="bg-gray-100 p-4 rounded-lg mt-4">
        <h2 class="text-lg font-semibold text-gray-700 mb-2">Loaded Prefixes</h2>
        <ul class="list-disc pl-6 text-gray-600">
          <li v-for="(namespace, prefix) in prefixes" :key="prefix">
            <strong class="text-gray-800">{{ prefix }}:</strong> {{ namespace }}
          </li>
        </ul>
      </div>
  </div>
</template>

<script setup>
/**
 * ViolationTable component
 *
 * Displays a table of SHACL validation violations with filtering and pagination capabilities.
 * Allows users to view, filter, sort, and export validation results.
 *
 * @example
 * // Basic usage in a parent component template:
 * // <ViolationTable />
 *
 * @dependencies
 * - vue (Composition API)
 * - ./ViolationTableRow.vue - For rendering individual violation rows
 * - ./Filter.vue - For filtering functionality
 * - font-awesome - For icons
 *
 * @data
 * - Fetches validation results from '../reports/result.json'
 * - Processes and formats the data using prefixes for readability
 *
 * @features
 * - Pagination with customizable items per page
 * - Filtering capabilities
 * - URI shortening using prefixes
 * - CSV export functionality
 * - Expandable rows for detailed information
 *
 * @style
 * - Clean table design with alternating row colors
 * - Filter panel with responsive positioning
 * - Pagination controls with disabled states
 */
import { ref, computed, onMounted } from 'vue';
import ViolationTableRowIntegrated from './ViolationTableRowIntegrated.vue';
import Filter from './Filter.vue';
import api from '@/utils/api';

const tableData = ref([]);
const prefixes = ref({});
const shapes = ref([]);
const allData = ref([]);
const showFullPrefixes = ref(false); // Reactive toggle state

const currentPage = ref(1);
const itemsPerPage = 10;

const totalPages = computed(() => Math.ceil(allData.value.length / itemsPerPage));
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return allData.value.slice(start, start + itemsPerPage);
});

const showPrefixes = ref(false);

const togglePrefixes = () => {
  showPrefixes.value = !showPrefixes.value;
};

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--;
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++;
};

const loadViolationData = async () => {
  try {
    // Get session ID from localStorage for tenant isolation
    const sessionId = localStorage.getItem('shacl_session_id');
    const response = await api.getViolations(sessionId);
    const data = response.data;

    prefixes.value = data.prefixes || {};
    console.log("Loaded Prefixes:", prefixes.value);

    if (Object.keys(prefixes.value).length === 0) {
      console.warn("No prefixes found! URIs will not be transformed.");
    }

    const violations = data.violations || [];
    console.log("Loaded violations:", violations);

    // Transform backend violation data to match frontend format
    allData.value = violations.map((violation) => {
      const formattedData = {
        focusNode: formatURI(violation.focus_node || ''),
        resultPath: formatURI(violation.property_path || ''),
        value: formatURI(violation.value || ''),
        message: violation.message || '',
        propertyShape: formatURI(violation.shape_id || ''),
        severity: formatURI(violation.severity || ''),
        targetClass: '', // Backend doesn't provide this field
        targetNode: formatURI(violation.focus_node || ''),
        nodeShape: formatURI(violation.shape_id || ''),
        constraintComponent: formatURI(violation.constraint_id || ''),
        context: violation.context || {}, // PHOENIX-style context with example values
        shapes: {
          shape: formatURI(violation.shape_id || ''),
          type: formatURI(violation.violation_type || violation.severity || ''),
          properties: [], // Backend doesn't provide this level of detail yet
          targetClass: '', // Backend doesn't provide this field
        },
      };

      console.log("Formatted violation:", formattedData);
      return formattedData;
    });

    tableData.value = [...allData.value];
    console.log("Final Processed Data:", tableData.value);

  } catch (error) {
    console.error('Error fetching violation data:', error);
    // Set empty data to prevent errors
    allData.value = [];
    tableData.value = [];
  }
};


const formatURI = (uri) => {
  if (!uri || typeof uri !== "string") return uri; // Ensure valid input

  console.log("Processing URI:", uri);

  let matchedPrefix = null;
  let matchedNamespace = null;

  for (const [prefix, namespace] of Object.entries(prefixes.value)) {
    if (uri.startsWith(namespace) && (!matchedNamespace || namespace.length > matchedNamespace.length)) {
      matchedPrefix = prefix;
      matchedNamespace = namespace;
    }
  }

  if (matchedPrefix) {
    const transformedURI = `${matchedPrefix}:${uri.slice(matchedNamespace.length)}`;
    console.log(`Transformed "${uri}" → "${transformedURI}"`);
    return transformedURI;
  }

  console.log(`No match for "${uri}". Returning original.`);
  return uri; // Return as is if no prefix match
};

// Fetch data on mount
onMounted(async () => {
  await loadViolationData();
});

const downloadCSV = () => {
  if (!tableData.value.length) {
    alert("No data available to export.");
    return;
  }

  try {
    const headers = Object.keys(tableData.value[0]).join(",");
    const rows = tableData.value.map((row) =>
      Object.values(row)
        .map((value) => {
          if (typeof value === "string") {
            return `"${value.replace(/"/g, '""')}"`;
          } else if (Array.isArray(value)) {
            return `"${value.join("; ")}"`;
          }
          return value;
        })
        .join(",")
    );

    const csvContent = [headers, ...rows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);
    link.setAttribute("download", "ValidationResults.csv");
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Error generating CSV file:", error);
    alert("Failed to generate CSV file.");
  }
};

const isFilterBoxVisible = ref(false);
const filters = ref({
  dropdown1: [],
  dropdown2: [],
  dropdown3: [],
  dropdown4: [],
  options1: [],
  options2: [],
  options3: [],
  options4: [],
});

const toggleFilterBox = () => {
  isFilterBoxVisible.value = !isFilterBoxVisible.value;
};

const applyFilters = (updatedFilters) => {
  filters.value = { ...updatedFilters };
};

const resetAllFilters = () => {
  for (let i = 1; i <= 4; i++) {
    filters.value[`dropdown${i}`] = [];
  }
};

const setDropdownOptions = (options) => {
  filters.value = { ...filters.value, ...options };
};

// Event handlers for integrated cards
const handleViolationFixed = (data) => {
  console.log('Violation fixed:', data);

  // Option 1: Reload all data after fix
  // loadViolationData();

  // Option 2: Update local data to remove the fixed violation
  // This provides better UX without full page reload
  const violationIndex = allData.value.findIndex(item =>
    item.focusNode === data.focusNode &&
    item.resultPath === data.resultPath &&
    item.constraintComponent === data.constraintComponent
  );

  if (violationIndex !== -1) {
    // Remove the fixed violation from the list
    allData.value.splice(violationIndex, 1);

    // Adjust current page if necessary
    if (paginatedData.value.length === 0 && currentPage.value > 1) {
      currentPage.value--;
    }
  }

  // Optionally show success message
  // Could integrate with a toast notification system
  console.log('Violation successfully resolved and removed from table');
};

const handleViolationRejected = (data) => {
  console.log('Violation rejected:', data);
  // Optionally log rejection for analytics
};

</script>

<style scoped>
.grid-cols-4 {
  grid-template-columns: repeat(4, 1fr);
}

table {
  table-layout: fixed; /* Enforce fixed layout for consistent column widths */
  width: 100%; /* Ensure the table spans the full container width */
}


th,
td {
  padding: 12px;
  vertical-align: top;
}

tbody tr:hover {
  background-color: #f0f8ff;
}

tbody tr {
  cursor: pointer;
}

button:focus {
  outline: none;
}

/* Word wrap for all text cells except ID column */
td:not(:first-child):not(:last-child) {
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
  max-width: 300px; /* Reasonable max width for readability */
}

/* Special handling for violated triple column */
td:nth-child(2) {
  max-width: 250px;
}

/* Special handling for error message column */
td:nth-child(3) {
  max-width: 200px;
}

/* Keep ID column narrow and without wrap */
td:first-child {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60px;
}

/* Keep action column narrow */
td:last-child {
  white-space: nowrap;
  max-width: 80px;
}
</style>
