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
      <div class="maxlength-constraint-content">
        <div class="alert alert-error">
          <h4 class="alert-title">String too long</h4>
          <p class="alert-message">
            Current value "{{ value }}" ({{ currentLength }} characters) exceeds maximum of {{ maxLength }} characters
          </p>
        </div>

        <div class="input-section">
          <label class="input-label">Enter corrected value:</label>
          <textarea
            v-model="correctedValue"
            class="text-input"
            :placeholder="`Maximum ${maxLength} characters allowed`"
            @input="validateInput"
          ></textarea>
          <div class="length-indicator">
            <div class="length-bar">
              <div
                class="length-fill"
                :style="{ width: `${progressPercentage}%` }"
                :class="{ 'exceeded': currentLength > maxLength }"
              ></div>
            </div>
            <span class="length-text" :class="{ 'text-red-600': currentLength > maxLength }">
              {{ currentLength }}/{{ maxLength }} characters
            </span>
          </div>
          <p v-if="currentLength > maxLength" class="help-text error">
            ⚠️ {{ currentLength - maxLength }} character{{ (currentLength - maxLength) === 1 ? '' : 's' }} over limit
          </p>
          <button
            v-if="currentLength > maxLength"
            @click="autoTrim"
            type="button"
            class="trim-btn"
          >
            Auto-trim to {{ maxLength }} characters
          </button>
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
const maxLength = computed(() => props.context?.maxLength || 100)
const currentLength = computed(() => correctedValue.value?.length || 0)
const progressPercentage = computed(() => Math.min(100, (currentLength.value / maxLength.value) * 100))
const canApplyFix = computed(() => currentLength.value <= maxLength.value)

const validateInput = () => {
  // Validation handled by computed properties
}

const autoTrim = () => {
  correctedValue.value = correctedValue.value.substring(0, maxLength.value)
}

const handleRejectFix = () => emit('reject-fix')
const handleApplyFix = () => {
  if (canApplyFix.value) {
    emit('apply-fix', {
      newValue: correctedValue.value,
      fixType: 'maxlength_correction'
    })
  }
}

// Initialize with current value
correctedValue.value = props.value || ''
</script>

<style scoped>
.alert {
  @apply p-4 bg-red-50 border-l-4 border-red-400 rounded-lg;
}
.alert-title {
  @apply text-sm font-semibold text-red-800;
}
.alert-message {
  @apply text-sm text-red-700 mt-1;
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
.length-indicator {
  @apply flex items-center gap-3;
}
.length-bar {
  @apply flex-1 bg-gray-200 rounded-full h-2;
}
.length-fill {
  @apply h-2 bg-blue-500 rounded-full transition-all duration-300;
}
.length-fill.exceeded {
  @apply bg-red-500;
}
.length-text {
  @apply text-sm text-gray-600;
}
.help-text {
  @apply text-sm text-gray-600;
}
.help-text.error {
  @apply text-red-600;
}
.trim-btn {
  @apply px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm font-medium transition-colors;
}
</style>