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
      <div class="generic-constraint-content">
        <div class="alert alert-info">
          <h4 class="alert-title">{{ getConstraintTitle() }} Violation</h4>
          <p class="alert-message">{{ message }}</p>
        </div>

        <div class="fix-section">
          <label class="input-label">Enter corrected value:</label>
          <input
            v-model="correctedValue"
            type="text"
            class="text-input"
            :placeholder="getInputPlaceholder()"
          />

          <div class="advanced-info">
            <h5>Constraint Details:</h5>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Constraint:</span>
                <code class="detail-value">{{ constraintComponent }}</code>
              </div>
              <div class="detail-item">
                <span class="detail-label">Property:</span>
                <code class="detail-value">{{ resultPath }}</code>
              </div>
              <div class="detail-item">
                <span class="detail-label">Current Value:</span>
                <code class="detail-value">{{ value }}</code>
              </div>
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

const props = defineProps({
  focusNode: String,
  resultPath: String,
  value: String,
  message: String,
  constraintComponent: String,
  context: Object,
  isLoading: Boolean,
  hasError: Boolean,
  errorMessage: String
})

const emit = defineEmits(['reject-fix', 'apply-fix'])

const correctedValue = ref('')

const canApplyFix = computed(() => correctedValue.value.trim() !== '')

const getConstraintTitle = () => {
  if (!props.constraintComponent) return 'Unknown Constraint'

  const name = props.constraintComponent.split('#').pop() || props.constraintComponent
  return name.replace(/ConstraintComponent$/, '')
}

const getInputPlaceholder = () => {
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (propertyName.includes('name')) return 'e.g., John Doe'
  if (propertyName.includes('email')) return 'e.g., user@example.com'
  if (propertyName.includes('date')) return 'e.g., 2024-01-01'
  if (propertyName.includes('age')) return 'e.g., 25'

  return 'Enter corrected value...'
}

const handleRejectFix = () => emit('reject-fix')
const handleApplyFix = () => {
  if (canApplyFix.value) {
    emit('apply-fix', {
      newValue: correctedValue.value,
      fixType: 'generic_correction'
    })
  }
}
</script>

<style scoped>
.alert {
  @apply p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg;
}
.alert-title {
  @apply text-sm font-semibold text-blue-800;
}
.alert-message {
  @apply text-sm text-blue-700 mt-1;
}
.fix-section {
  @apply space-y-4;
}
.input-label {
  @apply block text-sm font-medium text-gray-700;
}
.text-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
}
.advanced-info {
  @apply bg-gray-50 p-3 rounded-lg space-y-3;
}
.advanced-info h5 {
  @apply text-sm font-medium text-gray-700;
}
.detail-grid {
  @apply grid grid-cols-1 gap-2;
}
.detail-item {
  @apply flex items-center gap-2;
}
.detail-label {
  @apply text-xs font-medium text-gray-500 min-w-20;
}
.detail-value {
  @apply text-xs font-mono text-gray-700 bg-gray-100 px-2 py-1 rounded;
}
</style>