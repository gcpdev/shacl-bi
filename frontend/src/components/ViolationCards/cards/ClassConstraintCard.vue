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
      <div class="class-constraint-content">
        <!-- Violation Details -->
        <div class="violation-details">
          <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="alert-title">Not an instance of required class</h4>
              <p class="alert-message">
                The value <code>{{ formatNodeName(value) }}</code> is not an instance of
                <code>{{ formatNodeName(requiredClass) }}</code>
              </p>
            </div>
          </div>
        </div>

        <!-- Fix Options -->
        <div class="fix-options">
          <h4 class="fix-title">Choose how to fix this violation:</h4>

          <!-- Option 1: Select existing instance -->
          <div class="fix-option">
            <h5 class="option-title">Select a valid instance:</h5>
            <div class="instance-selection">
              <!-- Search input -->
              <div class="search-group">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Search instances..."
                  class="search-input"
                />
              </div>

              <!-- Instance list -->
              <div class="instance-list">
                <div
                  v-for="instance in filteredInstances"
                  :key="instance.uri"
                  class="instance-item"
                  :class="{ 'selected': selectedInstance === instance.uri }"
                  @click="selectInstance(instance)"
                >
                  <div class="instance-info">
                    <div class="instance-name">{{ instance.name }}</div>
                    <div class="instance-uri">{{ formatNodeName(instance.uri) }}</div>
                  </div>
                  <div class="instance-preview">
                    <div v-if="instance.preview" class="preview-text">
                      {{ instance.preview }}
                    </div>
                  </div>
                </div>

                <!-- Create new instance option -->
                <div
                  class="instance-item create-new"
                  :class="{ 'selected': selectedInstance === 'CREATE_NEW' }"
                  @click="selectCreateNew"
                >
                  <div class="instance-info">
                    <div class="instance-name">Create new {{ formatNodeName(requiredClass) }}...</div>
                    <div class="instance-uri">Generate a new instance</div>
                  </div>
                  <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Option 2: Convert current resource -->
          <div class="fix-option">
            <h5 class="option-title">Alternative: Convert current resource</h5>
            <div class="convert-option">
              <label class="checkbox-label">
                <input
                  v-model="addTypeToCurrent"
                  type="checkbox"
                  class="checkbox"
                />
                <span class="checkbox-text">
                  Add <code>rdf:type {{ formatNodeName(requiredClass) }}</code> to
                  <code>{{ formatNodeName(value) }}</code>
                </span>
              </label>
              <p class="convert-note">
                This will make the current resource an instance of the required class.
              </p>
            </div>
          </div>
        </div>

        <!-- Create New Instance Form (shown when "Create new" is selected) -->
        <div v-if="showCreateForm" class="create-form">
          <h5 class="form-title">Create New {{ formatNodeName(requiredClass) }}</h5>
          <div class="form-group">
            <label class="form-label">Instance Name:</label>
            <input
              v-model="newInstanceName"
              type="text"
              :placeholder="`e.g., ${getInstanceSuggestion()}`"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Instance URI:</label>
            <div class="uri-input-group">
              <input
                v-model="newInstanceUri"
                type="text"
                placeholder="Auto-generated if empty"
                class="form-input"
              />
              <button
                @click="generateInstanceUri"
                type="button"
                class="generate-btn"
              >
                Generate
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #advanced-content>
      <div class="advanced-class-info">
        <h4>Class Constraint Details</h4>
        <div class="class-info-grid">
          <div class="info-item">
            <span class="info-label">Required Class:</span>
            <code class="info-value">{{ requiredClass }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Current Value:</span>
            <code class="info-value">{{ value }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Property:</span>
            <code class="info-value">{{ resultPath }}</code>
          </div>
          <div class="info-item">
            <span class="info-label">Focus Node:</span>
            <code class="info-value">{{ focusNode }}</code>
          </div>
        </div>

        <!-- Available instances details -->
        <div v-if="context?.availableInstances" class="instances-detail">
          <h5>Available Instances ({{ context.availableInstances.length }})</h5>
          <pre class="instances-data">{{ JSON.stringify(context.availableInstances, null, 2) }}</pre>
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
  value: String,
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
const selectedInstance = ref('')
const addTypeToCurrent = ref(false)
const showCreateForm = ref(false)

// Create new instance form state
const newInstanceName = ref('')
const newInstanceUri = ref('')

// Computed properties
const requiredClass = computed(() => {
  return props.context?.requiredClass || props.context?.class || 'Unknown Class'
})

const availableInstances = computed(() => {
  return props.context?.availableInstances || getDefaultInstances()
})

const filteredInstances = computed(() => {
  if (!searchQuery.value) {
    return availableInstances.value
  }

  const query = searchQuery.value.toLowerCase()
  return availableInstances.value.filter(instance =>
    instance.name.toLowerCase().includes(query) ||
    instance.uri.toLowerCase().includes(query) ||
    (instance.preview && instance.preview.toLowerCase().includes(query))
  )
})

const canApplyFix = computed(() => {
  return (selectedInstance.value && selectedInstance.value !== 'CREATE_NEW') ||
         (showCreateForm.value && newInstanceName.value.trim()) ||
         addTypeToCurrent.value
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

const getDefaultInstances = () => {
  // Return some default instances for demo purposes
  return [
    {
      uri: 'http://example.org/Address001',
      name: 'Address001',
      preview: '123 Main St, Berlin'
    },
    {
      uri: 'http://example.org/Address002',
      name: 'Address002',
      preview: '456 Park Ave, Munich'
    }
  ]
}

const selectInstance = (instance) => {
  selectedInstance.value = instance.uri
  showCreateForm.value = false
}

const selectCreateNew = () => {
  selectedInstance.value = 'CREATE_NEW'
  showCreateForm.value = true
  generateInstanceUri()
}

const getInstanceSuggestion = () => {
  const className = formatNodeName(requiredClass.value).toLowerCase()
  const propertyName = formatNodeName(props.resultPath).toLowerCase()

  if (className.includes('address')) {
    return 'NewAddress'
  }
  if (className.includes('person')) {
    return 'NewPerson'
  }
  if (propertyName.includes('address')) {
    return 'NewAddress'
  }

  return `New${formatNodeName(requiredClass.value)}`
}

const generateInstanceUri = () => {
  const baseUri = 'http://example.org/'
  const className = formatNodeName(requiredClass.value)
  const randomId = Math.random().toString(36).substr(2, 9).toUpperCase()

  newInstanceUri.value = `${baseUri}${className}${randomId}`
}

const handleRejectFix = () => {
  emit('reject-fix')
}

const handleApplyFix = async () => {
  try {
    const sessionId = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER'
    let sparqlQuery = ''

    if (selectedInstance.value && selectedInstance.value !== 'CREATE_NEW') {
      // Replace with existing instance
      if (props.value) {
        sparqlQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> <${props.value}> .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> <${selectedInstance.value}> .
  }
}`
      } else {
        sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.focusNode}> <${props.resultPath}> <${selectedInstance.value}> .
  }
}`
      }
    } else if (showCreateForm.value && newInstanceName.value.trim()) {
      // Create new instance and use it
      const instanceUri = newInstanceUri.value || generateInstanceUri()
      sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${instanceUri}> rdf:type <${requiredClass.value}> ;
                 rdfs:label "${newInstanceName.value}"@en .
    <${props.focusNode}> <${props.resultPath}> <${instanceUri}> .
  }
}`
    } else if (addTypeToCurrent.value) {
      // Add type to current resource
      sparqlQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${sessionId}> {
    <${props.value}> rdf:type <${requiredClass.value}> .
  }
}`
    }

    if (sparqlQuery) {
      await api.post('/api/repair', {
        repair_query: sparqlQuery,
        session_id: sessionId
      })

      emit('apply-fix', {
        newValue: selectedInstance.value || newInstanceUri.value || props.value,
        sparqlQuery: sparqlQuery,
        fixType: selectedInstance.value === 'CREATE_NEW' ? 'create' :
                addTypeToCurrent.value ? 'add_type' : 'replace'
      })
    }
  } catch (error) {
    console.error('Error applying class constraint fix:', error)
    emit('reject-fix', { error: error.message })
  }
}

// Watch for changes
watch(() => selectedInstance.value, (newValue) => {
  if (newValue !== 'CREATE_NEW') {
    showCreateForm.value = false
  }
})

watch(() => addTypeToCurrent.value, (newValue) => {
  if (newValue) {
    selectedInstance.value = ''
    showCreateForm.value = false
  }
})
</script>

<style scoped>
.class-constraint-content {
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

.alert-message code {
  @apply bg-yellow-100 px-1 py-0.5 rounded text-xs font-mono;
}

.fix-options {
  @apply space-y-4;
}

.fix-title {
  @apply text-sm font-semibold text-gray-700;
}

.fix-option {
  @apply space-y-3;
}

.option-title {
  @apply text-sm font-medium text-gray-700;
}

.instance-selection {
  @apply space-y-3;
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

.instance-list {
  @apply max-h-64 overflow-y-auto border border-gray-200 rounded-md;
}

.instance-item {
  @apply p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors;
}

.instance-item:last-child {
  @apply border-b-0;
}

.instance-item.selected {
  @apply bg-blue-50 border-blue-200;
}

.instance-item.create-new {
  @apply bg-blue-50 border-blue-200;
}

.instance-item.create-new:hover {
  @apply bg-blue-100;
}

.instance-info {
  @apply flex-1;
}

.instance-name {
  @apply text-sm font-medium text-gray-800;
}

.instance-uri {
  @apply text-xs text-gray-500 mt-1;
}

.instance-preview {
  @apply text-xs text-gray-600;
}

.preview-text {
  @apply bg-gray-100 px-2 py-1 rounded text-gray-700;
}

.convert-option {
  @apply bg-gray-50 p-3 rounded-md border border-gray-200;
}

.checkbox-label {
  @apply flex items-start gap-3 cursor-pointer;
}

.checkbox {
  @apply h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5;
}

.checkbox-text {
  @apply text-sm text-gray-700;
}

.checkbox-text code {
  @apply bg-gray-200 px-1 py-0.5 rounded text-xs font-mono;
}

.convert-note {
  @apply text-xs text-gray-500 mt-2 ml-7;
}

.create-form {
  @apply bg-blue-50 p-4 rounded-md border border-blue-200 space-y-3;
}

.form-title {
  @apply text-sm font-semibold text-blue-800;
}

.form-group {
  @apply space-y-1;
}

.form-label {
  @apply block text-sm font-medium text-gray-700;
}

.form-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.uri-input-group {
  @apply flex gap-2;
}

.generate-btn {
  @apply px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium transition-colors;
}

.advanced-class-info {
  @apply space-y-4;
}

.class-info-grid {
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

.instances-detail h5 {
  @apply text-sm font-medium text-gray-700 mb-2;
}

.instances-data {
  @apply text-xs font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto bg-gray-50 p-3 rounded border border-gray-200;
}
</style>