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
      <div class="maxinclusive-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-error">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Value too large</h4>
              <p class="alert-message">
                Value <code>{{ currentValue }}</code> exceeds the maximum of <code>{{ maxValue }}</code>
              </p>
            </div>
          </div>
        </div>

        <!-- Visual Range Indicator -->
        <div class="range-indicator">
          <div class="range-bar">
            <div class="range-line"></div>
            <div class="range-mark current-value" :style="{ left: getCurrentValuePosition() + '%' }"></div>
            <div class="range-mark max-value" :style="{ left: getMaxValuePosition() + '%' }"></div>
            <div v-if="hasBothConstraints" class="range-mark min-value" :style="{ left: '5%' }"></div>
          </div>
          <div class="range-labels">
            <span class="range-label start">{{ getRangeStartLabel() }}</span>
            <span class="range-label current">Current: {{ currentValue }}</span>
            <span class="range-label end">{{ getRangeEndLabel() }}</span>
          </div>
        </div>

        <!-- Fix Section -->
        <div class="fix-section">
          <h4 class="fix-title">Enter valid value (≤ {{ maxValue }}):</h4>

          <!-- Slider Input -->
          <div class="slider-input">
            <div class="slider-container">
              <input
                v-model.number="correctedValue"
                type="range"
                :min="getSliderMin()"
                :max="maxValue"
                step="getStepSize()"
                class="value-slider"
                @input="validateValue"
              />
              <div class="slider-labels">
                <span>{{ getSliderMin() }}</span>
                <span>{{ maxValue }}</span>
              </div>
            </div>
            <div class="slider-output">
              <input
                v-model.number="correctedValue"
                type="number"
                :max="maxValue"
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
              @click="setToMaximum"
              type="button"
              class="quick-btn"
            >
              Set to {{ maxValue }} (maximum)
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
      <div class="advanced-maxinclusive-info">
        <h4>Maximum Value Constraint Details</h4>
        <div class="maxinclusive-info-grid">
          <div class="info-item">
            <span class="info-label">Maximum Value:</span>
            <code class="info-value">{{ maxValue }}</code>
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
            <code class="info-value">Yes (≤)</code>
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

const maxValue = computed(() => {
  // First try to get from context
  if (props.context?.maxValue) return props.context.maxValue
  if (props.context?.maximum) return props.context.maximum

  // Use extracted range if available
  if (constraintRange.value) {
    return constraintRange.value.max
  }

  // Extract from other common patterns
  if (props.message) {
    const maxMatch = props.message.match(/maximum(?:\s+of)?\s+(\d+)/i)
    if (maxMatch) {
      return Number(maxMatch[1])
    }

    // Extract from "must be ≤ X" pattern
    const lessThanMatch = props.message.match(/must be\s+≤?\s*(\d+)/i)
    if (lessThanMatch) {
      return Number(lessThanMatch[1])
    }
  }

  // Default fallback
  return 100
})

const currentValue = computed(() => {
  return Number(props.value) || 0
})

const validationStatus = computed(() => {
  if (correctedValue.value <= maxValue.value) {
    return { icon: 'check', text: `Valid (≤ ${maxValue.value})`, class: 'status-valid' }
  } else {
    return { icon: 'x', text: `Too large (must be ≤ ${maxValue.value})`, class: 'status-error' }
  }
})

const canApplyFix = computed(() => {
  return correctedValue.value <= maxValue.value
})

const hasBothConstraints = computed(() => {
  // Check if there's also a MinInclusive constraint on the same property
  return props.context?.minValue !== undefined ||
         props.context?.minimum !== undefined ||
         constraintRange.value !== null
})

const quickSuggestions = computed(() => {
  const suggestions = []
  const max = maxValue.value

  // Add suggestions based on property name and maximum value
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (propertyName.includes('age')) {
    suggestions.push(
      { value: max, label: `${max} (maximum)` },
      { value: Math.min(max, 65), label: '65 (retirement age)' },
      { value: Math.min(max, 30), label: '30' },
      { value: Math.min(max, 25), label: '25' }
    )
  } else if (propertyName.includes('price') || propertyName.includes('cost')) {
    suggestions.push(
      { value: max, label: `$${max} (maximum)` },
      { value: max * 0.8, label: `$${max * 0.8}` },
      { value: max * 0.5, label: `$${max * 0.5}` }
    )
  } else {
    suggestions.push(
      { value: max, label: `${max} (maximum)` },
      { value: max * 0.9, label: `${max * 0.9}` },
      { value: max * 0.5, label: `${max * 0.5}` }
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
  const range = maxValue.value - getSliderMin()
  if (range === 0) return 0
  return Math.min(100, Math.max(0, ((currentValue.value - getSliderMin()) / range) * 100))
}

const getCurrentValuePosition = () => {
  const max = maxValue.value
  const current = currentValue.value

  if (hasBothConstraints.value) {
    // Bounded range: position between min and max values
    const min = getMinValue()
    const range = max - min
    if (range === 0) return 50 // Both min and max are the same

    const position = 5 + ((current - min) / range) * 90 // Scale to 5-95%
    return Math.max(5, Math.min(95, position))
  } else {
    // Unbounded range: from -infinity to maxValue
    if (current > max) {
      // Current value exceeds max - position it beyond the max marker
      return Math.min(98, 95 + ((current - max) / max) * 3)
    } else {
      // Current value is within acceptable range - position it proportionally
      // We'll use a scale where 0 is at 10% and maxValue is at 95%
      if (current <= 0) return 10
      return Math.min(95, 10 + (current / max) * 85)
    }
  }
}

const getMaxValuePosition = () => {
  if (hasBothConstraints.value) {
    // In bounded range, max is at 95%
    return 95
  } else {
    // In unbounded range, max is at 95%
    return 95
  }
}

const getMinValue = () => {
  if (props.context?.minValue !== undefined) return props.context.minValue
  if (props.context?.minimum !== undefined) return props.context.minimum
  if (constraintRange.value) return constraintRange.value.min
  return 0
}

const getRangeStartLabel = () => {
  if (hasBothConstraints.value) {
    return `${getMinValue()} (min)`
  }
  return '-∞'
}

const getRangeEndLabel = () => {
  return `${maxValue.value} (max)`
}

const getMaxPosition = () => {
  const range = maxValue.value - getSliderMin()
  if (range === 0) return 0
  return ((maxValue.value - getSliderMin()) / range) * 100
}

const getSliderMin = () => {
  // Use constraint minimum if available
  if (constraintRange.value) {
    return constraintRange.value.min
  }

  const max = maxValue.value
  // Set reasonable min based on maximum value
  if (max <= 0) return -100
  if (max <= 10) return 0
  if (max <= 100) return 0
  return 0
}

const getStepSize = () => {
  const max = maxValue.value
  // Use appropriate step size based on value range
  if (max < 1) return 0.1
  if (max < 10) return 1
  if (max < 100) return 5
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

const setToMaximum = () => {
  correctedValue.value = maxValue.value
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
      fixType: 'maxinclusive_correction'
    })
  } catch (error) {
    console.error('Error applying maxInclusive constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Initialize corrected value
correctedValue.value = Math.min(maxValue.value, currentValue.value)
</script>

<style scoped>
.maxinclusive-constraint-content {
  @apply space-y-4;
}

.violation-details {
  @apply space-y-3;
}

.alert {
  @apply flex items-start gap-3 p-4 rounded-lg border;
}

.alert-error {
  @apply bg-red-50 border-red-200;
}

.alert-title {
  @apply text-sm font-semibold text-red-800;
}

.alert-message {
  @apply text-sm text-red-700 mt-1;
}

.alert-message code {
  @apply bg-red-100 px-1 py-0.5 rounded text-xs font-mono;
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

.advanced-maxinclusive-info {
  @apply space-y-4;
}

.maxinclusive-info-grid {
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