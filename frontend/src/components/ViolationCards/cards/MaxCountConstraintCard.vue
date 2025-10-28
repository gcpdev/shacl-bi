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
    :errorMessage="errorMessage"
    :can-apply-fix="canApplyFix"
    @reject-fix="handleRejectFix"
    @apply-fix="handleApplyFix"
  >
    <template #constraint-content>
      <div class="maxcount-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-error">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Too many values</h4>
              <p class="alert-message">
                Property <code>{{ formatPropertyName(resultPath) }}</code> has
                <span class="count-badge current">{{ currentCount }}</span> values but allows at most
                <span class="count-badge max">{{ maxCount }}</span>
              </p>
            </div>
          </div>

          <!-- Excess indicator -->
          <div class="excess-indicator">
            <div class="excess-text">
              Remove <span class="excess-number">{{ excessCount }}</span> value{{ excessCount === 1 ? '' : 's' }}
            </div>
            <div class="excess-progress">
              <div class="progress-bar">
                <div
                  class="progress-fill excess"
                  :style="{ width: `${excessPercentage}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Remove Excess Values Section -->
        <div class="remove-values-section">
          <h4 class="section-title">
            ❌ Remove excess values (remove {{ excessCount }}):
          </h4>

          <!-- MaxCount = 1: Radio button selection -->
          <div v-if="maxCount === 1" class="single-selection">
            <p class="selection-hint">Select the value to keep (remove others):</p>
            <div class="value-options">
              <label
                v-for="(value, index) in currentValues"
                :key="index"
                class="value-option"
                :class="{ 'selected': selectedValue === value }"
              >
                <input
                  v-model="selectedValue"
                  :value="value"
                  type="radio"
                  name="keep-value"
                  class="value-radio"
                />
                <div class="option-content">
                  <div class="option-main">
                    <span class="option-number">{{ index + 1 }}</span>
                    <code class="option-value">{{ formatValue(value) }}</code>
                    <span v-if="getValueType(value)" class="option-type">{{ getValueType(value) }}</span>
                  </div>
                  <div class="option-actions">
                    <button
                      type="button"
                      @click="previewValue(value)"
                      class="preview-btn"
                      title="Preview this value"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- MaxCount > 1: Checkbox selection -->
          <div v-else class="multi-selection">
            <p class="selection-hint">
              Select up to {{ maxCount }} values to keep ({{ selectedValues.length }}/{{ maxCount }} selected):
            </p>
            <div class="value-options">
              <label
                v-for="(value, index) in currentValues"
                :key="index"
                class="value-option"
                :class="{
                  'selected': selectedValues.includes(value),
                  'disabled': !selectedValues.includes(value) && selectedValues.length >= maxCount
                }"
              >
                <input
                  v-model="selectedValues"
                  :value="value"
                  type="checkbox"
                  class="value-checkbox"
                  :disabled="!selectedValues.includes(value) && selectedValues.length >= maxCount"
                />
                <div class="option-content">
                  <div class="option-main">
                    <span class="option-number">{{ index + 1 }}</span>
                    <code class="option-value">{{ formatValue(value) }}</code>
                    <span v-if="getValueType(value)" class="option-type">{{ getValueType(value) }}</span>
                  </div>
                  <div class="option-actions">
                    <button
                      type="button"
                      @click="previewValue(value)"
                      class="preview-btn"
                      title="Preview this value"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </label>
            </div>

            <!-- Selection counter -->
            <div class="selection-counter">
              <span class="counter-text">
                {{ selectedValues.length }} of {{ maxCount }} selected
                <span v-if="selectedValues.length > maxCount" class="counter-error">
                  (remove {{ selectedValues.length - maxCount }} more)
                </span>
                <span v-else-if="selectedValues.length < maxCount" class="counter-hint">
                  (can select {{ maxCount - selectedValues.length }} more)
                </span>
              </span>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="quick-actions">
            <h5 class="quick-title">Quick actions:</h5>
            <div class="action-buttons">
              <button
                v-if="maxCount === 1"
                @click="selectFirstValue"
                type="button"
                class="quick-btn"
              >
                Keep First Value
              </button>
              <button
                v-if="maxCount === 1"
                @click="selectLastValue"
                type="button"
                class="quick-btn"
              >
                Keep Last Value
              </button>
              <button
                @click="clearSelection"
                type="button"
                class="quick-btn secondary"
              >
                Clear Selection
              </button>
            </div>
          </div>

          <!-- Preview Section -->
          <div v-if="previewingValue" class="preview-section">
            <h5 class="preview-title">Value Preview:</h5>
            <div class="preview-content">
              <div class="preview-value">
                <code>{{ formatValue(previewingValue) }}</code>
              </div>
              <div v-if="getValueDetails(previewingValue)" class="preview-details">
                <div v-for="(detail, key) in getValueDetails(previewingValue)" :key="key" class="detail-item">
                  <span class="detail-label">{{ key }}:</span>
                  <span class="detail-value">{{ detail }}</span>
                </div>
              </div>
            </div>
            <button
              @click="previewingValue = null"
              type="button"
              class="close-preview"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </template>

    <template #advanced-content>
      <div class="advanced-maxcount-info">
        <h4>Maximum Count Constraint Details</h4>
        <div class="maxcount-info-grid">
          <div class="info-item">
            <span class="info-label">Maximum Count:</span>
            <code class="info-value">{{ maxCount }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Count:</span>
            <code class="info-value">{{ currentCount }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Excess Count:</span>
            <code class="info-value">{{ excessCount }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Property:</span>
            <code class="info-value">{{ formatPropertyName(resultPath) }}</code>
          </div>
        </div>

        <!-- Values to be removed -->
        <div class="values-to-remove">
          <h5>Values that will be removed:</h5>
          <div class="remove-list">
            <div
              v-for="value in valuesToRemove"
              :key="value"
              class="remove-item"
            >
              <code class="remove-value">{{ formatValue(value) }}</code>
              <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </div>
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
const selectedValue = ref('')
const selectedValues = ref([])
const previewingValue = ref(null)

// Computed properties
const maxCount = computed(() => {
  return props.context?.maxCount || props.context?.maxAllowed || 1
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

const excessCount = computed(() => {
  return Math.max(0, currentCount.value - maxCount.value)
})

const excessPercentage = computed(() => {
  if (currentCount.value === 0) return 0
  return Math.round((excessCount.value / currentCount.value) * 100)
})

const valuesToRemove = computed(() => {
  if (maxCount.value === 1) {
    return currentValues.value.filter(v => v !== selectedValue.value)
  } else {
    return currentValues.value.filter(v => !selectedValues.value.includes(v))
  }
})

const canApplyFix = computed(() => {
  if (excessCount.value === 0) return true // No fix needed

  if (maxCount.value === 1) {
    return selectedValue.value !== ''
  } else {
    return selectedValues.value.length <= maxCount.value && selectedValues.value.length > 0
  }
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
    if (value.startsWith('"')) {
      return value
    }
    return `"${value}"`
  }
  return String(value)
}

const getValueType = (value) => {
  if (!value) return ''

  const str = String(value)

  if (str.includes('^^')) {
    return str.split('^^')[1]
  }

  if (str.startsWith('<') && str.endsWith('>')) {
    return 'IRI'
  }

  if (str.startsWith('_:')) {
    return 'BlankNode'
  }

  if (str.includes('"') && str.includes('http')) {
    return 'IRI (as string)'
  }

  if (!isNaN(str) && !str.includes('.')) {
    return 'Integer'
  }

  if (!isNaN(str) && str.includes('.')) {
    return 'Decimal'
  }

  if (str.toLowerCase() === 'true' || str.toLowerCase() === 'false') {
    return 'Boolean'
  }

  if (str.match(/^\d{4}-\d{2}-\d{2}/)) {
    return 'Date'
  }

  return 'String'
}

const getValueDetails = (value) => {
  // Return additional details about the value if available
  const details = {}

  const type = getValueType(value)
  if (type) {
    details['Type'] = type
  }

  // Add more details based on context if available
  if (props.context?.valueDetails?.[value]) {
    Object.assign(details, props.context.valueDetails[value])
  }

  return Object.keys(details).length > 0 ? details : null
}

const selectFirstValue = () => {
  if (currentValues.value.length > 0) {
    selectedValue.value = currentValues.value[0]
  }
}

const selectLastValue = () => {
  if (currentValues.value.length > 0) {
    selectedValue.value = currentValues.value[currentValues.value.length - 1]
  }
}

const clearSelection = () => {
  if (maxCount.value === 1) {
    selectedValue.value = ''
  } else {
    selectedValues.value = []
  }
}

const previewValue = (value) => {
  previewingValue.value = value
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  if (!canApplyFix.value || excessCount.value === 0) return

  try {
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'

    // Prepare DELETE statements for excess values
    const deleteClauses = valuesToRemove.value.map(value =>
      `    <${props.focusNode}> <${props.resultPath}> ${formatValue(value)} .`
    ).join('\n')

    const sparqlQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
${deleteClauses}
  }
}`

    await api.post('/api/repair', {
      repair_query: sparqlQuery,
      session_id: sessionId
    })

    emit('apply-fix', {
      valuesToRemove: valuesToRemove.value,
      valuesToKeep: maxCount.value === 1 ? [selectedValue.value] : selectedValues.value,
      sparqlQuery: sparqlQuery,
      fixType: 'remove_excess_values',
      removedCount: valuesToRemove.value.length
    })
  } catch (error) {
    console.error('Error applying maxCount constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Initialize with default selection
if (maxCount.value === 1 && currentValues.value.length > 0 && !selectedValue.value) {
  selectedValue.value = currentValues.value[0]
} else if (maxCount.value > 1 && selectedValues.value.length === 0) {
  // Select first maxCount values by default
  selectedValues.value = currentValues.value.slice(0, maxCount.value)
}
</script>

<style scoped>
.maxcount-constraint-content {
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

.count-badge {
  @apply px-2 py-1 rounded text-xs font-medium;
}

.count-badge.current {
  @apply bg-red-100 text-red-800;
}

.count-badge.max {
  @apply bg-blue-100 text-blue-800;
}

.excess-indicator {
  @apply bg-red-50 p-3 rounded-lg border border-red-200 space-y-2;
}

.excess-text {
  @apply text-sm font-medium text-red-700;
}

.excess-number {
  @apply font-bold text-red-800;
}

.excess-progress {
  @apply w-full;
}

.progress-bar {
  @apply w-full bg-gray-200 rounded-full h-2;
}

.progress-fill.excess {
  @apply bg-red-500 h-2 rounded-full transition-all duration-300;
}

.remove-values-section {
  @apply space-y-4;
}

.section-title {
  @apply text-sm font-semibold text-gray-700;
}

.single-selection,
.multi-selection {
  @apply space-y-3;
}

.selection-hint {
  @apply text-sm text-gray-600 mb-3;
}

.value-options {
  @apply space-y-2;
}

.value-option {
  @apply flex items-start gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors;
}

.value-option.selected {
  @apply bg-blue-50 border-blue-200;
}

.value-option.disabled {
  @apply opacity-50 cursor-not-allowed;
}

.value-radio,
.value-checkbox {
  @apply h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 mt-1;
}

.option-content {
  @apply flex-1 flex items-center justify-between gap-3;
}

.option-main {
  @apply flex items-center gap-3 flex-1;
}

.option-number {
  @apply flex-shrink-0 w-6 h-6 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center text-xs font-medium;
}

.option-value {
  @apply text-sm font-mono text-gray-800 bg-gray-50 px-2 py-1 rounded;
}

.option-type {
  @apply text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded;
}

.option-actions {
  @apply flex items-center gap-2;
}

.preview-btn {
  @apply p-1 text-gray-400 hover:text-gray-600 transition-colors;
}

.selection-counter {
  @apply bg-gray-50 p-3 rounded-lg border border-gray-200;
}

.counter-text {
  @apply text-sm text-gray-700;
}

.counter-error {
  @apply text-red-600 font-medium;
}

.counter-hint {
  @apply text-gray-500;
}

.quick-actions {
  @apply space-y-2;
}

.quick-title {
  @apply text-sm font-medium text-gray-700;
}

.action-buttons {
  @apply flex flex-wrap gap-2;
}

.quick-btn {
  @apply px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm font-medium transition-colors;
}

.quick-btn.secondary {
  @apply bg-gray-100 text-gray-700 hover:bg-gray-200;
}

.preview-section {
  @apply relative bg-blue-50 p-4 rounded-lg border border-blue-200 space-y-3;
}

.preview-title {
  @apply text-sm font-medium text-blue-800;
}

.preview-content {
  @apply space-y-2;
}

.preview-value code {
  @apply text-sm font-mono text-blue-800 bg-blue-100 px-2 py-1 rounded;
}

.preview-details {
  @apply space-y-1;
}

.detail-item {
  @apply flex gap-2 text-sm;
}

.detail-label {
  @apply font-medium text-gray-600 min-w-20;
}

.detail-value {
  @apply text-gray-800;
}

.close-preview {
  @apply absolute top-2 right-2 p-1 text-gray-500 hover:text-gray-700 transition-colors;
}

.advanced-maxcount-info {
  @apply space-y-4;
}

.maxcount-info-grid {
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

.values-to-remove {
  @apply space-y-2;
}

.values-to-remove h5 {
  @apply text-sm font-medium text-gray-700;
}

.remove-list {
  @apply space-y-1;
}

.remove-item {
  @apply flex items-center gap-2 p-2 bg-red-50 rounded border border-red-200;
}

.remove-value {
  @apply text-sm font-mono text-red-800;
}
</style>