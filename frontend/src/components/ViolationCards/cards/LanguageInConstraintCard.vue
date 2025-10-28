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
      <div class="languagein-constraint-content">
        <div class="alert alert-warning">
          <h4 class="alert-title">Language not allowed</h4>
          <p class="alert-message">
            Language tag "@{{ currentLanguage }}" is not in the list of allowed languages
          </p>
        </div>

        <div class="language-options">
          <label class="input-label">Allowed Languages:</label>
          <div class="language-list">
            <button
              v-for="lang in allowedLanguages"
              :key="lang.code"
              @click="selectedLanguage = lang.code"
              :class="{ 'selected': selectedLanguage === lang.code }"
              class="language-btn"
            >
              {{ lang.name }} ({{ lang.code }})
            </button>
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

const selectedLanguage = ref('')
const currentLanguage = computed(() => {
  const match = props.value?.match(/@([a-z-]+)/)
  return match ? match[1] : 'unknown'
})
const allowedLanguages = computed(() => props.context?.allowedLanguages || [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' }
])
const canApplyFix = computed(() => selectedLanguage.value !== '')

const handleRejectFix = () => emit('reject-fix')
const handleApplyFix = () => {
  if (canApplyFix.value) {
    emit('apply-fix', {
      newValue: selectedLanguage.value,
      fixType: 'language_correction'
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
.language-options {
  @apply space-y-3;
}
.input-label {
  @apply block text-sm font-medium text-gray-700;
}
.language-list {
  @apply flex flex-wrap gap-2;
}
.language-btn {
  @apply px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm;
}
.language-btn.selected {
  @apply bg-blue-100 border-blue-300 text-blue-700;
}
</style>