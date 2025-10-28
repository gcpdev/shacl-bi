<template>
  <GenericConstraintCard
    :focus-node="focusNode"
    :result-path="resultPath"
    :value="value"
    :message="message"
    :constraint-component="constraintComponent"
    :context="context"
    :is-loading="isLoading"
    :has-error="hasError"
    :error-message="errorMessage"
    @reject-fix="$emit('reject-fix', $event)"
    @apply-fix="$emit('apply-fix', $event)"
  />
</template>

<script setup>
import GenericConstraintCard from './GenericConstraintCard.vue'

defineProps({
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

defineEmits(['reject-fix', 'apply-fix'])
</script>