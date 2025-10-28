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
      <div class="mininclusive-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Value too small</h4>
              <p class="alert-message">
                Value <code>{{ currentValue }}</code> is below the minimum of <code>{{ minValue }}</code>
              </p>
            </div>
          </div>
        </div>

        <!-- Visual Range Indicator -->
        <div class="range-indicator">
          <div class="range-bar">
            <div class="range-line"></div>
            <div class="range-mark min-value" :style="{ left: getMinValuePosition() + '%' }"></div>
            <div class="range-mark current-value" :style="{ left: getCurrentValuePosition() + '%' }"></div>
            <div v-if="hasBothConstraints" class="range-mark max-value" :style="{ left: '95%' }"></div>
          </div>
          <div class="range-labels">
            <span class="range-label start">{{ getRangeStartLabel() }}</span>
            <span class="range-label current">Current: {{ currentValue }}</span>
            <span class="range-label end">{{ getRangeEndLabel() }}</span>
          </div>
        </div>

        <!-- Fix Section -->
        <div class="fix-section">
          <h4 class="fix-title">Enter valid value (≥ {{ minValue }}):</h4>

          <!-- Slider Input -->
          <div class="slider-input">
            <div class="slider-container">
              <input
                v-model.number="correctedValue"
                type="range"
                :min="minValue"
                :max="getSliderMax()"
                step="getStepSize()"
                class="value-slider"
                @input="validateValue"
              />
              <div class="slider-labels">
                <span>{{ minValue }}</span>
                <span>{{ getSliderMax() }}</span>
              </div>
            </div>
            <div class="slider-output">
              <input
                v-model.number="correctedValue"
                type="number"
                :min="minValue"
                :step="getStepSize()"
                class="value-input"
                @input="validateValue"
              />
              <span class="input-unit">{{ getUnit() }}</span>
            </div>
          </div>

          <!-- Quick Fix Buttons -->
          <div class="quick-fixes">
            <span class="quick-label">Quick fixes:</span>
            <button
              @click="setToMinimum"
              type="button"
              class="quick-btn"
            >
              Set to {{ minValue }} (minimum)
            </button>
            <button
              v-for="suggestion in quickSuggestions"
              :key="suggestion.value"
              @click="correctedValue = suggestion.value"
              type="button"
              class="quick-btn"
            >
              {{ suggestion.label }}
            </button>
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
      <div class="advanced-mininclusive-info">
        <h4>Minimum Value Constraint Details</h4>
        <div class="mininclusive-info-grid">
          <div class="info-item">
            <span class="info-label">Minimum Value:</span>
            <code class="info-value">{{ minValue }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Value:</span>
            <code class="info-value">{{ currentValue }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Property:</span>
            <code class="info-value">{{ formatPropertyName(resultPath) }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Inclusive:</span>
            <code class="info-value">Yes (>=)</code>
          </div>
        </div>
      </div>
    </template>
  </ShaclViolationCard>
</template>

<script setup>
import { ref, computed } from 'vue'
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
const correctedValue = ref(0)

// Computed properties
const constraintRange = computed(() => {
  // Extract range from SHACL message if available (format: "between X and Y")
  if (props.message) {
    const betweenMatch = props.message.match(/between\s+(\d+)(?:\s+\([^)]*\))?\s+and\s+(\d+)(?:\s+\([^)]*\))?/i)
    if (betweenMatch) {
      return {
        min: Number(betweenMatch[1]), // First number is the minimum
        max: Number(betweenMatch[2])  // Second number is the maximum
      }
    }
  }

  return null
})

const minValue = computed(() => {
  // First try to get from context
  if (props.context?.minValue) return props.context.minValue
  if (props.context?.minimum) return props.context.minimum

  // Use extracted range if available
  if (constraintRange.value) {
    return constraintRange.value.min
  }

  // Extract from other common patterns
  if (props.message) {
    const minMatch = props.message.match(/minimum(?:\s+of)?\s+(\d+)/i)
    if (minMatch) {
      return Number(minMatch[1])
    }

    // Extract from "must be ≥ X" pattern
    const greaterThanMatch = props.message.match(/must be\s+≥?\s*(\d+)/i)
    if (greaterThanMatch) {
      return Number(greaterThanMatch[1])
    }
  }

  // Default fallback
  return 0
})

const currentValue = computed(() => {
  return Number(props.value) || 0
})

const validationStatus = computed(() => {
  if (correctedValue.value >= minValue.value) {
    return { icon: 'check', text: `Valid (≥ ${minValue.value})`, class: 'status-valid' }
  } else {
    return { icon: 'x', text: `Too small (must be ≥ ${minValue.value})`, class: 'status-error' }
  }
})

const canApplyFix = computed(() => {
  return correctedValue.value >= minValue.value
})

const hasBothConstraints = computed(() => {
  // Check if there's also a MaxInclusive constraint on the same property
  return props.context?.maxValue !== undefined ||
         props.context?.maximum !== undefined ||
         constraintRange.value !== null
})

const quickSuggestions = computed(() => {
  const suggestions = []
  const min = minValue.value

  // Add suggestions based on property name and minimum value
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (propertyName.includes('age')) {
    suggestions.push(
      { value: min, label: `${min} (minimum)` },
      { value: Math.max(min, 18), label: '18 (adult age)' },
      { value: Math.max(min, 25), label: '25' },
      { value: Math.max(min, 30), label: '30' }
    )
  } else if (propertyName.includes('price') || propertyName.includes('cost')) {
    suggestions.push(
      { value: min, label: `$${min} (minimum)` },
      { value: min * 1.5, label: `$${min * 1.5}` },
      { value: min * 2, label: `$${min * 2}` }
    )
  } else {
    suggestions.push(
      { value: min, label: `${min} (minimum)` },
      { value: min * 2, label: `${min * 2}` },
      { value: min * 5, label: `${min * 5}` }
    )
  }

  return suggestions.slice(0, 4)
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

const getValuePosition = () => {
  const range = getSliderMax() - minValue.value
  if (range === 0) return 0
  return Math.min(100, Math.max(0, ((currentValue.value - minValue.value) / range) * 100))
}

const getCurrentValuePosition = () => {
  const min = minValue.value
  const current = currentValue.value

  if (hasBothConstraints.value) {
    // Bounded range: position between min and max values
    const max = getMaxValue()
    const range = max - min
    if (range === 0) return 50 // Both min and max are the same

    const position = 5 + ((current - min) / range) * 90 // Scale to 5-95%
    return Math.max(5, Math.min(95, position))
  } else {
    // Unbounded range: from minValue to +infinity
    if (current < min) {
      // Current value is below min - position it before the min marker
      return Math.max(2, 5 - ((min - current) / Math.max(1, min)) * 3)
    } else {
      // Current value is within acceptable range - position it proportionally
      // We'll use a scale where minValue is at 5% and it extends towards 90%
      const offset = current - min
      return Math.min(90, 5 + (offset / Math.max(1, min)) * 10)
    }
  }
}

const getMinValuePosition = () => {
  if (hasBothConstraints.value) {
    // In bounded range, min is at 5%
    return 5
  } else {
    // In unbounded range, min is at 5%
    return 5
  }
}

const getMaxValue = () => {
  if (props.context?.maxValue !== undefined) return props.context.maxValue
  if (props.context?.maximum !== undefined) return props.context.maximum
  if (constraintRange.value) return constraintRange.value.max
  return minValue.value * 3 // Default fallback
}

const getRangeStartLabel = () => {
  return `${minValue.value} (min)`
}

const getRangeEndLabel = () => {
  if (hasBothConstraints.value) {
    return `${getMaxValue()} (max)`
  }
  return '+∞'
}

const getMinPosition = () => {
  const range = getSliderMax() - minValue.value
  if (range === 0) return 0
  return ((minValue.value - minValue.value) / range) * 100
}

const getSliderMax = () => {
  // Use constraint maximum if available
  if (constraintRange.value) {
    return constraintRange.value.max
  }

  const min = minValue.value
  // Set reasonable max based on minimum value
  if (min <= 0) return 100
  if (min <= 10) return 50
  if (min <= 100) return 200
  return min * 3
}

const getStepSize = () => {
  const min = minValue.value
  // Use appropriate step size based on value range
  if (min < 1) return 0.1
  if (min < 10) return 1
  if (min < 100) return 5
  return 10
}

const getUnit = () => {
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (propertyName.includes('age')) return 'years'
  if (propertyName.includes('price') || propertyName.includes('cost')) return '$'
  if (propertyName.includes('length')) return 'm'
  if (propertyName.includes('weight')) return 'kg'
  if (propertyName.includes('temperature')) return '°C'

  return ''
}

const validateValue = () => {
  // Validation is handled by computed property
}

const setToMinimum = () => {
  correctedValue.value = minValue.value
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  if (!canApplyFix.value) return

  try {
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'

    // Determine datatype based on context or property name
    const propertyName = props.resultPath?.toLowerCase() || ''
    let formattedValue

    if (propertyName.includes('age') || propertyName.includes('count') || propertyName.includes('number')) {
      formattedValue = `"${correctedValue.value}"^^xsd:integer`
    } else if (propertyName.includes('price') || propertyName.includes('cost')) {
      formattedValue = `"${correctedValue.value}"^^xsd:decimal`
    } else {
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
      fixType: 'mininclusive_correction'
    })
  } catch (error) {
    console.error('Error applying minInclusive constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Initialize corrected value
correctedValue.value = Math.max(minValue.value, currentValue.value)
</script>

<style scoped>
.mininclusive-constraint-content {
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

.slider-input {
  @apply space-y-3;
}

.slider-container {
  @apply space-y-2;
}

.value-slider {
  @apply w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer;
}

.value-slider::-webkit-slider-thumb {
  @apply appearance-none w-4 h-4 bg-blue-500 rounded-full cursor-pointer;
}

.slider-labels {
  @apply flex justify-between text-xs text-gray-600;
}

.slider-output {
  @apply flex items-center gap-3;
}

.value-input {
  @apply w-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.input-unit {
  @apply text-sm text-gray-600 font-medium;
}

.quick-fixes {
  @apply flex items-center gap-2 flex-wrap;
}

.quick-label {
  @apply text-sm text-gray-600;
}

.quick-btn {
  @apply px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm font-medium transition-colors;
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

.advanced-mininclusive-info {
  @apply space-y-4;
}

.mininclusive-info-grid {
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

.range-indicator {
  @apply my-4 p-3 bg-gray-50 rounded-lg border border-gray-200;
}

.range-bar {
  @apply relative h-2 mb-2;
}

.range-line {
  @apply absolute top-1/2 left-0 right-0 h-0.5 bg-gray-300 -translate-y-1/2;
}

.range-mark {
  @apply absolute w-3 h-3 bg-white border-2 rounded-full -translate-y-1/2 -translate-x-1/2 top-1/2;
}

.range-mark.current-value {
  @apply border-red-500 bg-red-500;
}

.range-mark.max-value {
  @apply border-green-500 bg-green-500;
}

.range-mark.min-value {
  @apply border-green-500 bg-green-500;
}

.range-labels {
  @apply flex justify-between text-xs text-gray-600 relative;
}

.range-label {
  @apply text-center;
}

.range-label.start {
  @apply absolute left-0;
}

.range-label.current {
  @apply absolute left-1/2 -translate-x-1/2 text-red-600 font-medium;
}

.range-label.end {
  @apply absolute right-0;
}
</style>