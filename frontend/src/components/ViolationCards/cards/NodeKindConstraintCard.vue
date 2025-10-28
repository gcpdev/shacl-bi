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
      <div class="nodekind-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Wrong node kind</h4>
              <p class="alert-message">
                Current value is a <span class="node-kind-badge current">{{ currentNodeKind }}</span>
                but should be a <span class="node-kind-badge required">{{ requiredNodeKind }}</span>
              </p>
            </div>
          </div>
        </div>

        <!-- Fix Options -->
        <div class="fix-options">
          <h4 class="fix-title">Select or create a {{ requiredNodeKind.toLowerCase() }}:</h4>

          <!-- Required Node Kind is IRI -->
          <div v-if="requiredNodeKind === 'IRI'" class="iri-options">
            <!-- Resource Browser -->
            <div class="resource-browser">
              <div class="browser-header">
                <h5 class="browser-title">Resource Browser</h5>
                <div class="search-group">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                  </svg>
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="Search resources..."
                    class="search-input"
                  />
                </div>
              </div>

              <!-- Recent Resources -->
              <div class="recent-resources">
                <h6 class="section-title">Recent:</h6>
                <div class="resource-list">
                  <div
                    v-for="resource in filteredRecentResources"
                    :key="resource.uri"
                    class="resource-item"
                    :class="{ 'selected': selectedResource === resource.uri }"
                    @click="selectResource(resource)"
                  >
                    <div class="resource-info">
                      <div class="resource-name">{{ resource.name }}</div>
                      <div class="resource-uri">{{ formatNodeName(resource.uri) }}</div>
                    </div>
                    <div class="resource-type">{{ resource.type }}</div>
                  </div>
                </div>
              </div>

              <!-- Search Results -->
              <div v-if="searchQuery && searchResults.length > 0" class="search-results">
                <h6 class="section-title">Search Results:</h6>
                <div class="resource-list">
                  <div
                    v-for="resource in searchResults"
                    :key="resource.uri"
                    class="resource-item"
                    :class="{ 'selected': selectedResource === resource.uri }"
                    @click="selectResource(resource)"
                  >
                    <div class="resource-info">
                      <div class="resource-name">{{ resource.name }}</div>
                      <div class="resource-uri">{{ formatNodeName(resource.uri) }}</div>
                    </div>
                    <div class="resource-type">{{ resource.type }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Create New IRI -->
            <div class="create-iri-section">
              <h5 class="section-title">Or create new IRI:</h5>
              <div class="iri-input-group">
                <input
                  v-model="newIriValue"
                  type="text"
                  :placeholder="getIriPlaceholder()"
                  class="iri-input"
                />
                <button
                  @click="generateIriFromLiteral"
                  type="button"
                  class="generate-iri-btn"
                  title="Auto-generate from current literal value"
                  v-if="currentNodeKind === 'Literal'"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                  </svg>
                  Auto-generate
                </button>
              </div>
              <p class="iri-note">
                Auto-generate IRI from literal: "{{ value }}"
              </p>
            </div>
          </div>

          <!-- Required Node Kind is Literal -->
          <div v-else-if="requiredNodeKind === 'Literal'" class="literal-options">
            <div class="literal-input-group">
              <label class="input-label">Enter literal value:</label>
              <input
                v-model="literalValue"
                type="text"
                :placeholder="getLiteralPlaceholder()"
                class="literal-input"
              />
              <div v-if="context?.datatype" class="datatype-hint">
                <span class="hint-label">Datatype:</span>
                <code class="datatype-code">{{ context.datatype }}</code>
              </div>
            </div>

            <!-- Convert from IRI options -->
            <div v-if="currentNodeKind === 'IRI'" class="convert-options">
              <h5 class="section-title">Or convert from IRI:</h5>
              <div class="convert-methods">
                <label class="convert-method">
                  <input
                    v-model="convertMethod"
                    type="radio"
                    value="localname"
                    class="convert-radio"
                  />
                  <span class="convert-text">Use local name: "{{ getLocalName(value) }}"</span>
                </label>
                <label class="convert-method">
                  <input
                    v-model="convertMethod"
                    type="radio"
                    value="fulluri"
                    class="convert-radio"
                  />
                  <span class="convert-text">Use full URI as string</span>
                </label>
                <label class="convert-method">
                  <input
                    v-model="convertMethod"
                    type="radio"
                    value="label"
                    class="convert-radio"
                  />
                  <span class="convert-text">Use rdfs:label (if available)</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Required Node Kind is BlankNode -->
          <div v-else-if="requiredNodeKind === 'BlankNode'" class="blanknode-options">
            <div class="blanknode-input-group">
              <label class="input-label">Blank Node ID (optional):</label>
              <input
                v-model="blankNodeId"
                type="text"
                placeholder="Auto-generated if empty"
                class="blanknode-input"
              />
              <p class="blanknode-note">
                Blank nodes are identified within the current graph only
              </p>
            </div>
          </div>
        </div>

        <!-- Preview Section -->
        <div class="preview-section">
          <h5 class="preview-title">Preview:</h5>
          <div class="preview-content">
            <code class="preview-value">{{ getPreviewValue() }}</code>
          </div>
        </div>
      </div>
    </template>

    <template #advanced-content>
      <div class="advanced-nodekind-info">
        <h4>Node Kind Constraint Details</h4>
        <div class="nodekind-info-grid">
          <div class="info-item">
            <span class="info-label">Required Node Kind:</span>
            <code class="info-value">{{ requiredNodeKind }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Node Kind:</span>
            <code class="info-value">{{ currentNodeKind }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Value:</span>
            <code class="info-value">{{ value }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Property:</span>
            <code class="info-value">{{ resultPath }}</code>
          </div>
        </div>

        <!-- Node Kind Explanations -->
        <div class="nodekind-explanations">
          <h5>Node Kind Types:</h5>
          <div class="explanation-list">
            <div class="explanation-item">
              <strong>IRI:</strong> Internationalized Resource Identifier (a URI/URL)
            </div>
            <div class="explanation-item">
              <strong>Literal:</strong> A literal value (string, number, date, etc.)
            </div>
            <div class="explanation-item">
              <strong>BlankNode:</strong> An anonymous node identified only within the current graph
            </div>
          </div>
        </div>
      </div>
    </template>
  </ShaclViolationCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
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
const searchQuery = ref('')
const selectedResource = ref('')
const newIriValue = ref('')
const literalValue = ref('')
const blankNodeId = ref('')
const convertMethod = ref('localname')

// Computed properties
const requiredNodeKind = computed(() => {
  return props.context?.requiredNodeKind || 'IRI'
})

const currentNodeKind = computed(() => {
  // Determine current node kind from value
  const value = String(props.value || '')

  if (value.startsWith('_:')) {
    return 'BlankNode'
  }
  if (value.startsWith('http')) {
    return 'IRI'
  }
  if (value.includes('"') || !isNaN(value)) {
    return 'Literal'
  }

  // Default assumption
  return 'Literal'
})

const recentResources = computed(() => {
  return props.context?.recentResources || getDefaultRecentResources()
})

const searchResults = computed(() => {
  if (!searchQuery.value) return []

  const query = searchQuery.value.toLowerCase()
  return recentResources.value.filter(resource =>
    resource.name.toLowerCase().includes(query) ||
    resource.uri.toLowerCase().includes(query) ||
    resource.type.toLowerCase().includes(query)
  )
})

const filteredRecentResources = computed(() => {
  if (!searchQuery.value) return recentResources.value
  return []
})

const canApplyFix = computed(() => {
  if (requiredNodeKind.value === 'IRI') {
    return (selectedResource.value && selectedResource.value !== 'CREATE_NEW') ||
           (newIriValue.value.trim())
  }
  if (requiredNodeKind.value === 'Literal') {
    return literalValue.value.trim() || convertMethod.value
  }
  if (requiredNodeKind.value === 'BlankNode') {
    return true // Blank nodes can always be created
  }
  return false
})

// Methods
const formatNodeName = (uri) => {
  if (!uri) return ''
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri
  }
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

const getDefaultRecentResources = () => {
  return [
    {
      uri: 'http://example.org/Person001',
      name: 'Person001',
      type: 'Person'
    },
    {
      uri: 'http://example.org/Person002',
      name: 'Person002',
      type: 'Person'
    },
    {
      uri: 'http://example.org/Organization001',
      name: 'Organization001',
      type: 'Organization'
    }
  ]
}

const selectResource = (resource) => {
  selectedResource.value = resource.uri
  newIriValue.value = ''
}

const getIriPlaceholder = () => {
  const baseUri = 'http://example.org/'
  const className = formatNodeName(props.resultPath)
  return `${baseUri}${className}123`
}

const getLiteralPlaceholder = () => {
  const propertyName = props.resultPath?.toLowerCase() || ''

  if (propertyName.includes('name')) return 'e.g., John Doe'
  if (propertyName.includes('email')) return 'e.g., user@example.com'
  if (propertyName.includes('date')) return 'e.g., 2024-01-01'
  if (propertyName.includes('age')) return 'e.g., 25'

  return 'Enter literal value...'
}

const getLocalName = (uri) => {
  if (!uri) return ''
  const parts = uri.split(/[#\/]/)
  return parts[parts.length - 1] || uri
}

const generateIriFromLiteral = () => {
  const literal = String(props.value || '')
  const baseUri = 'http://example.org/'

  // Convert literal to a valid IRI format
  const normalized = literal
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .substring(0, 50)

  const randomId = Math.random().toString(36).substr(2, 6).toUpperCase()
  newIriValue.value = `${baseUri}${normalized}_${randomId}`
}

const getPreviewValue = () => {
  if (requiredNodeKind.value === 'IRI') {
    if (selectedResource.value) {
      return `<${selectedResource.value}>`
    }
    if (newIriValue.value) {
      return `<${newIriValue.value}>`
    }
  }
  if (requiredNodeKind.value === 'Literal') {
    if (literalValue.value) {
      return `"${literalValue.value}"`
    }
    if (convertMethod.value === 'localname') {
      return `"${getLocalName(props.value)}"`
    }
    if (convertMethod.value === 'fulluri') {
      return `"${props.value}"`
    }
    if (convertMethod.value === 'label') {
      return `"${getLocalName(props.value)}"`
    }
  }
  if (requiredNodeKind.value === 'BlankNode') {
    return blankNodeId.value ? '_:' + blankNodeId.value : '_:auto123'
  }

  return 'No value selected'
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  try {
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'
    let sparqlQuery = ''
    let finalValue = ''

    if (requiredNodeKind.value === 'IRI') {
      if (selectedResource.value) {
        finalValue = `<${selectedResource.value}>`
      } else if (newIriValue.value) {
        finalValue = `<${newIriValue.value}>`
      }
    } else if (requiredNodeKind.value === 'Literal') {
      if (literalValue.value) {
        const datatype = props.context?.datatype
        finalValue = datatype ? `"${literalValue.value}"^^${datatype}` : `"${literalValue.value}"`
      } else if (convertMethod.value === 'localname') {
        finalValue = `"${getLocalName(props.value)}"`
      } else if (convertMethod.value === 'fulluri') {
        finalValue = `"${props.value}"`
      } else if (convertMethod.value === 'label') {
        finalValue = `"${getLocalName(props.value)}"`
      }
    } else if (requiredNodeKind.value === 'BlankNode') {
      finalValue = blankNodeId.value ? '_:' + blankNodeId.value : '_:auto123'
    }

    if (props.value) {
      // Replace existing value
      sparqlQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> ${props.value} .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> ${finalValue} .
  }
}`
    } else {
      // Add new value
      sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> ${finalValue} .
  }
}`
    }

    await api.post('/api/repair', {
      repair_query: sparqlQuery,
      session_id: sessionId
    })

    emit('apply-fix', {
      newValue: finalValue,
      sparqlQuery: sparqlQuery,
      fixType: 'nodekind_conversion',
      nodeKind: requiredNodeKind.value
    })
  } catch (error) {
    console.error('Error applying node kind constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Watch for changes
watch(() => selectedResource.value, (newValue) => {
  if (newValue) {
    newIriValue.value = ''
  }
})

watch(() => newIriValue.value, (newValue) => {
  if (newValue) {
    selectedResource.value = ''
  }
})
</script>

<style scoped>
.nodekind-constraint-content {
  @apply space-y-4;
}

.violation-details {
  @apply space-y-3;
}

.alert {
  @apply flex items-start gap-3 p-4 rounded-lg border;
}

.alert-warning {
  @apply bg-yellow-50 border-yellow-200;
}

.alert-title {
  @apply text-sm font-semibold text-yellow-800;
}

.alert-message {
  @apply text-sm text-yellow-700 mt-1;
}

.node-kind-badge {
  @apply px-2 py-1 rounded text-xs font-medium;
}

.node-kind-badge.current {
  @apply bg-red-100 text-red-800;
}

.node-kind-badge.required {
  @apply bg-green-100 text-green-800;
}

.fix-options {
  @apply space-y-4;
}

.fix-title {
  @apply text-sm font-semibold text-gray-700;
}

.iri-options,
.literal-options,
.blanknode-options {
  @apply space-y-4;
}

.resource-browser {
  @apply border border-gray-200 rounded-lg overflow-hidden;
}

.browser-header {
  @apply bg-gray-50 p-4 border-b border-gray-200 space-y-3;
}

.browser-title {
  @apply text-sm font-medium text-gray-700;
}

.search-group {
  @apply relative;
}

.search-group svg {
  @apply absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400;
}

.search-input {
  @apply w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.recent-resources,
.search-results {
  @apply p-4 space-y-3;
}

.section-title {
  @apply text-sm font-medium text-gray-700;
}

.resource-list {
  @apply space-y-2;
}

.resource-item {
  @apply p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50 transition-colors;
}

.resource-item.selected {
  @apply bg-blue-50 border-blue-200;
}

.resource-info {
  @apply flex-1;
}

.resource-name {
  @apply text-sm font-medium text-gray-800;
}

.resource-uri {
  @apply text-xs text-gray-500 mt-1;
}

.resource-type {
  @apply text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded;
}

.create-iri-section {
  @apply space-y-3;
}

.iri-input-group {
  @apply flex gap-2;
}

.iri-input {
  @apply flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.generate-iri-btn {
  @apply p-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors;
}

.iri-note {
  @apply text-xs text-gray-500;
}

.literal-input-group {
  @apply space-y-2;
}

.input-label {
  @apply block text-sm font-medium text-gray-700;
}

.literal-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.datatype-hint {
  @apply flex items-center gap-2;
}

.hint-label {
  @apply text-xs text-gray-500;
}

.datatype-code {
  @apply text-xs font-mono text-gray-700 bg-gray-50 px-2 py-1 rounded;
}

.convert-options {
  @apply space-y-3;
}

.convert-methods {
  @apply space-y-2;
}

.convert-method {
  @apply flex items-center gap-2 cursor-pointer;
}

.convert-radio {
  @apply h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500;
}

.convert-text {
  @apply text-sm text-gray-700;
}

.blanknode-input-group {
  @apply space-y-2;
}

.blanknode-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.blanknode-note {
  @apply text-xs text-gray-500;
}

.preview-section {
  @apply space-y-2;
}

.preview-title {
  @apply text-sm font-medium text-gray-700;
}

.preview-content {
  @apply bg-gray-50 p-3 rounded-md border border-gray-200;
}

.preview-value {
  @apply text-sm font-mono text-gray-800;
}

.advanced-nodekind-info {
  @apply space-y-4;
}

.nodekind-info-grid {
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

.nodekind-explanations {
  @apply space-y-2;
}

.nodekind-explanations h5 {
  @apply text-sm font-medium text-gray-700;
}

.explanation-list {
  @apply space-y-1;
}

.explanation-item {
  @apply text-xs text-gray-600;
}
</style>