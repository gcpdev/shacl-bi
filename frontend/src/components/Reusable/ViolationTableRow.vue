<template>
  <tr class="even:bg-gray-50 hover:bg-blue-50 transition-colors" @click="toggleDetails" >
    <!-- Display the row number in the first column -->
    <td  class="text-left px-6 py-4 border-b border-gray-300">{{ rowNumber }}</td> <!-- Row number column -->

    <!-- Display the RDF Triple in a single cell -->
    <td class="text-left px-6 py-4 border-b border-gray-300 violation-triple">
      <div class="triple-line">
        <span class="triple-subject">{{ focusNode }}</span>
      </div>
      <div class="triple-line">
        <span class="triple-predicate">{{ resultPath }}</span>
      </div>
      <div class="triple-line">
        <span class="triple-object">{{ value }}</span>
      </div>
    </td>

    <!-- Error message column -->
    <td class="text-left px-6 py-4 border-b border-gray-300 error-message">
      <div class="message-text">{{ message }}</div>
    </td>

    <td class="text-right px-6 py-4 border-b border-gray-300">
      <button @click.stop="toggleDetails" class="toggle-btn">
        <span v-if="showDetails" class="triangle-down"></span>
        <span v-else class="triangle-left"></span>
      </button>
    </td>
    
  </tr>
  
  <!-- Show additional information when clicked -->
  <tr v-if="showDetails">
    <td colspan="2" class="details-cell text-left align-top px-6 py-4 border-b border-gray-300 text-gray-800 font-medium cursor-pointer">
      <div>
        <div class="text-left text-xl font-semibold text-gray-700 mb-3">
          <strong>Full Validation Details:</strong>
        </div>
        <!-- Convert details list into a table -->
        <table class="w-full border-collapse">
          <tbody>
            <tr v-if="focusNode">
              <td class="font-bold pr-4">Focus Node:</td>
              <td>{{ focusNode }}</td>
            </tr>
            <tr v-if="resultPath">
              <td class="font-bold pr-4">Result Path:</td>
              <td>{{ resultPath }}</td>
            </tr>
            <tr v-if="value">
              <td class="font-bold pr-4">Value:</td>
              <td>{{ value }}</td>
            </tr>
            <tr v-if="message">
              <td class="font-bold pr-4">Message:</td>
              <td>{{ message }}</td>
            </tr>
            <tr v-if="propertyShape">
              <td class="font-bold pr-4">Property Shape:</td>
              <td>{{ propertyShape }}</td>
            </tr>
            <tr v-if="severity">
              <td class="font-bold pr-4">Severity:</td>
              <td>{{ severity }}</td>
            </tr>
            <tr v-if="targetClass && targetClass.length > 0">
              <td class="font-bold pr-4">Target Class:</td>
              <td>{{ targetClass }}</td>
            </tr>
            <tr v-if="targetNode && targetNode.length > 0">
              <td class="font-bold pr-4">Target Node:</td>
              <td>{{ targetNode }}</td>
            </tr>
            <tr v-if="targetSubjectsOf && targetSubjectsOf.length > 0">
              <td class="font-bold pr-4">Target Subjects of:</td>
              <td>{{ targetSubjectsOf }}</td>
            </tr>
            <tr v-if="targetObjectsOf && targetObjectsOf.length > 0">
              <td class="font-bold pr-4">Target Objects of:</td>
              <td>{{ targetObjectsOf }}</td>
            </tr>
            <tr v-if="nodeShape">
              <td class="font-bold pr-4">Node Shape:</td>
              <td>{{ nodeShape }}</td>
            </tr>
            <tr v-if="constraintComponent">
              <td class="font-bold pr-4">Constraint Component:</td>
              <td>{{ constraintComponent }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </td>
    <td colspan="2" class="details-cell text-right align-top px-6 py-4 border-b border-gray-300 text-gray-800 font-medium cursor-pointer">
      <div>
        <div class="text-left text-xl font-semibold text-gray-700 mb-3">
          <strong>Shape Details:</strong>
        </div>
          <p><strong>Shape:</strong> {{ (shapes && shapes.shape) || "None" }}</p>
          <p><strong>Type:</strong> {{ (shapes && shapes.type) || "None" }}</p>
          <div class="details-list">
            <!-- Iterate over the Properties array -->
            <div v-if="shapes.properties && shapes.properties.length > 0">
              <strong>Property Shapes Details:</strong>
              <ul class="ml-6">
                <li v-for="(property, index) in shapes.properties" :key="index">
                  <p><strong>{{ property.predicate }}:</strong>
                    <span v-if="Array.isArray(property.object)">
                      <ul>
                        <li v-for="(obj, idx) in property.object" :key="idx">{{ obj }}</li>
                      </ul>
                    </span>
                    <span v-else>&nbsp; {{ property.object }}</span>
                  </p>
                  <p class="my-2" />
                </li>
              </ul>
            </div>
            <p v-else>No properties available.</p>
            <p><strong>Target Class:</strong> {{ (shapes && shapes.targetClass) || "None" }}</p>
        </div>
      </div>
    </td>
  </tr>

  <!-- Explanation and Fix Suggestions Row -->
  <tr v-if="showDetails">
    <td colspan="4" class="details-cell text-left align-top px-6 py-4 border-b border-gray-300 bg-blue-50">
      <div class="grid grid-cols-1 gap-6">
        <!-- Problem Explanation -->
        <div>
          <div class="text-lg font-semibold text-gray-700 mb-2 flex items-center">
            <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Problem Explanation
          </div>
          <div v-if="explanationLoading" class="text-gray-600 italic">
            Loading explanation...
          </div>
          <div v-else-if="explanationData" class="text-gray-800">
            <p class="mb-2">{{ explanationData.explanation_natural_language }}</p>
            <div v-if="explanationData.has_enhanced" class="text-xs text-blue-600 font-medium">
              ✨ AI-powered explanation
            </div>
          </div>
          <div v-else class="text-gray-600 italic">
            <button
              @click="loadExplanation"
              class="text-blue-600 hover:text-blue-800 underline text-sm"
            >
              Generate Explanation
            </button>
          </div>
        </div>

        <!-- Suggested Solution -->
        <div>
          <div class="text-lg font-semibold text-gray-700 mb-2 flex items-center">
            <svg class="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Suggested Solution
          </div>
          <div v-if="explanationLoading" class="text-gray-600 italic">
            Loading repair suggestion...
          </div>
          <div v-else-if="explanationData" class="text-gray-800">
            <p class="mb-3">{{ explanationData.suggestion_natural_language }}</p>

            <!-- Accept/Reject Buttons -->
            <div v-if="explanationData.proposed_repair && explanationData.proposed_repair.query" class="flex items-center gap-3">
              <button
                @click="acceptRepair"
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 text-sm"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Accept Fix
              </button>
              <button
                @click="rejectRepair"
                class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2 text-sm"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                Reject
              </button>
              <div v-if="explanationData.has_enhanced" class="text-xs text-green-600 font-medium">
                ✨ AI-powered repair suggestion
              </div>
            </div>

            <!-- Repair Query Preview (PHOENIX-style) -->
            <div v-if="explanationData.proposed_repair && explanationData.proposed_repair.query" class="mt-3">
              <div class="flex items-center justify-between">
                <button
                  @click="showRepairQuery = !showRepairQuery"
                  class="text-xs text-gray-600 hover:text-gray-800 underline"
                >
                  {{ showRepairQuery ? 'Hide' : 'Show' }} SPARQL Query
                </button>
              </div>
              <!-- PHOENIX-style input interface (always visible when query exists) -->
              <div class="mt-3 space-y-3">
                <!-- Action Badge -->
                <div class="flex items-center gap-2">
                  <span class="px-2 py-1 text-xs font-medium rounded" :class="getActionBadgeClass(getActionType(explanationData.proposed_repair.query))">
                    {{ getActionType(explanationData.proposed_repair.query) }}
                  </span>
                  <span class="text-xs text-gray-500">
                    {{ resultPath }}
                  </span>
                </div>

                <!-- PHOENIX-style input fields based on constraint type -->
                <div v-if="isMaxCountViolation" class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">
                    {{ getMaxCountInputLabel() }}
                  </label>
                  <!-- Single selection for maxCount = 1 -->
                  <select
                    v-if="maxCount === 1"
                    v-model="selectedValues[0]"
                    class="w-full p-2 border border-gray-300 rounded text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Choose the correct value to keep...</option>
                    <option v-for="val in actualValues" :key="val" :value="val">{{ val }}</option>
                  </select>
                  <!-- Multi-selection for maxCount > 1 -->
                  <div v-else class="space-y-2 p-3 border rounded-md bg-gray-50">
                    <div v-for="val in actualValues" :key="val" class="flex items-center gap-2">
                      <input
                        type="checkbox"
                        :id="`value-${val}`"
                        :value="val"
                        v-model="selectedValues"
                        :disabled="selectedValues.length >= maxCount && !selectedValues.includes(val)"
                        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      >
                      <label :for="`value-${val}`" class="text-sm font-normal">{{ val }}</label>
                    </div>
                    <div class="text-xs text-gray-500 mt-2">
                      Select up to {{ maxCount }} values to keep ({{ selectedValues.length }} selected)
                    </div>
                  </div>
                </div>

                <!-- Pattern constraint with PHOENIX-style PatternInput -->
                <div v-else-if="isPatternViolation" class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">
                    Enter the correct value:
                  </label>
                  <div v-if="explanationData.constraint_info && explanationData.constraint_info.pattern" class="text-xs text-blue-600 mb-1">
                    Pattern: {{ explanationData.constraint_info.pattern }}
                  </div>
                  <div class="flex items-center gap-2 p-2 border rounded-md bg-gray-50">
                    <span v-if="patternInfo.prefix" class="font-mono text-gray-600 text-sm">{{ patternInfo.prefix }}</span>
                    <input
                      v-model="patternInputValue"
                      @input="updatePatternInput"
                      type="text"
                      :placeholder="(explanationData.constraint_info && explanationData.constraint_info.exampleValue) || 'Enter value...'"
                      class="flex-1 p-1 border-b border-gray-300 focus:border-blue-500 focus:outline-none font-mono text-sm"
                    >
                    <span v-if="patternInfo.suffix" class="font-mono text-gray-600 text-sm">{{ patternInfo.suffix }}</span>
                  </div>
                  <div v-if="explanationData.constraint_info && explanationData.constraint_info.exampleValue" class="text-xs text-gray-500">
                    Example: {{ explanationData.constraint_info.exampleValue }}
                  </div>
                </div>

                <!-- InConstraint violation with dropdown -->
                <div v-else-if="isInConstraintViolation && allowedValues.length > 0" class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">
                    Select the correct value:
                  </label>
                  <select
                    v-model="selectedAllowedValue"
                    class="w-full p-2 border border-gray-300 rounded text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Choose from the list of allowed values...</option>
                    <option v-for="val in allowedValues" :key="val" :value="val">{{ val }}</option>
                  </select>
                </div>

                <!-- General user input for other constraints -->
                <div v-else-if="needsUserInput" class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">
                    Enter the correct value:
                  </label>
                  <input
                    v-model="userProvidedValue"
                    type="text"
                    :placeholder="getInputPlaceholder()"
                    class="w-full p-2 border border-gray-300 rounded text-sm focus:border-blue-500 focus:outline-none"
                  >
                </div>

                <!-- Value to remove for DELETE operations -->
                <div v-if="value && getActionType(explanationData.proposed_repair.query) === 'DELETE'" class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">
                    Value to remove:
                  </label>
                  <div class="p-2 bg-red-50 rounded border border-red-200">
                    <code class="text-sm text-red-800">{{ value }}</code>
                  </div>
                </div>

                <!-- SPARQL Query Edit Section (Advanced) -->
                <details class="border rounded-lg">
                  <summary class="p-2 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50">
                    🔧 Advanced: Edit SPARQL Query
                  </summary>
                  <div class="p-3 border-t">
                    <textarea
                      v-model="editableQuery"
                      class="w-full p-3 bg-gray-100 rounded text-xs font-mono text-gray-700 max-h-40 overflow-y-auto border border-blue-300 focus:border-blue-500 focus:outline-none resize-none"
                      rows="8"
                      placeholder="Edit the SPARQL query here..."
                    ></textarea>
                    <div class="flex gap-2 mt-2">
                      <button
                        @click="applyEditedQuery"
                        class="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
                      >
                        Apply Query Changes
                      </button>
                      <button
                        @click="resetQuery"
                        class="px-3 py-1 bg-gray-500 text-white rounded text-xs hover:bg-gray-600 transition-colors"
                      >
                        Reset
                      </button>
                    </div>
                  </div>
                </details>

                <!-- Query Preview (collapsible) -->
                <details class="border rounded-lg">
                  <summary class="p-2 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50">
                    📄 Current SPARQL Query
                  </summary>
                  <div class="p-3 border-t">
                    <pre class="text-xs font-mono text-gray-700 whitespace-pre-wrap">{{ explanationData.proposed_repair.query }}</pre>
                  </div>
                </details>
              </div>
            </div>
          </div>
          <div v-else class="text-gray-600 italic">
            No repair suggestion available
          </div>
        </div>
      </div>
    </td>
  </tr>
</template>

<script setup>
/**
 * ViolationTableRow component
 *
 * Renders an expandable row for SHACL validation violations.
 * Shows basic violation info with the ability to expand for detailed information.
 *
 * @example
 * // Basic usage in a parent component template:
 * // <ViolationTableRow
 * //   :rowNumber="1"
 * //   focusNode="ex:Person1"
 * //   resultPath="ex:name"
 * //   value="John Doe"
 * //   message="Value does not match pattern" 
 * // />
 *
 * @prop {Number} rowNumber - The sequential number for this row
 * @prop {String} focusNode - The focus node URI of the violation
 * @prop {String} resultPath - The property path involved in the violation
 * @prop {String|Number} value - The value that caused the violation
 * @prop {String} message - The validation error message
 * @prop {String} propertyShape - The property shape URI
 * @prop {String} severity - The severity level of the violation
 * @prop {Object} shapes - Object containing shape details
 * @prop {String|Array} targetClass - The target class of the shape
 * @prop {String|Array} targetNode - The target node of the shape
 * @prop {String|Array} targetSubjectsOf - The target subjects of the shape
 * @prop {String|Array} targetObjectsOf - The target objects of the shape
 * @prop {String} nodeShape - The node shape URI
 * @prop {String} constraintComponent - The constraint component URI
 *
 * @dependencies
 * - vue (Composition API)
 *
 * @style
 * - Interactive row with hover effects and expandable details.
 * - Compact data display with triangle indicators for expansion state.
 * - Well-structured nested tables for details view.
 * 
 * @returns {HTMLElement} Two table rows: a main row showing summary violation 
 * information and an expandable details row that appears when clicked, displaying
 * comprehensive violation information and shape details in a structured format.
 */
import { defineProps, ref, computed, watch } from 'vue';
import api from '@/utils/api';

// Define the props to receive data from the parent component
const props = defineProps({
  rowNumber: Number,
  focusNode: String,
  resultPath: String,
  value: [String, Number],
  message: String,
  propertyShape: String,
  severity: String,
  shapes: Object,
  targetClass: [String, Array],
  targetNode: [String, Array],
  targetSubjectsOf: [String, Array],
  targetObjectsOf: [String, Array],
  nodeShape: String,
  constraintComponent: String,
});

const showDetails = ref(false);
const explanationData = ref(null);
const explanationLoading = ref(false);
const showRepairQuery = ref(false);
const editMode = ref(false);
const editableQuery = ref('');

// PHOENIX-style input variables
const userInput = ref('');
const selectedValues = ref([]);
const selectedAllowedValue = ref('');
const patternInputValue = ref('');
const patternInfo = ref({ prefix: '', suffix: '', example: '' });
const maxCount = ref(1);
const actualValues = ref([]);
const allowedValues = ref([]);

const finalQuery = computed(() => {
  const originalQuery = explanationData.value?.proposed_repair?.query || '';
  if (originalQuery.includes('$user_provided_value')) {
    // Ensure the user provided value is properly quoted if it's a string literal
    const formattedValue = userInput.value.startsWith('http') ? `<${userInput.value}>` : `"${userInput.value}"`;
    return originalQuery.replace(/\$user_provided_value/g, formattedValue);
  }
  return editableQuery.value;
});

const toggleDetails = () => {
  const originalQuery = explanationData.value?.proposed_repair?.query || '';
  if (originalQuery.includes('$user_provided_value')) {
    // Ensure the user provided value is properly quoted if it's a string literal
    const formattedValue = userProvidedValue.value.startsWith('http') ? `<${userProvidedValue.value}>` : `"${userProvidedValue.value}"`;
    return originalQuery.replace(/\$user_provided_value/g, formattedValue);
  }
  return editableQuery.value;
});

const toggleDetails = () => {
  showDetails.value = !showDetails.value;
  // Load explanation when details are opened
  if (showDetails.value && !explanationData.value) {
    loadExplanation();
  }
};

const loadExplanation = async () => {
  if (explanationLoading.value) return;

  explanationLoading.value = true;
  try {
    // Get session ID from localStorage
    const sessionId = localStorage.getItem('shacl_session_id');

    // Create violation object for API
    const violation = {
      focus_node: props.focusNode,
      property_path: props.resultPath,
      value: props.value,
      message: props.message,
      shape_id: props.nodeShape,
      constraint_id: props.constraintComponent,
      severity: props.severity
    };

    const response = await api.postExplanation(violation, sessionId);

    explanationData.value = response.data;
    console.log('Full backend response:', response.data);
    console.log('Constraint component:', props.constraintComponent);
    console.log('Constraint info:', response.data.constraint_info);

    // Initialize editable query with the original query
    if (response.data && response.data.proposed_repair && response.data.proposed_repair.query) {
      editableQuery.value = response.data.proposed_repair.query;
      console.log('Editable query set to:', editableQuery.value);
    } else {
      console.log('No query provided in response');
    }

    // Initialize constraint-specific data
    initializeConstraintSpecificData();
    console.log('After initialization - Pattern:', isPatternViolation.value, 'MaxCount:', isMaxCountViolation.value, 'InConstraint:', isInConstraintViolation.value);
    console.log('Explanation loaded:', explanationData.value);

  } catch (error) {
    console.error('Error loading explanation:', error);
    // Set a basic explanation as fallback
    explanationData.value = {
      explanation_natural_language: `The resource '${props.focusNode}' violates the constraint '${props.constraintComponent}' on property '${props.resultPath}'. ${props.message}`,
      suggestion_natural_language: 'To fix this violation, please review the data and ensure it complies with the constraint requirements.',
      proposed_repair: { query: '' },
      has_enhanced: false
    };
  } finally {
    explanationLoading.value = false;
  }
};

const acceptRepair = async () => {
  if (!finalQuery.value) return;

  try {
    const sessionId = localStorage.getItem('shacl_session_id');

    const response = await api.postRepair(finalQuery.value, sessionId);

    if (response.data.success) {
      // Show success message
      alert('Repair applied successfully! The violation has been fixed.');
      // Optionally refresh the data or reload the page
      window.location.reload();
    } else {
      alert('Failed to apply repair: ' + response.data.error);
    }

  } catch (error) {
    console.error('Error applying repair:', error);
    alert('Failed to apply repair: ' + (error.response?.data?.error || error.message));
  }
};

const rejectRepair = () => {
  // Clear the explanation data
  explanationData.value = null;
  showRepairQuery.value = false;
  editMode.value = false;
};

const applyEditedQuery = () => {
  // Update the explanation data with the edited query
  if (explanationData.value && explanationData.value.proposed_repair) {
    explanationData.value.proposed_repair.query = editableQuery.value;
  }
  editMode.value = false;
};

const resetQuery = () => {
  if (explanationData.value?.proposed_repair?.query) {
    editableQuery.value = explanationData.value.proposed_repair.query;
  }
};

// PHOENIX-style computed properties
const isMaxCountViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  console.log('Checking MaxCount in:', constraint);
  return constraint.includes('MaxCountConstraintComponent') || constraint.includes('MaxCount') || false;
});

const isPatternViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  console.log('Checking Pattern in:', constraint);
  return constraint.includes('PatternConstraintComponent') || constraint.includes('Pattern') || false;
});

const isInConstraintViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  console.log('Checking InConstraint in:', constraint);
  return constraint.includes('InConstraintComponent') || constraint.includes('InConstraint') || false;
});

const needsUserInput = computed(() => {
  const query = explanationData.value?.proposed_repair?.query || '';
  return query.includes('$user_provided_value');
});

// PHOENIX-style helper methods
const getActionType = (query) => {
  if (!query) return 'MODIFY';
  if (query.includes('INSERT') && !query.includes('DELETE')) return 'ADD';
  if (query.includes('DELETE')) return 'DELETE';
  return 'MODIFY';
};

const getActionBadgeClass = (actionType) => {
  const classMap = {
    'ADD': 'bg-green-100 text-green-800 border border-green-200',
    'DELETE': 'bg-red-100 text-red-800 border border-red-200',
    'MODIFY': 'bg-blue-100 text-blue-800 border border-blue-200'
  };
  return classMap[actionType] || classMap['MODIFY'];
};

const getMaxCountInputLabel = () => {
  if (maxCount.value === 1) {
    return 'Select the value to keep:';
  }
  return `Select up to ${maxCount.value} values to keep:`;
};

const updatePatternInput = () => {
  // Combine prefix, input, and suffix for pattern constraints
  const fullValue = `${patternInfo.value.prefix}${patternInputValue.value}${patternInfo.value.suffix}`;
  userInput.value = fullValue;
};

const parsePattern = (pattern) => {
  // Parse regex pattern into prefix and suffix (similar to PHOENIX's PatternInput)
  try {
    const match = pattern.match(/^(.*?)(\(.*?\))(.*)$/);
    if (match) {
      return {
        prefix: match[1].replace(/\\/g, ''),
        suffix: match[3].replace(/\\/g, ''),
        hasVariable: true
      };
    }
    return { prefix: '', suffix: '', hasVariable: false };
  } catch (e) {
    return { prefix: '', suffix: '', hasVariable: false };
  }
};

const getInputPlaceholder = () => {
  const propertyLower = props.resultPath?.toLowerCase() || '';

  if (propertyLower.includes('name')) return 'e.g., John Doe';
  if (propertyLower.includes('email')) return 'e.g., user@example.com';
  if (propertyLower.includes('date')) return 'e.g., 2024-01-01';
  if (propertyLower.includes('age') || propertyLower.includes('count')) return 'e.g., 25';
  if (propertyLower.includes('url')) return 'e.g., https://example.com';

  return 'Enter a value...';
};

const initializeConstraintSpecificData = () => {
  if (!explanationData.value) return;

  // Initialize MaxCount data
  if (isMaxCountViolation.value) {
    // Extract maxCount and actualValues from constraint info if available
    const constraintInfo = explanationData.value.constraint_info || {};
    maxCount.value = constraintInfo.maxCount || 1;
    actualValues.value = constraintInfo.actualValues || [props.value].filter(Boolean);

    // Pre-select first maxCount values (PHOENIX behavior)
    selectedValues.value = actualValues.value.slice(0, maxCount.value);
  }

  // Initialize Pattern data
  if (isPatternViolation.value) {
    const constraintInfo = explanationData.value.constraint_info || {};
    const pattern = constraintInfo.pattern;

    if (pattern) {
      patternInfo.value = parsePattern(pattern);
      patternInfo.value.example = constraintInfo.exampleValue || '';
    }
  }

  // Initialize InConstraint data
  if (isInConstraintViolation.value) {
    const constraintInfo = explanationData.value.constraint_info || {};
    allowedValues.value = constraintInfo.allowedValues || [];
  }
};

// Helper methods to provide contextual information like PHOENIX
const getConstraintTypeLabel = (constraintComponent) => {
  if (!constraintComponent) return 'Unknown';

  const labelMap = {
    'MinCountConstraintComponent': 'Missing Required Value',
    'MaxCountConstraintComponent': 'Too Many Values',
    'DatatypeConstraintComponent': 'Incorrect Data Type',
    'PatternConstraintComponent': 'Pattern Mismatch',
    'InConstraintComponent': 'Value Not in Allowed List',
    'MinLengthConstraintComponent': 'Value Too Short',
    'MaxLengthConstraintComponent': 'Value Too Long',
    'MinInclusiveConstraintComponent': 'Value Too Small',
    'MaxInclusiveConstraintComponent': 'Value Too Large',
    'NodeKindConstraintComponent': 'Wrong Node Type',
    'ClassConstraintComponent': 'Wrong Class Type'
  };

  const componentName = constraintComponent.split('#').pop() || constraintComponent;
  return labelMap[componentName] || componentName.replace(/([A-Z])/g, ' $1').trim();
};

const getConstraintHint = (constraintComponent) => {
  if (!constraintComponent) return '';

  const hints = {
    'MinCountConstraintComponent': 'Use INSERT DATA to add a missing required value.',
    'MaxCountConstraintComponent': 'Use DELETE WHERE to remove extra values.',
    'DatatypeConstraintComponent': 'Use DELETE/INSERT to fix the data type (e.g., add xsd:integer for numbers).',
    'PatternConstraintComponent': 'Ensure the value matches the required pattern (like email format).',
    'InConstraintComponent': 'Value must be one of the allowed values in the constraint.',
    'MinLengthConstraintComponent': 'Value needs more characters to meet minimum length.',
    'MaxLengthConstraintComponent': 'Value has too many characters, needs to be shortened.',
    'MinInclusiveConstraintComponent': 'Value must be greater than or equal to the minimum.',
    'MaxInclusiveConstraintComponent': 'Value must be less than or equal to the maximum.',
    'NodeKindConstraintComponent': 'Expected either a literal value or a URI/IRI node.',
    'ClassConstraintComponent': 'Resource must be an instance of the specified class.'
  };

  const componentName = constraintComponent.split('#').pop() || constraintComponent;
  return hints[componentName] || '';
};

const getQueryPlaceholder = (constraintComponent) => {
  const componentName = constraintComponent?.split('#').pop() || '';

  if (componentName.includes('MinCount')) {
    return `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "EXAMPLE_VALUE" .
  }
}`;
  } else if (componentName.includes('MaxCount')) {
    return `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
}`;
  } else if (componentName.includes('Datatype')) {
    return `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "CORRECTED_VALUE"^^xsd:datatype .
  }
}`;
  } else {
    return `# Modify the SPARQL query based on the specific constraint
# Make sure to use the correct graph URI and actual values`;
  }
};

const generateSampleQuery = () => {
  const componentName = props.constraintComponent?.split('#').pop() || '';

  let sampleQuery = '';

  if (componentName.includes('MinCount')) {
    // Generate a sensible default based on property name
    const defaultValue = getDefaultValueForProperty(props.resultPath);
    sampleQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> ${defaultValue} .
  }
}`;
  } else if (componentName.includes('MaxCount')) {
    sampleQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
}`;
  } else if (componentName.includes('Datatype')) {
    const correctedValue = getCorrectedDatatypeValue(props.value, props.resultPath);
    sampleQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> ${correctedValue} .
  }
}`;
  } else {
    sampleQuery = `# Example SPARQL query for ${componentName}
# Modify according to your specific needs
DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "CORRECTED_VALUE" .
  }
}`;
  }

  editableQuery.value = sampleQuery;
};

// Helper functions to generate sensible defaults (similar to PHOENIX's approach)
const getDefaultValueForProperty = (propertyPath) => {
  if (!propertyPath) return '""';

  const lowerPath = propertyPath.toLowerCase();

  if (lowerPath.includes('name') || lowerPath.includes('label') || lowerPath.includes('title')) {
    return '"Unknown Name"';
  } else if (lowerPath.includes('email') || lowerPath.includes('mail')) {
    return '"unknown@example.com"';
  } else if (lowerPath.includes('date') || lowerPath.includes('created') || lowerPath.includes('modified')) {
    return `"${new Date().toISOString().split('T')[0]}"^^xsd:date`;
  } else if (lowerPath.includes('age') || lowerPath.includes('count') || lowerPath.includes('number')) {
    return '"0"^^xsd:integer';
  } else if (lowerPath.includes('description') || lowerPath.includes('comment') || lowerPath.includes('text')) {
    return '""';
  } else if (lowerPath.includes('url') || lowerPath.includes('link') || lowerPath.includes('uri')) {
    return '"http://example.org"';
  } else {
    return '""';
  }
};

const getCorrectedDatatypeValue = (value, propertyPath) => {
  if (!value) return '""';

  // Try to determine appropriate datatype based on property name
  const lowerPath = propertyPath?.toLowerCase() || '';

  if (lowerPath.includes('age') || lowerPath.includes('count') || lowerPath.includes('number')) {
    return isNaN(value) ? `"0"^^xsd:integer` : `"${value}"^^xsd:integer`;
  } else if (lowerPath.includes('date') || lowerPath.includes('created') || lowerPath.includes('modified')) {
    return `"${value}"^^xsd:date`;
  } else if (lowerPath.includes('email') || lowerPath.includes('url') || lowerPath.includes('uri')) {
    return `"${value}"`;
  } else {
    // Default to string
    return `"${value}"`;
  }
};

// PHOENIX-style watchers to automatically update SPARQL queries
watch(editableQuery, (newValue) => {
  // This watcher now primarily serves to keep the advanced edit field in sync
  // The main query logic is handled by the `finalQuery` computed property.
});


watch(selectedAllowedValue, (newValue) => {
  if (!newValue) return;
  userProvidedValue.value = newValue;
});

watch(selectedValues, (newValues) => {
  if (!isMaxCountViolation.value || !editableQuery.value) return;

  // For MaxCount violations, generate DELETE query for values to remove
  const valuesToDelete = actualValues.value.filter(v => !newValues.includes(v));
  if (valuesToDelete.length > 0) {
    const deleteClauses = valuesToDelete.map(val =>
      `<${props.focusNode}> <${props.resultPath}> "${val}" .`
    ).join('\n    ');

    editableQuery.value = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    ${deleteClauses}
  }
}`;
  }
}, { deep: true });
</script>


<style scoped>
table {
  width: 100%;
  border-collapse: collapse; /* Ensures no extra spacing */
}

td,th {
  padding: 1px 1px; /* Reduce padding inside cells */
}

div {
  text-align: left;
}

tr {
  cursor: pointer;
}

tr:hover {
  background-color: #f0f8ff;
}

/* Styling for the toggle button */
.toggle-column {
  text-align: right;
}

.toggle-btn {
  background-color: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.toggle-btn:hover {
  color: #007bff;
}

/* Symbols for toggle: triangle left and down */
.triangle-left {
  display: inline-block;
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 7px solid black; /* Left triangle */
}

.triangle-down {
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid black; /* Downward triangle */
}

.details-cell {
  background-color: #f9fafb; /* Light gray background for better contrast */
  border-radius: 8px; /* Rounded corners for a smoother look */
}

.details-list p {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #4a5568;
  margin-bottom: 8px;
}

.details-list strong {
  color: #2d3748; /* Darker text color for labels */
}

.shape-details {
  padding: 12px;
  font-size: 0.85rem;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
}

.text-xl {
  font-size: 1.25rem; /* Slightly larger font for headings */
}

.font-semibold {
  font-weight: 600; /* Semi-bold for better emphasis */
}

.text-gray-700 {
  color: #4a5568; /* Darker text for better contrast */
}

.text-gray-800 {
  color: #2d3748; /* Even darker for important text */
}

.mb-3 {
  margin-bottom: 16px; /* Adds space after headings */
}

.cursor-pointer:hover {
  background-color: #f0f4f8; /* Subtle hover effect */
}

.details-list p {
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 4px;
}

.details-list ul {
  padding-left: 1.5rem;
}

.details-list strong {
  color: #2d3748;
}

/* Styling for violated triple display */
.violation-triple {
  max-width: 250px;
}

.triple-line {
  margin-bottom: 4px;
  line-height: 1.3;
  word-break: break-all;
}

.triple-subject {
  color: #2563eb;
  font-weight: 500;
}

.triple-predicate {
  color: #059669;
  font-weight: 500;
}

.triple-object {
  color: #dc2626;
  font-weight: 500;
}

/* Styling for error message display */
.error-message {
  max-width: 200px;
}

.message-text {
  word-break: break-word;
  line-height: 1.4;
  color: #374151;
}

/* Enhanced styling for details section */
.details-cell {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 16px !important;
}

.details-cell table {
  word-break: break-word;
  line-height: 1.5;
}

.details-cell table td {
  vertical-align: top;
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.details-cell table td:last-child {
  border-bottom: none;
}

.details-cell .font-bold {
  min-width: 140px;
  color: #1f2937;
  font-weight: 600;
}

/* Improved styling for explanation section */
.grid.grid-cols-1 {
  gap: 24px;
}

.grid.grid-cols-1 > div {
  line-height: 1.5;
  word-break: break-word;
}

/* Make sure long URIs in explanation section wrap */
.text-gray-800 {
  word-break: break-all;
  overflow-wrap: break-word;
}
</style>
