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
      <div class="pattern-constraint-content">
        <div class="alert alert-warning">
          <h4 class="alert-title">Pattern mismatch</h4>
          <p class="alert-message">
            Value "{{ value }}" does not match the required pattern
          </p>
        </div>

        <div class="pattern-info">
          <p class="pattern-text"><strong>Pattern:</strong> {{ pattern }}</p>
          <p v-if="example" class="pattern-example"><strong>Example:</strong> {{ example }}</p>
        </div>

        <div class="input-section">
          <label class="input-label">Enter corrected value:</label>
          <input
            v-model="correctedValue"
            type="text"
            class="text-input"
            :placeholder="example || `Value matching pattern: ${pattern}`"
            @input="validatePattern"
          />
          <div class="validation-status" :class="{ 'valid': isValid }">
            {{ isValid ? '✓ Pattern matches' : '✗ Pattern does not match' }}
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
const pattern = computed(() => props.context?.pattern || '.*')
const example = computed(() => props.context?.example || '')
const isValid = ref(false)

const canApplyFix = computed(() => isValid.value)

const validatePattern = () => {
  try {
    const regex = new RegExp(pattern.value)
    isValid.value = regex.test(correctedValue.value)
  } catch (e) {
    isValid.value = false
  }
}

const handleRejectFix = () => emit('reject-fix')
const handleApplyFix = () => {
  if (canApplyFix.value) {
    emit('apply-fix', {
      newValue: correctedValue.value,
      fixType: 'pattern_correction'
    })
  }
}

// Initialize with current value
correctedValue.value = props.value || ''
validatePattern()
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
.pattern-info {
  @apply bg-gray-50 p-3 rounded mb-4;
}
.pattern-text, .pattern-example {
  @apply text-sm text-gray-700;
}
.input-section {
  @apply space-y-3;
}
.input-label {
  @apply block text-sm font-medium text-gray-700;
}
.text-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
}
.validation-status {
  @apply text-sm font-medium;
}
.validation-status.valid {
  @apply text-green-600;
}
.validation-status:not(.valid) {
  @apply text-red-600;
}
</style>