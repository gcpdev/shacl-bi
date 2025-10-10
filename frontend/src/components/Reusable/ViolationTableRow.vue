<template>
  <tr class="even:bg-gray-50 hover:bg-blue-50 transition-colors" @click="toggleDetails" >
    <!-- Display the row number in the first column -->
    <td  class="text-left px-6 py-4 border-b border-gray-300">{{ rowNumber }}</td> <!-- Row number column -->

    <!-- Display the RDF Triple in a single cell -->
    <td class="text-left px-6 py-4 border-b border-gray-300">
      <span>{{ focusNode }}</span>
      <span>&nbsp;&nbsp;&nbsp;</span>
      <span>{{ resultPath }}</span>
      <span>&nbsp;&nbsp;&nbsp;</span>
      <span>{{ value }}</span>
    </td>
    
    <!-- Error message column -->
    <td  class="text-left px-6 py-4 border-b border-gray-300">  
      {{ message }} 
    </td>

    <td class="text-right px-6 py-4 border-b border-gray-300">
      <button @click.stop="toggleDetails" class="toggle-btn">
        <span v-if="showDetails" class="triangle-down"></span>
        <span v-else class="triangle-left"></span>
      </button>
    </td>
    <td class="text-right px-6 py-4 border-b border-gray-300">
      <button @click.stop="showPhoenixDetails" class="bg-blue-500 text-white px-4 py-2 rounded mb-4">Details</button>
    </td>
    
  </tr>
  
  <!-- Show additional information when clicked -->
  <tr v-if="showDetails">
    <td colspan="3" class="details-cell text-left align-top px-4 py-4 border-b border-gray-300 text-gray-700 font-medium cursor-pointer" style="width: 55%;">
      <div>
        <div class="text-left text-lg font-semibold text-gray-700 mb-3">
          <strong>Full Validation Details:</strong>
        </div>
        <!-- Validation details list -->
        <div class="text-sm space-y-2">
          <p v-if="focusNode" class="break-words">
            <strong>Focus Node:</strong> {{ focusNode }}
          </p>
          <p v-if="resultPath" class="break-words">
            <strong>Result Path:</strong> {{ resultPath }}
          </p>
          <p v-if="value" class="break-words">
            <strong>Value:</strong> {{ value }}
          </p>
          <p v-if="message" class="break-words">
            <strong>Message:</strong> {{ message }}
          </p>
          <p v-if="propertyShape" class="break-words">
            <strong>Property Shape:</strong> {{ propertyShape }}
          </p>
          <p v-if="severity" class="break-words">
            <strong>Severity:</strong> {{ severity }}
          </p>
          <p v-if="targetClass && (Array.isArray(targetClass) ? targetClass.length > 0 : targetClass)" class="break-words">
            <strong>Target Class:</strong> {{ Array.isArray(targetClass) ? targetClass.join(', ') : targetClass }}
          </p>
          <p v-if="targetNode && (Array.isArray(targetNode) ? targetNode.length > 0 : targetNode)" class="break-words">
            <strong>Target Node:</strong> {{ Array.isArray(targetNode) ? targetNode.join(', ') : targetNode }}
          </p>
          <p v-if="targetSubjectsOf && (Array.isArray(targetSubjectsOf) ? targetSubjectsOf.length > 0 : targetSubjectsOf)" class="break-words">
            <strong>Target Subjects of:</strong> {{ Array.isArray(targetSubjectsOf) ? targetSubjectsOf.join(', ') : targetSubjectsOf }}
          </p>
          <p v-if="targetObjectsOf && (Array.isArray(targetObjectsOf) ? targetObjectsOf.length > 0 : targetObjectsOf)" class="break-words">
            <strong>Target Objects of:</strong> {{ Array.isArray(targetObjectsOf) ? targetObjectsOf.join(', ') : targetObjectsOf }}
          </p>
          <p v-if="nodeShape" class="break-words">
            <strong>Node Shape:</strong> {{ nodeShape }}
          </p>
          <p v-if="constraintComponent" class="break-words">
            <strong>Constraint Component:</strong> {{ constraintComponent }}
          </p>
        </div>
      </div>
    </td>
    <td colspan="2" class="details-cell text-left align-top px-4 py-4 border-b border-gray-300 text-gray-700 font-medium cursor-pointer" style="width: 45%;">
      <div>
        <div class="text-left text-lg font-semibold text-gray-700 mb-3">
          <strong>Shape Details:</strong>
        </div>
          <div v-if="shapes" class="text-sm">
            <p class="break-words"><strong>Shape:</strong> {{ shapes.shape || shapes.Shape || "None" }}</p>
            <p class="break-words"><strong>Type:</strong> {{ shapes.type || shapes.Type || "None" }}</p>
            <div class="details-list">
              <!-- Iterate over the Properties array (handle both naming conventions) -->
              <div v-if="(shapes.properties && shapes.properties.length > 0) || (shapes.Properties && shapes.Properties.length > 0)">
                <p class="font-semibold">Property Shapes Details:</p>
                <ul class="ml-4 list-disc">
                  <li v-for="(property, index) in (shapes.properties || shapes.Properties)" :key="index" class="mb-2">
                    <p class="break-words"><strong>{{ property.predicate || property.Predicate }}:</strong>
                      <span v-if="Array.isArray(property.object || property.Object)">
                        <ul class="ml-4 list-circle">
                          <li v-for="(obj, idx) in (property.object || property.Object)" :key="idx" class="break-words">{{ obj }}</li>
                        </ul>
                      </span>
                      <span v-else class="break-words">&nbsp; {{ property.object || property.Object }}</span>
                    </p>
                  </li>
                </ul>
              </div>
              <p v-else>No properties available.</p>
              <p class="break-words"><strong>Target Class:</strong> {{ shapes.targetClass || shapes.TargetClass || "None" }}</p>
            </div>
          </div>
          <div v-else class="text-sm">
            <p><strong>Shape:</strong> No shape details available</p>
            <p><strong>Type:</strong> No type information available</p>
            <p><strong>Properties:</strong> No properties available</p>
          </div>
        </div>
    </td>
  </tr>
  <ViolationDetails :show="showPhoenixDetailsModal" :explanation="explanation" :suggestion="suggestion" @close="closePhoenixDetails" />
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
import { defineProps, ref } from 'vue';
import ViolationDetails from './ViolationDetails.vue';

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
  explanation: [Object, String], // AI explanation for this violation
  session_id: String, // Add session_id to props
});

const showDetails = ref(false);
const showPhoenixDetailsModal = ref(false);
const explanation = ref("");
const suggestion = ref("");

const toggleDetails = () => {
  showDetails.value = !showDetails.value;
};

const showPhoenixDetails = () => {
  fetchViolationDetails();
};

const fetchViolationDetails = async () => {
  // Immediately show the modal with a loading state
  explanation.value = 'Loading AI-generated explanation...';
  suggestion.value = 'Please wait a moment.';
  showPhoenixDetailsModal.value = true;

  // If there's no session ID, we can't fetch anything
  if (!props.session_id) {
    explanation.value = 'Error: No session ID was provided for this violation.';
    suggestion.value = 'Cannot fetch details.';
    return;
  }

  try {
    // Use the session_id to fetch the enhanced explanation
    const response = await fetch(`/api/explanations/${props.session_id}`);
    
    if (response.ok) {
      const data = await response.json();
      if (data.status === 'completed') {
        // The backend returns an array of explanations. Find the one for this row.
        const violationExplanation = data.explanations[props.rowNumber - 1]; 
        if (violationExplanation) {
          explanation.value = violationExplanation.explanation_natural_language || 'Explanation received, but the content is empty.';
          suggestion.value = violationExplanation.suggestion_natural_language || 'No suggestion is available.';
        } else {
          explanation.value = 'Explanation not found for this violation.';
          suggestion.value = 'The backend did not provide details for this specific item.';
        }
      } else if (data.status === 'processing') {
        explanation.value = data.message || 'AI explanations are still being generated.';
        suggestion.value = 'Please close this dialog and try again in a moment.';
      } else {
        // Handle other statuses like 'error' from the backend if they are added
        explanation.value = data.message || 'An unknown error occurred on the backend.';
        suggestion.value = 'Please check the backend logs for more details.';
      }
    } else {
      explanation.value = 'Could not load details from the server.';
      suggestion.value = `The server responded with an error: ${response.status}`;
    }
  } catch (error) {
    console.error('Error fetching violation details:', error);
    explanation.value = 'A network error occurred while fetching the details.';
    suggestion.value = 'Please check your network connection and the browser console for more information.';
  }
};

const closePhoenixDetails = () => {
  showPhoenixDetailsModal.value = false;
};
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
</style>
