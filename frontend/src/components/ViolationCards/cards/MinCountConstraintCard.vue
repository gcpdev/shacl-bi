<template>
  <ShaclViolationCard
    :focus-node="focusNode"
    :result-path="resultPath"
    :value="value"
    :message="message"
    :constraint-component="constraintComponent"
    :context="context"
    :is-loading="isLoading"
    :has-error="hasError"
    :error-message="errorMessage"
    :can-apply-fix="canApplyFix"
    @reject-fix="handleRejectFix"
    @apply-fix="handleApplyFix"
  >
    <template #constraint-content>
      <div class="mincount-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Missing required values</h4>
              <p class="alert-message">
                Property <code>{{ formatPropertyName(resultPath) }}</code> has
                <span class="count-badge current">{{ currentCount }}</span> values but requires at least
                <span class="count-badge required">{{ requiredCount }}</span>
              </p>
            </div>
          </div>

          <!-- Progress Indicator -->
          <div class="progress-section">
            <div class="progress-info">
              <span class="progress-text">{{ currentCount }} of {{ requiredCount }} required values</span>
              <span class="progress-percentage">{{ progressPercentage }}%</span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${progressPercentage}%` }"
                :class="{ 'progress-complete': progressPercentage >= 100 }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Add Values Section -->
        <div class="add-values-section">
          <h4 class="section-title">
            ➕ Add {{ missingCount }} required {{ missingCount === 1 ? 'value' : 'values' }}:
          </h4>

          <!-- Dynamic value inputs -->
          <div class="value-inputs">
            <div
              v-for="(inputValue, index) in newValues"
              :key="index"
              class="value-input-row"
            >
              <div class="input-number">{{ index + 1 }}</div>
              <div class="input-group">
                <label class="input-label">
                  Value {{ index + 1 }} {{ index < requiredCount ? '(required)' : '(optional)' }}:
                </label>
                <div class="input-with-type">
                  <input
                    v-model="newValues[index]"
                    type="text"
                    :placeholder="getInputPlaceholder(index)"
                    class="value-input"
                    @input="validateValue(index)"
                  />
                  <select
                    v-model="valueTypes[index]"
                    class="type-select"
                    @change="validateValue(index)"
                  >
                    <option value="string">String</option>
                    <option value="integer">Integer</option>
                    <option value="decimal">Decimal</option>
                    <option value="date">Date</option>
                    <option value="boolean">Boolean</option>
                    <option value="uri">URI/IRI</option>
                  </select>
                </div>
                <div v-if="validationErrors[index]" class="input-error">
                  {{ validationErrors[index] }}
                </div>
              </div>

              <!-- Remove button for optional inputs -->
              <button
                v-if="index >= requiredCount"
                @click="removeValueInput(index)"
                type="button"
                class="remove-btn"
                title="Remove this value"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- Add more values button -->
          <button
            @click="addValueInput"
            type="button"
            class="add-more-btn"
            :disabled="newValues.length >= 10"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Add another value
          </button>

          <!-- Quick suggestions based on property name -->
          <div v-if="quickSuggestions.length > 0" class="quick-suggestions">
            <h5 class="suggestions-title">💡 Quick suggestions:</h5>
            <div class="suggestion-list">
              <button
                v-for="suggestion in quickSuggestions"
                :key="suggestion.value"
                @click="applySuggestion(suggestion)"
                type="button"
                class="suggestion-btn"
              >
                <span class="suggestion-value">{{ suggestion.value }}</span>
                <span class="suggestion-type">{{ suggestion.type }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Current Values Display -->
        <div v-if="currentValues.length > 0" class="current-values-section">
          <h5 class="current-title">Current values:</h5>
          <div class="current-values-list">
            <div
              v-for="(currentValue, index) in currentValues"
              :key="index"
              class="current-value-item"
            >
              <code class="current-value">{{ formatValue(currentValue) }}</code>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #advanced-content>
      <div class="advanced-mincount-info">
        <h4>Minimum Count Constraint Details</h4>
        <div class="mincount-info-grid">
          <div class="info-item">
            <span class="info-label">Required Count:</span>
            <code class="info-value">{{ requiredCount }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Count:</span>
            <code class="info-value">{{ currentCount }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Missing Count:</span>
            <code class="info-value">{{ missingCount }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Property:</span>
            <code class="info-value">{{ formatPropertyName(resultPath) }}</code>
          </div>
        </div>

        <!-- Property hints -->
        <div v-if="context?.propertyHints" class="property-hints">
          <h5>Property Information</h5>
          <div class="hints-grid">
            <div v-if="context.propertyHints.description" class="hint-item">
              <span class="hint-label">Description:</span>
              <span class="hint-value">{{ context.propertyHints.description }}</span>
            </div>
            <div v-if="context.propertyHints.expectedType" class="hint-item">
              <span class="hint-label">Expected Type:</span>
              <code class="hint-value">{{ context.propertyHints.expectedType }}</code>
            </div>
            <div v-if="context.propertyHints.examples" class="hint-item">
              <span class="hint-label">Examples:</span>
              <div class="hint-examples">
                <code
                  v-for="example in context.propertyHints.examples"
                  :key="example"
                  class="hint-example"
                >
                  {{ example }}
                </code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </ShaclViolationCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import ShaclViolationCard from '../ShaclViolationCard.vue'
import api from '@/utils/api'

const props = defineProps({
  focusNode: String,
  resultPath: String,
  value: [String, Number, Array],
  message: String,
  constraintComponent: String,
  context: Object,
  isLoading: Boolean,
  hasError: Boolean,
  errorMessage: String
})

const emit = defineEmits(['reject-fix', 'apply-fix'])

// Local state
const newValues = ref([])
const valueTypes = ref([])
const validationErrors = ref([])

// Computed properties
const requiredCount = computed(() => {
  return props.context?.minCount || props.context?.requiredCount || 1
})

const currentValues = computed(() => {
  if (props.context?.currentValues) {
    return props.context.currentValues
  }

  // Handle different value formats
  if (Array.isArray(props.value)) {
    return props.value
  }

  if (props.value) {
    return [props.value]
  }

  return []
})

const currentCount = computed(() => {
  return currentValues.value.length
})

const missingCount = computed(() => {
  return Math.max(0, requiredCount.value - currentCount.value)
})

const progressPercentage = computed(() => {
  return Math.round((currentCount.value / requiredCount.value) * 100)
})

const canApplyFix = computed(() => {
  // Check if required number of valid values are provided
  const validRequiredValues = newValues.value
    .slice(0, requiredCount.value)
    .filter((_, index) => !validationErrors.value[index] && newValues.value[index]?.trim())

  return validRequiredValues.length >= requiredCount.value
})

const quickSuggestions = computed(() => {
  const propertyName = props.resultPath?.toLowerCase() || ''
  const suggestions = []

  if (propertyName.includes('name')) {
    suggestions.push(
      { value: 'Unknown Name', type: 'string' },
      { value: 'John Doe', type: 'string' },
      { value: 'Jane Smith', type: 'string' }
    )
  }

  if (propertyName.includes('email')) {
    suggestions.push(
      { value: 'unknown@example.com', type: 'string' },
      { value: 'contact@example.org', type: 'string' }
    )
  }

  if (propertyName.includes('phone') || propertyName.includes('telephone')) {
    suggestions.push(
      { value: '+1-555-123-4567', type: 'string' },
      { value: '+44-20-7946-0958', type: 'string' }
    )
  }

  if (propertyName.includes('age')) {
    suggestions.push(
      { value: '0', type: 'integer' },
      { value: '18', type: 'integer' },
      { value: '25', type: 'integer' }
    )
  }

  if (propertyName.includes('date')) {
    const today = new Date().toISOString().split('T')[0]
    suggestions.push(
      { value: today, type: 'date' },
      { value: '2024-01-01', type: 'date' }
    )
  }

  if (propertyName.includes('url') || propertyName.includes('website')) {
    suggestions.push(
      { value: 'https://example.com', type: 'uri' },
      { value: 'http://www.example.org', type: 'uri' }
    )
  }

  if (propertyName.includes('description') || propertyName.includes('comment')) {
    suggestions.push(
      { value: 'No description available', type: 'string' }
    )
  }

  // Add context-specific suggestions if available
  if (props.context?.suggestions) {
    suggestions.push(...props.context.suggestions)
  }

  return suggestions.slice(0, 6) // Limit to 6 suggestions
})

// Methods
const formatPropertyName = (uri) => {
  if (!uri) return ''
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri
  }
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

const formatValue = (value) => {
  if (!value) return 'null'
  if (typeof value === 'string') {
    if (value.startsWith('http')) {
      return `<${value}>`
    }
    return `"${value}"`
  }
  return String(value)
}

const getInputPlaceholder = (index) => {
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (index < requiredCount.value) {
    if (propertyName.includes('name')) return 'e.g., John Doe'
    if (propertyName.includes('email')) return 'e.g., user@example.com'
    if (propertyName.includes('phone')) return 'e.g., +1-555-123-4567'
    if (propertyName.includes('age')) return 'e.g., 25'
    if (propertyName.includes('date')) return 'e.g., 2024-01-01'
    if (propertyName.includes('url')) return 'e.g., https://example.com'

    return `Required value ${index + 1}`
  }

  return 'Optional value...'
}

const validateValue = (index) => {
  const value = newValues.value[index]
  const type = valueTypes.value[index]

  if (!value || !value.trim()) {
    validationErrors.value[index] = index < requiredCount.value ? 'This value is required' : ''
    return
  }

  validationErrors.value[index] = ''

  switch (type) {
    case 'integer':
      if (isNaN(value) || !Number.isInteger(Number(value))) {
        validationErrors.value[index] = 'Must be an integer'
      }
      break
    case 'decimal':
      if (isNaN(value)) {
        validationErrors.value[index] = 'Must be a valid number'
      }
      break
    case 'date':
      if (!value.match(/^\d{4}-\d{2}-\d{2}$/)) {
        validationErrors.value[index] = 'Must be a valid date (YYYY-MM-DD)'
      } else {
        const date = new Date(value)
        if (isNaN(date.getTime())) {
          validationErrors.value[index] = 'Must be a valid date'
        }
      }
      break
    case 'boolean':
      if (!['true', 'false'].includes(value.toLowerCase())) {
        validationErrors.value[index] = 'Must be true or false'
      }
      break
    case 'uri':
      if (!value.startsWith('http')) {
        validationErrors.value[index] = 'Must be a valid URI/IRI (starting with http)'
      }
      break
  }

  // Apply additional constraints from context if available
  if (props.context?.constraints) {
    const constraints = props.context.constraints
    const numValue = Number(value)

    if (constraints.minValue !== undefined && numValue < constraints.minValue) {
      validationErrors.value[index] = `Must be at least ${constraints.minValue}`
    }
    if (constraints.maxValue !== undefined && numValue > constraints.maxValue) {
      validationErrors.value[index] = `Must be no more than ${constraints.maxValue}`
    }
    if (constraints.minLength && value.length < constraints.minLength) {
      validationErrors.value[index] = `Must be at least ${constraints.minLength} characters`
    }
    if (constraints.maxLength && value.length > constraints.maxLength) {
      validationErrors.value[index] = `Must be no more than ${constraints.maxLength} characters`
    }
  }
}

const addValueInput = () => {
  if (newValues.value.length >= 10) return // Limit to reasonable number

  newValues.value.push('')
  valueTypes.value.push('string')
  validationErrors.value.push('')
}

const removeValueInput = (index) => {
  newValues.value.splice(index, 1)
  valueTypes.value.splice(index, 1)
  validationErrors.value.splice(index, 1)
}

const applySuggestion = (suggestion) => {
  // Find the first empty or invalid slot to apply the suggestion
  let targetIndex = -1

  for (let i = 0; i < Math.max(requiredCount.value, newValues.value.length); i++) {
    if (!newValues.value[i] || validationErrors.value[i]) {
      targetIndex = i
      break
    }
  }

  if (targetIndex === -1) {
    // Add a new slot if all current slots are filled
    addValueInput()
    targetIndex = newValues.value.length - 1
  }

  newValues.value[targetIndex] = suggestion.value
  valueTypes.value[targetIndex] = suggestion.type
  validateValue(targetIndex)
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  if (!canApplyFix.value) return

  try {
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'

    // Prepare the SPARQL INSERT statements
    const insertClauses = []

    for (let i = 0; i < newValues.value.length; i++) {
      const value = newValues.value[i]
      const type = valueTypes.value[i]

      if (!value || !value.trim() || validationErrors.value[i]) {
        continue
      }

      let formattedValue
      switch (type) {
        case 'integer':
          formattedValue = `"${value}"^^xsd:integer`
          break
        case 'decimal':
          formattedValue = `"${value}"^^xsd:decimal`
          break
        case 'date':
          formattedValue = `"${value}"^^xsd:date`
          break
        case 'boolean':
          formattedValue = `"${value.toLowerCase()}"^^xsd:boolean`
          break
        case 'uri':
          formattedValue = `<${value}>`
          break
        default:
          formattedValue = `"${value}"`
      }

      insertClauses.push(`    <${props.focusNode}> <${props.resultPath}> ${formattedValue} .`)
    }

    if (insertClauses.length === 0) {
      throw new Error('No valid values to insert')
    }

    const sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
${insertClauses.join('\n')}
  }
}`

    await api.post('/api/repair', {
      repair_query: sparqlQuery,
      session_id: sessionId
    })

    emit('apply-fix', {
      newValues: newValues.value.filter((_, index) => !validationErrors.value[index] && newValues.value[index]?.trim()),
      sparqlQuery: sparqlQuery,
      fixType: 'add_missing_values',
      addedCount: insertClauses.length
    })
  } catch (error) {
    console.error('Error applying minCount constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Initialize with required number of empty inputs
watch(() => requiredCount.value, (newRequiredCount) => {
  const currentInputs = newValues.value.length
  if (currentInputs < newRequiredCount) {
    for (let i = currentInputs; i < newRequiredCount; i++) {
      newValues.value.push('')
      valueTypes.value.push('string')
      validationErrors.value.push('')
    }
  }
}, { immediate: true })

// Initialize with one empty input if no required count is available
if (requiredCount.value > 0 && newValues.value.length === 0) {
  for (let i = 0; i < requiredCount.value; i++) {
    newValues.value.push('')
    valueTypes.value.push('string')
    validationErrors.value.push('')
  }
}
</script>

<style scoped>
.mincount-constraint-content {
  @apply space-y-4;
}

.violation-details {
  @apply space-y-3;
}

.alert {
  @apply flex items-start gap-3 p-4 rounded-lg border;
}

.alert-warning {
  @apply bg-yellow-50 border-yellow-200;
}

.alert-title {
  @apply text-sm font-semibold text-yellow-800;
}

.alert-message {
  @apply text-sm text-yellow-700 mt-1;
}

.alert-message code {
  @apply bg-yellow-100 px-1 py-0.5 rounded text-xs font-mono;
}

.count-badge {
  @apply px-2 py-1 rounded text-xs font-medium;
}

.count-badge.current {
  @apply bg-red-100 text-red-800;
}

.count-badge.required {
  @apply bg-green-100 text-green-800;
}

.progress-section {
  @apply space-y-2;
}

.progress-info {
  @apply flex justify-between items-center text-sm;
}

.progress-text {
  @apply text-gray-600;
}

.progress-percentage {
  @apply font-medium text-gray-700;
}

.progress-bar {
  @apply w-full bg-gray-200 rounded-full h-2;
}

.progress-fill {
  @apply bg-blue-500 h-2 rounded-full transition-all duration-300;
}

.progress-fill.progress-complete {
  @apply bg-green-500;
}

.add-values-section {
  @apply space-y-4;
}

.section-title {
  @apply text-sm font-semibold text-gray-700;
}

.value-inputs {
  @apply space-y-3;
}

.value-input-row {
  @apply flex items-start gap-3 p-3 border border-gray-200 rounded-lg;
}

.input-number {
  @apply flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium;
}

.input-group {
  @apply flex-1 space-y-2;
}

.input-label {
  @apply block text-sm font-medium text-gray-700;
}

.input-with-type {
  @apply flex gap-2;
}

.value-input {
  @apply flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.type-select {
  @apply px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.input-error {
  @apply text-sm text-red-600;
}

.remove-btn {
  @apply p-2 text-red-500 hover:bg-red-50 rounded-md transition-colors;
}

.add-more-btn {
  @apply inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm font-medium transition-colors;
}

.quick-suggestions {
  @apply space-y-2;
}

.suggestions-title {
  @apply text-sm font-medium text-gray-700;
}

.suggestion-list {
  @apply flex flex-wrap gap-2;
}

.suggestion-btn {
  @apply flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-md text-sm transition-colors;
}

.suggestion-value {
  @apply font-medium text-gray-700;
}

.suggestion-type {
  @apply text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded;
}

.current-values-section {
  @apply space-y-2;
}

.current-title {
  @apply text-sm font-medium text-gray-700;
}

.current-values-list {
  @apply space-y-1;
}

.current-value-item {
  @apply p-2 bg-gray-50 rounded border border-gray-200;
}

.current-value {
  @apply text-sm font-mono text-gray-700;
}

.advanced-mincount-info {
  @apply space-y-4;
}

.mincount-info-grid {
  @apply grid grid-cols-2 gap-3;
}

.info-item {
  @apply space-y-1;
}

.info-label {
  @apply text-xs font-medium text-gray-500;
}

.info-value {
  @apply text-xs font-mono text-gray-700 bg-gray-50 px-2 py-1 rounded;
}

.property-hints {
  @apply space-y-3;
}

.property-hints h5 {
  @apply text-sm font-medium text-gray-700;
}

.hints-grid {
  @apply space-y-2;
}

.hint-item {
  @apply space-y-1;
}

.hint-label {
  @apply text-xs font-medium text-gray-500;
}

.hint-value {
  @apply text-sm text-gray-700;
}

.hint-examples {
  @apply space-y-1;
}

.hint-example {
  @apply block text-xs font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded;
}
</style>