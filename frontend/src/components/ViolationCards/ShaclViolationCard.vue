<template>
  <div class="shacl-violation-card">
    <!-- Card Header -->
    <div class="card-header">
      <div class="flex items-center gap-3">
        <!-- Constraint Icon -->
        <div class="constraint-icon">
          <component :is="getConstraintIcon()" class="w-6 h-6" />
        </div>

        <!-- Title -->
        <div class="flex-1">
          <h3 class="card-title">
            {{ getConstraintTitle() }}
          </h3>
          <p class="card-subtitle" v-if="getConstraintSubtitle()">
            {{ getConstraintSubtitle() }}
          </p>
        </div>

        <!-- Status Badge -->
        <div class="status-badge" :class="getStatusClass()">
          {{ getStatusText() }}
        </div>
      </div>
    </div>

    <!-- Card Content -->
    <div class="card-content">
      <!-- Context Information -->
      <div class="context-section">
        <div class="context-row">
          <span class="context-label">Property:</span>
          <span class="context-value">{{ formatPropertyName(resultPath) }}</span>
        </div>
        <div class="context-row">
          <span class="context-label">Current Value:</span>
          <span class="context-value">{{ formatValue(value) }}</span>
        </div>
      </div>

      <!-- Constraint-Specific Content -->
      <div class="constraint-section">
        <slot name="constraint-content">
          <!-- Default content if no specific slot provided -->
          <div class="default-content">
            <p>{{ message }}</p>
          </div>
        </slot>
      </div>

      <!-- Action Section -->
      <div class="action-section">
        <slot name="action-content">
          <!-- Default action buttons -->
          <div class="default-actions">
            <button
              @click="rejectFix"
              class="action-btn secondary"
              :disabled="isLoading"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
              Reject
            </button>

            <button
              @click="applyFix"
              class="action-btn primary"
              :disabled="!canApplyFix || isLoading"
            >
              <svg v-if="isLoading" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              {{ isLoading ? 'Applying...' : 'Apply Fix' }}
            </button>
          </div>
        </slot>
      </div>

      <!-- Advanced Section (collapsible) -->
      <details class="advanced-section" v-if="showAdvanced">
        <summary class="advanced-summary">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          Advanced Options
        </summary>
        <div class="advanced-content">
          <slot name="advanced-content">
            <!-- SPARQL Query Display -->
            <div class="sparql-section">
              <h4>SPARQL Query</h4>
              <pre class="sparql-query">{{ displayQuery }}</pre>
            </div>
          </slot>
        </div>
      </details>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  // Basic violation information
  focusNode: String,
  resultPath: String,
  value: [String, Number],
  message: String,
  constraintComponent: String,

  // Constraint-specific context
  context: {
    type: Object,
    default: () => ({})
  },

  // Violation state
  isLoading: {
    type: Boolean,
    default: false
  },
  hasError: {
    type: Boolean,
    default: false
  },
  errorMessage: String,

  // Configuration
  showAdvanced: {
    type: Boolean,
    default: true
  },
  canApplyFix: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['reject-fix', 'apply-fix'])

// Computed properties
const displayQuery = computed(() => {
  return props.context?.sparqlQuery || props.context?.proposed_repair?.query || 'No query available'
})

// Methods
const getConstraintIcon = () => {
  // Handle both full URIs (http://...#Component) and prefixed names (sh:Component)
  let constraintType = ''
  if (props.constraintComponent?.includes('#')) {
    constraintType = props.constraintComponent.split('#').pop() || ''
  } else {
    constraintType = props.constraintComponent || ''
  }

  // Remove prefix if present (e.g., "sh:" from "sh:InConstraintComponent")
  if (constraintType.includes(':')) {
    constraintType = constraintType.split(':').pop() || ''
  }

  // Map of constraint types to icon components
  const iconMap = {
    'ClassConstraintComponent': 'CheckCircleIcon',
    'DatatypeConstraintComponent': 'CodeBracketIcon',
    'NodeKindConstraintComponent': 'DocumentTextIcon',
    'MinCountConstraintComponent': 'PlusCircleIcon',
    'MaxCountConstraintComponent': 'MinusCircleIcon',
    'MinInclusiveConstraintComponent': 'ArrowTrendingUpIcon',
    'MaxInclusiveConstraintComponent': 'ArrowTrendingDownIcon',
    'MinLengthConstraintComponent': 'Bars3Icon',
    'MaxLengthConstraintComponent': 'Bars3BottomLeftIcon',
    'PatternConstraintComponent': 'FingerPrintIcon',
    'LanguageInConstraintComponent': 'LanguageIcon',
    'UniqueLangConstraintComponent': 'CheckBadgeIcon',
    'EqualsConstraintComponent': 'ArrowsPointingInIcon',
    'DisjointConstraintComponent': 'XMarkIcon',
    'LessThanConstraintComponent': 'ArrowLeftIcon',
    'LessThanOrEqualsConstraintComponent': 'ArrowSmallLeftIcon',
    'NotConstraintComponent': 'NoSymbolIcon',
    'AndConstraintComponent': 'LinkIcon',
    'OrConstraintComponent': 'LinkIcon',
    'XoneConstraintComponent': 'LinkIcon',
    'HasValueConstraintComponent': 'HashtagIcon',
    'InConstraintComponent': 'ListBulletIcon',
    'ClosedConstraintComponent': 'LockClosedIcon',
    'NodeConstraintComponent': 'CircleStackIcon',
    'QualifiedValueShapeConstraintComponent': 'CheckCircleIcon',
    'SPARQLConstraintComponent': 'CodeBracketIcon'
  }

  return iconMap[constraintType] || 'ExclamationTriangleIcon'
}

const getConstraintTitle = () => {
  // Handle both full URIs (http://...#Component) and prefixed names (sh:Component)
  let constraintType = ''
  if (props.constraintComponent?.includes('#')) {
    constraintType = props.constraintComponent.split('#').pop() || ''
  } else {
    constraintType = props.constraintComponent || ''
  }

  // Remove prefix if present (e.g., "sh:" from "sh:InConstraintComponent")
  if (constraintType.includes(':')) {
    constraintType = constraintType.split(':').pop() || ''
  }

  // Debug logging to see what we're getting
  console.log('🔍 Constraint Component:', props.constraintComponent)
  console.log('🔍 Extracted Type:', constraintType)

  const titleMap = {
    'ClassConstraintComponent': 'Wrong Type',
    'DatatypeConstraintComponent': 'Wrong Data Type',
    'NodeKindConstraintComponent': 'Wrong Node Kind',
    'MinCountConstraintComponent': 'Missing Required Values',
    'MaxCountConstraintComponent': 'Too Many Values',
    'MinInclusiveConstraintComponent': 'Value Too Small',
    'MaxInclusiveConstraintComponent': 'Value Too Large',
    'MinLengthConstraintComponent': 'Text Too Short',
    'MaxLengthConstraintComponent': 'Text Too Long',
    'PatternConstraintComponent': 'Invalid Format',
    'LanguageInConstraintComponent': 'Language Not Allowed',
    'UniqueLangConstraintComponent': 'Duplicate Language',
    'EqualsConstraintComponent': 'Values Not Equal',
    'DisjointConstraintComponent': 'Conflicting Values',
    'LessThanConstraintComponent': 'Value Not Less Than',
    'LessThanOrEqualsConstraintComponent': 'Value Not Less Or Equal',
    'NotConstraintComponent': 'Invalid Value',
    'AndConstraintComponent': 'Multiple Constraint Violations',
    'OrConstraintComponent': 'No Valid Options',
    'XoneConstraintComponent': 'Ambiguous Value',
    'HasValueConstraintComponent': 'Missing Required Value',
    'InConstraintComponent': 'Invalid Value',
    'ClosedConstraintComponent': 'Extra Properties',
    'NodeConstraintComponent': 'Invalid Resource',
    'QualifiedValueShapeConstraintComponent': 'Qualified Value Violation',
    'SPARQLConstraintComponent': 'Custom Rule Violation'
  }

  const selectedTitle = titleMap[constraintType] || 'Constraint Violation'
  console.log('🔍 Selected Title:', selectedTitle, 'for type:', constraintType)
  return selectedTitle
}

const getConstraintSubtitle = () => {
  // Provide specific subtitle based on constraint context
  if (props.context?.requiredClass) {
    return `Not an instance of: ${formatPropertyName(props.context.requiredClass)}`
  }
  if (props.context?.requiredDatatype) {
    return `Required type: ${props.context.requiredDatatype}`
  }
  if (props.context?.minValue !== undefined) {
    return `Minimum value: ${props.context.minValue}`
  }
  if (props.context?.maxValue !== undefined) {
    return `Maximum value: ${props.context.maxValue}`
  }
  if (props.context?.minLength !== undefined) {
    return `Minimum length: ${props.context.minLength} characters`
  }
  if (props.context?.maxLength !== undefined) {
    return `Maximum length: ${props.context.maxLength} characters`
  }
  if (props.context?.pattern) {
    return `Pattern: ${props.context.pattern}`
  }
  return null
}

const getStatusClass = () => {
  if (props.hasError) return 'status-error'
  if (props.isLoading) return 'status-loading'
  if (props.canApplyFix) return 'status-ready'
  return 'status-incomplete'
}

const getStatusText = () => {
  if (props.hasError) return 'Error'
  if (props.isLoading) return 'Processing'
  if (props.canApplyFix) return 'Ready'
  return 'Incomplete'
}

const formatPropertyName = (uri) => {
  if (!uri) return ''
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri
  }
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

const formatValue = (value) => {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'string') {
    // Check if it's a URI
    if (value.startsWith('http')) {
      return formatPropertyName(value)
    }
    return `"${value}"`
  }
  return String(value)
}

const rejectFix = () => {
  emit('reject-fix', {
    focusNode: props.focusNode,
    resultPath: props.resultPath,
    value: props.value,
    constraintComponent: props.constraintComponent
  })
}

const applyFix = () => {
  emit('apply-fix', {
    focusNode: props.focusNode,
    resultPath: props.resultPath,
    value: props.value,
    constraintComponent: props.constraintComponent,
    context: props.context
  })
}
</script>

<style scoped>
.shacl-violation-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden;
}

.card-header {
  @apply bg-gray-50 px-4 py-3 border-b border-gray-200;
}

.constraint-icon {
  @apply flex-shrink-0 text-amber-500;
}

.card-title {
  @apply text-lg font-semibold text-gray-800;
}

.card-subtitle {
  @apply text-sm text-gray-600 mt-1;
}

.status-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full;
}

.status-ready {
  @apply bg-green-100 text-green-800;
}

.status-loading {
  @apply bg-blue-100 text-blue-800;
}

.status-error {
  @apply bg-red-100 text-red-800;
}

.status-incomplete {
  @apply bg-gray-100 text-gray-800;
}

.card-content {
  @apply p-4 space-y-4;
}

.context-section {
  @apply space-y-2;
}

.context-row {
  @apply flex items-center gap-2;
}

.context-label {
  @apply text-sm font-medium text-gray-500 min-w-20;
}

.context-value {
  @apply text-sm text-gray-800 font-mono bg-gray-50 px-2 py-1 rounded;
}

.constraint-section {
  @apply bg-blue-50 border border-blue-200 rounded-lg p-4;
}

.action-section {
  @apply pt-4 border-t border-gray-200;
}

.default-actions {
  @apply flex items-center gap-3 justify-end;
}

.action-btn {
  @apply inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.action-btn.primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.action-btn.secondary {
  @apply bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500;
}

.advanced-section {
  @apply border-t border-gray-200 pt-4;
}

.advanced-summary {
  @apply flex items-center gap-2 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50 p-2 rounded -mx-2;
}

.advanced-content {
  @apply mt-3 space-y-4;
}

.sparql-section h4 {
  @apply text-sm font-medium text-gray-700 mb-2;
}

.sparql-query {
  @apply text-xs font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto bg-gray-50 p-3 rounded border border-gray-200;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>