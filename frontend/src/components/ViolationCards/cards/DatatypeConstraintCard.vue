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
      <div class="datatype-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Wrong datatype</h4>
              <p class="alert-message">
                Value <code>{{ currentValue }}</code> ({{ currentDatatype }}) should be of type
                <code>{{ requiredDatatype }}</code>
              </p>
            </div>
          </div>
        </div>

        <!-- Datatype-specific Input -->
        <div class="fix-section">
          <h4 class="fix-title">Enter corrected value:</h4>

          <!-- Integer Input -->
          <div v-if="requiredDatatype === 'xsd:integer'" class="datatype-input">
            <div class="input-group">
              <label class="input-label">Integer value:</label>
              <div class="number-input">
                <button
                  @click="decrementNumber"
                  type="button"
                  class="number-btn"
                  :disabled="!canDecrement"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path>
                  </svg>
                </button>
                <input
                  v-model.number="correctedValue"
                  type="number"
                  step="1"
                  class="number-field"
                  @input="validateInteger"
                />
                <button
                  @click="incrementNumber"
                  type="button"
                  class="number-btn"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                  </svg>
                </button>
              </div>
              <div v-if="validationError" class="input-error">
                {{ validationError }}
              </div>
            </div>

            <!-- Quick value buttons -->
            <div class="quick-values">
              <span class="quick-label">Quick values:</span>
              <button
                v-for="val in quickIntegerValues"
                :key="val"
                @click="setQuickValue(val)"
                class="quick-btn"
              >
                {{ val }}
              </button>
            </div>
          </div>

          <!-- Decimal Input -->
          <div v-else-if="requiredDatatype === 'xsd:decimal'" class="datatype-input">
            <div class="input-group">
              <label class="input-label">Decimal value:</label>
              <div class="decimal-input">
                <input
                  v-model="correctedValue"
                  type="number"
                  step="0.01"
                  class="decimal-field"
                  @input="validateDecimal"
                />
                <span class="decimal-suffix">{{ getDecimalPrecision() }}</span>
              </div>
              <div v-if="validationError" class="input-error">
                {{ validationError }}
              </div>
            </div>

            <!-- Quick value buttons -->
            <div class="quick-values">
              <span class="quick-label">Quick values:</span>
              <button
                v-for="val in quickDecimalValues"
                :key="val"
                @click="setQuickValue(val)"
                class="quick-btn"
              >
                {{ val }}
              </button>
            </div>
          </div>

          <!-- Date Input -->
          <div v-else-if="requiredDatatype === 'xsd:date'" class="datatype-input">
            <div class="input-group">
              <label class="input-label">Date value:</label>
              <div class="date-input">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                <input
                  v-model="correctedValue"
                  type="date"
                  class="date-field"
                  @input="validateDate"
                />
              </div>
              <div v-if="validationError" class="input-error">
                {{ validationError }}
              </div>
            </div>

            <!-- Quick date buttons -->
            <div class="quick-values">
              <span class="quick-label">Quick dates:</span>
              <button
                v-for="date in quickDateValues"
                :key="date.label"
                @click="setQuickDate(date.value)"
                class="quick-btn"
              >
                {{ date.label }}
              </button>
            </div>
          </div>

          <!-- Boolean Input -->
          <div v-else-if="requiredDatatype === 'xsd:boolean'" class="datatype-input">
            <div class="input-group">
              <label class="input-label">Boolean value:</label>
              <div class="boolean-options">
                <label class="boolean-option">
                  <input
                    v-model="correctedValue"
                    type="radio"
                    value="true"
                    class="boolean-radio"
                  />
                  <span class="boolean-text">true</span>
                </label>
                <label class="boolean-option">
                  <input
                    v-model="correctedValue"
                    type="radio"
                    value="false"
                    class="boolean-radio"
                  />
                  <span class="boolean-text">false</span>
                </label>
              </div>
            </div>
          </div>

          <!-- String Input (default) -->
          <div v-else class="datatype-input">
            <div class="input-group">
              <label class="input-label">String value:</label>
              <input
                v-model="correctedValue"
                type="text"
                class="string-field"
                :placeholder="getStringPlaceholder()"
                @input="validateString"
              />
              <div v-if="validationError" class="input-error">
                {{ validationError }}
              </div>
            </div>
          </div>

          <!-- Validation Status -->
          <div class="validation-status">
            <div class="status-indicator" :class="validationStatus.class">
              <svg v-if="validationStatus.icon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="validationStatus.icon === 'check'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                <path v-else-if="validationStatus.icon === 'x'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
              {{ validationStatus.text }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #advanced-content>
      <div class="advanced-datatype-info">
        <h4>Datatype Constraint Details</h4>
        <div class="datatype-info-grid">
          <div class="info-item">
            <span class="info-label">Required Datatype:</span>
            <code class="info-value">{{ requiredDatatype }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Value:</span>
            <code class="info-value">{{ currentValue }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Datatype:</span>
            <code class="info-value">{{ currentDatatype }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Property:</span>
            <code class="info-value">{{ resultPath }}</code>
          </div>
        </div>

        <!-- Pattern if available -->
        <div v-if="context?.pattern" class="pattern-info">
          <h5>Pattern Constraint</h5>
          <code class="pattern-code">{{ context.pattern }}</code>
        </div>

        <!-- Range constraints if available -->
        <div v-if="context?.minValue !== undefined || context?.maxValue !== undefined" class="range-info">
          <h5>Value Range</h5>
          <div class="range-display">
            <span v-if="context?.minValue !== undefined" class="range-bound">Min: {{ context.minValue }}</span>
            <span v-if="context?.maxValue !== undefined" class="range-bound">Max: {{ context.maxValue }}</span>
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
  value: [String, Number],
  message: String,
  constraintComponent: String,
  context: Object,
  isLoading: Boolean,
  hasError: Boolean,
  errorMessage: String
})

const emit = defineEmits(['reject-fix', 'apply-fix'])

// Local state
const correctedValue = ref('')
const validationError = ref('')

// Computed properties
const requiredDatatype = computed(() => {
  return props.context?.requiredDatatype || props.context?.datatype || 'xsd:string'
})

const currentValue = computed(() => {
  return props.value || 'null'
})

const currentDatatype = computed(() => {
  // Try to infer current datatype from context or value
  if (props.context?.currentDatatype) {
    return props.context.currentDatatype
  }

  // Try to infer from the value format
  const value = String(props.value || '')
  if (value.includes('^^')) {
    return value.split('^^')[1]
  }
  if (value.includes('"') && value.includes('http')) {
    return 'xsd:anyURI'
  }
  if (!isNaN(value) && value.includes('.')) {
    return 'xsd:decimal'
  }
  if (!isNaN(value) && !value.includes('.')) {
    return 'xsd:integer'
  }
  if (value.toLowerCase() === 'true' || value.toLowerCase() === 'false') {
    return 'xsd:boolean'
  }
  if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
    return 'xsd:date'
  }

  return 'xsd:string'
})

const validationStatus = computed(() => {
  if (validationError.value) {
    return { icon: 'x', text: validationError.value, class: 'status-error' }
  }
  if (correctedValue.value && isValidValue()) {
    return { icon: 'check', text: `Valid ${requiredDatatype.value.split(':').pop()}`, class: 'status-valid' }
  }
  return { icon: null, text: 'Enter a value', class: 'status-neutral' }
})

const canApplyFix = computed(() => {
  return correctedValue.value && isValidValue()
})

const quickIntegerValues = computed(() => {
  const values = [0, 1, 18, 21, 25, 30, 40, 50]
  if (props.context?.minValue !== undefined) {
    values.unshift(props.context.minValue)
  }
  if (props.context?.maxValue !== undefined) {
    values.push(props.context.maxValue)
  }
  return [...new Set(values)].sort((a, b) => a - b)
})

const quickDecimalValues = computed(() => {
  const values = [0.0, 0.5, 1.0, 2.5, 5.0, 10.0]
  if (props.context?.minValue !== undefined) {
    values.unshift(parseFloat(props.context.minValue))
  }
  if (props.context?.maxValue !== undefined) {
    values.push(parseFloat(props.context.maxValue))
  }
  return [...new Set(values)].sort((a, b) => a - b)
})

const quickDateValues = computed(() => {
  const today = new Date()
  return [
    { label: 'Today', value: today.toISOString().split('T')[0] },
    { label: 'Yesterday', value: new Date(today - 86400000).toISOString().split('T')[0] },
    { label: 'Tomorrow', value: new Date(today.getTime() + 86400000).toISOString().split('T')[0] },
    { label: 'Last Week', value: new Date(today - 604800000).toISOString().split('T')[0] },
    { label: 'Next Week', value: new Date(today.getTime() + 604800000).toISOString().split('T')[0] }
  ]
})

const canDecrement = computed(() => {
  const min = props.context?.minValue
  return min === undefined || (correctedValue.value > min)
})

// Methods
const isValidValue = () => {
  if (!correctedValue.value) return false

  switch (requiredDatatype.value) {
    case 'xsd:integer':
      return !isNaN(correctedValue.value) && Number.isInteger(Number(correctedValue.value))
    case 'xsd:decimal':
      return !isNaN(correctedValue.value)
    case 'xsd:date':
      return correctedValue.value.match(/^\d{4}-\d{2}-\d{2}$/)
    case 'xsd:boolean':
      return ['true', 'false'].includes(correctedValue.value)
    default:
      return correctedValue.value.length > 0
  }
}

const validateInteger = () => {
  validationError.value = ''
  const value = Number(correctedValue.value)

  if (isNaN(value)) {
    validationError.value = 'Must be a valid integer'
    return
  }

  if (!Number.isInteger(value)) {
    validationError.value = 'Must be an integer (no decimals)'
    return
  }

  if (props.context?.minValue !== undefined && value < props.context.minValue) {
    validationError.value = `Must be at least ${props.context.minValue}`
    return
  }

  if (props.context?.maxValue !== undefined && value > props.context.maxValue) {
    validationError.value = `Must be no more than ${props.context.maxValue}`
    return
  }
}

const validateDecimal = () => {
  validationError.value = ''
  const value = Number(correctedValue.value)

  if (isNaN(value)) {
    validationError.value = 'Must be a valid number'
    return
  }

  if (props.context?.minValue !== undefined && value < props.context.minValue) {
    validationError.value = `Must be at least ${props.context.minValue}`
    return
  }

  if (props.context?.maxValue !== undefined && value > props.context.maxValue) {
    validationError.value = `Must be no more than ${props.context.maxValue}`
    return
  }
}

const validateDate = () => {
  validationError.value = ''

  if (!correctedValue.value.match(/^\d{4}-\d{2}-\d{2}$/)) {
    validationError.value = 'Must be a valid date (YYYY-MM-DD)'
    return
  }

  const date = new Date(correctedValue.value)
  if (isNaN(date.getTime())) {
    validationError.value = 'Must be a valid date'
    return
  }

  if (props.context?.minDate && date < new Date(props.context.minDate)) {
    validationError.value = `Must be on or after ${props.context.minDate}`
    return
  }

  if (props.context?.maxDate && date > new Date(props.context.maxDate)) {
    validationError.value = `Must be on or before ${props.context.maxDate}`
    return
  }
}

const validateString = () => {
  validationError.value = ''

  if (props.context?.pattern) {
    try {
      const regex = new RegExp(props.context.pattern)
      if (!regex.test(correctedValue.value)) {
        validationError.value = `Must match pattern: ${props.context.pattern}`
        return
      }
    } catch (e) {
      // Invalid regex pattern, ignore validation
    }
  }
}

const getStringPlaceholder = () => {
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (propertyName.includes('name')) return 'e.g., John Doe'
  if (propertyName.includes('email')) return 'e.g., user@example.com'
  if (propertyName.includes('url')) return 'e.g., https://example.com'
  if (propertyName.includes('phone')) return 'e.g., +1-555-123-4567'

  return 'Enter a string value...'
}

const getDecimalPrecision = () => {
  const precision = props.context?.precision || 2
  return `(${precision} decimal places)`
}

const incrementNumber = () => {
  const value = Number(correctedValue.value) || 0
  correctedValue.value = value + 1
}

const decrementNumber = () => {
  const value = Number(correctedValue.value) || 0
  const min = props.context?.minValue
  if (min === undefined || value - 1 >= min) {
    correctedValue.value = value - 1
  }
}

const setQuickValue = (value) => {
  correctedValue.value = value
}

const setQuickDate = (date) => {
  correctedValue.value = date
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  if (!isValidValue()) return

  try {
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'

    // Format the value with the correct datatype
    let formattedValue
    switch (requiredDatatype.value) {
      case 'xsd:integer':
      case 'xsd:decimal':
        formattedValue = `"${correctedValue.value}"^^${requiredDatatype.value}`
        break
      case 'xsd:date':
        formattedValue = `"${correctedValue.value}"^^${requiredDatatype.value}`
        break
      case 'xsd:boolean':
        formattedValue = `"${correctedValue.value}"^^${requiredDatatype.value}`
        break
      default:
        formattedValue = `"${correctedValue.value}"`
    }

    let sparqlQuery = ''
    if (props.value) {
      // Replace existing value
      sparqlQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> ${formattedValue} .
  }
}`
    } else {
      // Add new value
      sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> ${formattedValue} .
  }
}`
    }

    await api.post('/api/repair', {
      repair_query: sparqlQuery,
      session_id: sessionId
    })

    emit('apply-fix', {
      newValue: formattedValue,
      sparqlQuery: sparqlQuery,
      fixType: 'datatype_conversion'
    })
  } catch (error) {
    console.error('Error applying datatype constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Initialize corrected value from current value
watch(() => props.value, (newValue) => {
  if (newValue !== undefined) {
    // Extract the literal value from the current value
    const valueStr = String(newValue)
    if (valueStr.includes('"')) {
      correctedValue.value = valueStr.replace(/^"|".*$/g, '')
    } else {
      correctedValue.value = valueStr
    }
  }
}, { immediate: true })
</script>

<style scoped>
.datatype-constraint-content {
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

.fix-section {
  @apply space-y-4;
}

.fix-title {
  @apply text-sm font-semibold text-gray-700;
}

.datatype-input {
  @apply space-y-3;
}

.input-group {
  @apply space-y-2;
}

.input-label {
  @apply block text-sm font-medium text-gray-700;
}

.number-input {
  @apply flex items-center gap-2;
}

.number-btn {
  @apply p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed;
}

.number-field {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm text-center;
}

.decimal-input {
  @apply flex items-center gap-2;
}

.decimal-field {
  @apply flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.decimal-suffix {
  @apply text-sm text-gray-500;
}

.date-input {
  @apply relative flex items-center gap-2;
}

.date-input svg {
  @apply absolute left-3 pointer-events-none;
}

.date-field {
  @apply w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.boolean-options {
  @apply flex gap-4;
}

.boolean-option {
  @apply flex items-center gap-2 cursor-pointer;
}

.boolean-radio {
  @apply h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500;
}

.boolean-text {
  @apply text-sm text-gray-700;
}

.string-field {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.input-error {
  @apply text-sm text-red-600;
}

.validation-status {
  @apply pt-2;
}

.status-indicator {
  @apply flex items-center gap-2 text-sm font-medium;
}

.status-valid {
  @apply text-green-700;
}

.status-error {
  @apply text-red-700;
}

.status-neutral {
  @apply text-gray-500;
}

.quick-values {
  @apply flex items-center gap-2 flex-wrap;
}

.quick-label {
  @apply text-sm text-gray-600;
}

.quick-btn {
  @apply px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium transition-colors;
}

.advanced-datatype-info {
  @apply space-y-4;
}

.datatype-info-grid {
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

.pattern-info h5,
.range-info h5 {
  @apply text-sm font-medium text-gray-700 mb-2;
}

.pattern-code {
  @apply text-xs font-mono text-gray-700 bg-gray-50 px-2 py-1 rounded;
}

.range-display {
  @apply flex gap-4;
}

.range-bound {
  @apply text-sm text-gray-600;
}
</style>