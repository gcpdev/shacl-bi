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
      <div class="default-constraint-content">
        <!-- Constraint Details -->
        <div class="constraint-details">
          <h4 class="detail-title">Constraint Details</h4>
          <p class="detail-message">{{ message }}</p>

          <!-- Show constraint component if available -->
          <div v-if="constraintComponent" class="constraint-type">
            <span class="label">Constraint Type:</span>
            <code class="type">{{ formatConstraintType(constraintComponent) }}</code>
          </div>

          <!-- Show focus node if available -->
          <div v-if="focusNode" class="focus-node">
            <span class="label">Resource:</span>
            <code class="node">{{ formatNodeName(focusNode) }}</code>
          </div>
        </div>

        <!-- Simple Input Field -->
        <div class="fix-section">
          <h4 class="fix-title">Suggested Fix</h4>
          <div class="input-group">
            <label class="input-label">Enter corrected value:</label>
            <input
              v-model="correctedValue"
              type="text"
              :placeholder="getInputPlaceholder()"
              class="input-field"
              @input="validateInput"
            />
            <div v-if="inputError" class="input-error">
              {{ inputError }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #advanced-content>
      <div class="advanced-details">
        <!-- Raw context information -->
        <div v-if="context && Object.keys(context).length > 0" class="context-info">
          <h4>Context Information</h4>
          <pre class="context-json">{{ JSON.stringify(context, null, 2) }}</pre>
        </div>

        <!-- SPARQL Query -->
        <div v-if="context?.sparqlQuery || context?.proposed_repair?.query" class="sparql-info">
          <h4>SPARQL Query</h4>
          <pre class="sparql-query">{{ context?.sparqlQuery || context?.proposed_repair?.query }}</pre>
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
const correctedValue = ref('')
const inputError = ref('')
const isApplyingFix = ref(false)

// Computed properties
const canApplyFix = computed(() => {
  return correctedValue.value.trim() && !inputError.value && !isApplyingFix.value
})

// Methods
const formatConstraintType = (uri) => {
  if (!uri) return 'Unknown'
  if (uri.includes('#')) {
    return uri.split('#').pop()
  }
  return uri
}

const formatNodeName = (uri) => {
  if (!uri) return ''
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri
  }
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

const getInputPlaceholder = () => {
  const propertyLower = props.resultPath?.toLowerCase() || ''

  if (propertyLower.includes('name')) return 'e.g., John Doe'
  if (propertyLower.includes('email')) return 'e.g., user@example.com'
  if (propertyLower.includes('date')) return 'e.g., 2024-01-01'
  if (propertyLower.includes('age') || propertyLower.includes('count')) return 'e.g., 25'
  if (propertyLower.includes('url')) return 'e.g., https://example.com'
  if (propertyLower.includes('phone')) return 'e.g., +1-555-123-4567'

  return 'Enter corrected value...'
}

const validateInput = () => {
  inputError.value = ''

  // Basic validation - can be extended based on constraint type
  if (!correctedValue.value.trim()) {
    inputError.value = 'Value cannot be empty'
    return
  }

  // Add constraint-specific validation if context provides hints
  if (props.context?.minLength && correctedValue.value.length < props.context.minLength) {
    inputError.value = `Value must be at least ${props.context.minLength} characters long`
    return
  }

  if (props.context?.maxLength && correctedValue.value.length > props.context.maxLength) {
    inputError.value = `Value must be no more than ${props.context.maxLength} characters long`
    return
  }

  if (props.context?.pattern) {
    try {
      const regex = new RegExp(props.context.pattern)
      if (!regex.test(correctedValue.value)) {
        inputError.value = `Value must match pattern: ${props.context.pattern}`
        return
      }
    } catch (e) {
      // Invalid regex pattern, ignore validation
    }
  }
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  if (!canApplyFix.value) return

  isApplyingFix.value = true

  try {
    // Generate a basic SPARQL query for the fix
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'

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
    <${props.focusNode}> <${props.resultPath}> "${correctedValue.value}" .
  }
}`
    } else {
      // Add new value
      sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> "${correctedValue.value}" .
  }
}`
    }

    // Apply the fix via API
    await api.post('/api/repair', {
      repair_query: sparqlQuery,
      session_id: sessionId
    })

    emit('apply-fix', {
      newValue: correctedValue.value,
      sparqlQuery: sparqlQuery
    })

  } catch (error) {
    console.error('Error applying fix:', error)
    emit('reject-fix', { error: error.message })
  } finally {
    isApplyingFix.value = false
  }
}

// Initialize corrected value with current value for editing
if (props.value) {
  correctedValue.value = String(props.value).replace(/^"|"$/g, '') // Remove quotes if present
}
</script>

<style scoped>
.default-constraint-content {
  @apply space-y-4;
}

.constraint-details {
  @apply space-y-3;
}

.detail-title {
  @apply text-sm font-semibold text-gray-700;
}

.detail-message {
  @apply text-sm text-gray-600;
}

.constraint-type,
.focus-node {
  @apply flex items-center gap-2;
}

.label {
  @apply text-sm font-medium text-gray-500 min-w-24;
}

.type,
.node {
  @apply text-xs font-mono text-gray-700 bg-gray-50 px-2 py-1 rounded border border-gray-200;
}

.fix-section {
  @apply space-y-3;
}

.fix-title {
  @apply text-sm font-semibold text-gray-700;
}

.input-group {
  @apply space-y-2;
}

.input-label {
  @apply block text-sm font-medium text-gray-700;
}

.input-field {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.input-error {
  @apply text-sm text-red-600;
}

.advanced-details {
  @apply space-y-4;
}

.context-info h4,
.sparql-info h4 {
  @apply text-sm font-medium text-gray-700 mb-2;
}

.context-json,
.sparql-query {
  @apply text-xs font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto bg-gray-50 p-3 rounded border border-gray-200;
}
</style>