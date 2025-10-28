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
      <div class="in-constraint-content">
        <div class="alert alert-warning">
          <h4 class="alert-title">Invalid Value</h4>
          <p class="alert-message">
            Value <code>"{{ value }}"</code> is not allowed. Please select a valid value from the list below.
          </p>
        </div>

        <div class="allowed-values">
          <label class="input-label">Select the correct value:</label>
          <div class="dropdown-container">
            <select v-model="selectedValue" class="value-select">
              <option value="">-- Select a valid value --</option>
              <option v-for="val in allowedValues" :key="val" :value="val">{{ val }}</option>
            </select>
            <div class="dropdown-icon">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 20 20">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </div>
          </div>
          <div v-if="allowedValues.length === 0" class="no-values-message">
            <p class="text-sm text-gray-500">No allowed values available in context</p>
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

const selectedValue = ref('')

// Get allowed values from backend-provided context
const allowedValues = computed(() => {
  // Backend provides allowedValues in the context for sh:In constraints
  if (props.context?.allowedValues && Array.isArray(props.context.allowedValues)) {
    return props.context.allowedValues
  }

  // Fallback: empty array if no allowed values provided
  return []
})

const canApplyFix = computed(() => selectedValue.value !== '')

const handleRejectFix = () => emit('reject-fix')
const handleApplyFix = () => {
  if (canApplyFix.value) {
    emit('apply-fix', {
      newValue: selectedValue.value,
      fixType: 'in_constraint_correction'
    })
  }
}
</script>

<style scoped>
.alert {
  @apply p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-lg;
}
.alert-title {
  @apply text-sm font-semibold text-yellow-800;
}
.alert-message {
  @apply text-sm text-yellow-700 mt-1;
}
.allowed-values {
  @apply space-y-2;
}
.input-label {
  @apply block text-sm font-medium text-gray-700;
}
.dropdown-container {
  @apply relative;
}

.value-select {
  @apply w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white;
}

.dropdown-icon {
  @apply absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none;
}

.dropdown-icon svg {
  @apply text-gray-400;
}

.no-values-message {
  @apply mt-2 p-3 bg-gray-50 rounded-md border border-gray-200;
}
</style>