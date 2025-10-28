<template>
  <tr class="even:bg-gray-50 hover:bg-blue-50 transition-colors" @click="toggleDetails">
    <td class="text-left px-6 py-4 border-b border-gray-300">{{ rowNumber }}</td>

    <td class="text-left px-6 py-4 border-b border-gray-300 violation-triple">
      <div class="triple-line">
        <span class="triple-subject">{{ formatNodeName(focusNode) }}</span>
      </div>
      <div class="triple-line">
        <span class="triple-predicate">{{ formatPropertyName(resultPath) }}</span>
      </div>
      <div class="triple-line">
        <span class="triple-object">{{ value }}</span>
      </div>
    </td>

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

  <!-- Details Section with SHACL Violation Cards -->
  <tr v-if="showDetails">
    <td colspan="4" class="details-cell px-6 py-6 border-b border-gray-300">
      <div class="violation-cards-container">
  
        <!-- SHACL Violation Card -->
        <component
          :is="violationCardComponent"
          :focus-node="focusNode"
          :result-path="resultPath"
          :value="value"
          :message="message"
          :constraint-component="constraintComponent"
          :context="enhancedContext"
          :is-loading="explanationLoading || isApplyingFix"
          :has-error="hasError"
          :error-message="errorMessage"
          :can-apply-fix="canApplyFix"
          @reject-fix="handleRejectFix"
          @apply-fix="handleApplyFix"
        />

        <!-- Optional: Legacy explanation section for reference -->
        <details v-if="explanationData" class="mt-4 border rounded-lg">
          <summary class="p-3 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2 2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            AI Explanation Details
          </summary>
          <div class="p-3 border-t bg-gray-50 space-y-3">
            <div>
              <h5 class="text-sm font-medium text-gray-700">Problem Explanation:</h5>
              <p class="text-sm text-gray-600 mt-1">{{ explanationData.explanation_natural_language }}</p>
            </div>
            <div>
              <h5 class="text-sm font-medium text-gray-700">Suggested Solution:</h5>
              <p class="text-sm text-gray-600 mt-1">{{ explanationData.suggestion_natural_language }}</p>
            </div>
            <div v-if="explanationData.proposed_repair?.query">
              <h5 class="text-sm font-medium text-gray-700">SPARQL Query:</h5>
              <pre class="text-xs font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto bg-white p-2 rounded border border-gray-200 mt-1">{{ explanationData.proposed_repair.query }}</pre>
            </div>
          </div>
        </details>
      </div>
    </td>
  </tr>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getConstraintCard } from '@/components/ViolationCards/ConstraintCardRegistry.js'
import api from '@/utils/api'

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
  context: Object, // PHOENIX-style context with example values
})

const emit = defineEmits(['violation-fixed', 'violation-rejected'])

// State
const showDetails = ref(false)
const explanationData = ref(null)
const explanationLoading = ref(false)
const autoLoadingExplanations = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const isApplyingFix = ref(false)

// Computed properties
const violationCardComponent = computed(() => {
  const component = getConstraintCard(props.constraintComponent)
  return component
})

const enhancedContext = computed(() => {
  // Merge existing context with additional information from explanation data
  const baseContext = props.context || {}

  // Add constraint-specific context from explanation data
  if (explanationData.value?.constraint_info) {
    Object.assign(baseContext, explanationData.value.constraint_info)
  }

  // Add SPARQL query if available
  if (explanationData.value?.proposed_repair?.query) {
    baseContext.sparqlQuery = explanationData.value.proposed_repair.query
  }

  return baseContext
})

// Helper functions
const formatNodeName = (uri) => {
  if (!uri) return ''

  // If it's already formatted (has prefix), return as is
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri
  }

  // Extract local name from URI
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

const formatPropertyName = (uri) => {
  if (!uri) return ''

  // If it's already formatted (has prefix), return as is
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri
  }

  // Extract local name from URI
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

// Event handlers
const toggleDetails = () => {
  showDetails.value = !showDetails.value
}

const loadExplanation = async () => {
  if (!props.focusNode) return

  explanationLoading.value = true
  autoLoadingExplanations.value = false
  hasError.value = false
  errorMessage.value = ''

  try {
    const session_id = localStorage.getItem('shacl_session_id')
    const response = await api.post('/api/explanation', {
      violation: {
        focus_node: props.focusNode,
        property_path: props.resultPath,
        constraint_id: props.constraintComponent,
        value: props.value,
        message: props.message
      },
      session_id
    })

    explanationData.value = response.data
  } catch (error) {
    console.error('Error loading explanation:', error)
    hasError.value = true
    errorMessage.value = 'Failed to load explanation'
  } finally {
    explanationLoading.value = false
  }
}

const autoLoadExplanation = () => {
  // Auto-load explanation with a short delay to show "checking" state
  autoLoadingExplanations.value = true
  setTimeout(() => {
    if (autoLoadingExplanations.value) {
      loadExplanation()
    }
  }, 500)
}

const handleRejectFix = (data) => {
  console.log('Violation fix rejected:', data)
  emit('violation-rejected', {
    focusNode: props.focusNode,
    resultPath: props.resultPath,
    constraintComponent: props.constraintComponent,
    ...data
  })
}

const handleApplyFix = async (data) => {
  isApplyingFix.value = true
  hasError.value = false
  errorMessage.value = ''

  try {
    // Some cards may already have applied the fix (they make the API call themselves)
    // In that case, they provide the results in the data
    if (data.alreadyApplied) {
      console.log('Fix already applied by card component:', data)
      emit('violation-fixed', data)
      return
    }

    // For cards that don't apply the fix themselves, we can apply it here
    // This is a fallback mechanism
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'

    if (data.sparqlQuery) {
      await api.post('/api/repair', {
        repair_query: data.sparqlQuery,
        session_id: sessionId
      })
    }

    console.log('Violation fix applied:', data)
    emit('violation-fixed', {
      ...data,
      focusNode: props.focusNode,
      resultPath: props.resultPath,
      constraintComponent: props.constraintComponent
    })

  } catch (error) {
    console.error('Error applying fix:', error)
    hasError.value = true
    errorMessage.value = 'Failed to apply fix: ' + (error.response?.data?.error || error.message)
  } finally {
    isApplyingFix.value = false
  }
}

// Watchers
watch(() => showDetails.value, (newValue) => {
  if (newValue && !explanationData.value && !explanationLoading.value && !autoLoadingExplanations.value) {
    // Automatically try to load explanation when user opens details
    autoLoadExplanation()
  }
})

watch(() => autoLoadingExplanations.value, (newValue) => {
  if (newValue && !explanationData.value && !explanationLoading.value) {
    loadExplanation()
  }
})

// Load explanation data if it becomes available from parent
watch(() => props.context, (newContext) => {
  if (newContext?.explanationData) {
    explanationData.value = newContext.explanationData
  }
}, { immediate: true, deep: true })
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}

td, th {
  padding: 1px 1px;
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
  border-right: 7px solid black;
}

.triangle-down {
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid black;
}

.details-cell {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 16px !important;
}

.violation-cards-container {
  max-width: 100%;
  overflow-x: hidden;
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

/* Make sure long URIs in explanation section wrap */
.text-gray-800 {
  word-break: break-all;
  overflow-wrap: break-word;
}
</style>