<template>
  <tr class="even:bg-gray-50 hover:bg-blue-50 transition-colors" @click="toggleDetails">
    <td class="text-left px-6 py-4 border-b border-gray-300">{{ rowNumber }}</td>

    <td class="text-left px-6 py-4 border-b border-gray-300 violation-triple">
      <div class="triple-line">
        <span class="triple-subject">{{ formatNodeName(focusNode) }}</span>
      </div>
      <div class="triple-line">
        <span class="triple-predicate">{{ formatPropertyName(resultPath) }}</span>
      </div>
      <div class="triple-line">
        <span class="triple-object">{{ value }}</span>
      </div>
    </td>

    <td class="text-left px-6 py-4 border-b border-gray-300 error-message">
      <div class="message-text">{{ message }}</div>
    </td>

    <td class="text-right px-6 py-4 border-b border-gray-300">
      <button @click.stop="toggleDetails" class="toggle-btn">
        <span v-if="showDetails" class="triangle-down"></span>
        <span v-else class="triangle-left"></span>
      </button>
    </td>
  </tr>

  <!-- Details Section -->
  <tr v-if="showDetails">
    <td colspan="4" class="details-cell px-6 py-6 border-b border-gray-300">
      <!-- Problem & Solution Cards -->
      <div class="space-y-4">
        <!-- Problem Explanation -->
        <div class="p-4 rounded-lg bg-yellow-50 border-l-4 border-yellow-400">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="flex-1">
              <p class="text-sm font-semibold text-gray-700 mb-1">Problem Explanation</p>
              <div v-if="explanationLoading" class="text-gray-600 italic text-sm">
                Loading explanation...
              </div>
              <p v-else-if="explanationData" class="text-sm text-gray-800">
                {{ explanationData.explanation_natural_language }}
              </p>
              <div v-else class="text-sm">
                <div v-if="autoLoadingExplanations" class="text-gray-600 italic text-sm">
                  Checking for explanations...
                </div>
                <button v-else @click="loadExplanation" class="text-blue-600 hover:text-blue-800 underline">
                  Generate Explanation
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Suggested Solution -->
        <div class="p-4 rounded-lg bg-cyan-50 border-l-4 border-cyan-400">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-cyan-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="flex-1">
              <p class="text-sm font-semibold text-gray-700 mb-1">Suggested Solution</p>
              <div v-if="explanationLoading" class="text-gray-600 italic text-sm">
                Loading repair suggestion...
              </div>
              <div v-else-if="explanationData" class="space-y-3">
                <p class="text-sm text-gray-800">{{ explanationData.suggestion_natural_language }}</p>

                <!-- Action Badge - PHOENIX Style -->
                <div class="flex items-center gap-2 mt-3">
                  <span :class="getActionBadgeClass(getActionType(explanationData.proposed_repair?.query))" 
                        class="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold">
                    <svg v-if="getActionType(explanationData.proposed_repair?.query) === 'ADD'" 
                         class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                    <svg v-else-if="getActionType(explanationData.proposed_repair?.query) === 'DELETE'" 
                         class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path>
                    </svg>
                    <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                    </svg>
                    {{ getActionType(explanationData.proposed_repair?.query) }}
                  </span>
                  <span class="text-xs text-gray-500">{{ formatPropertyName(resultPath) }}</span>
                </div>

                <!-- Input Interface Based on Constraint Type -->
                <div class="space-y-3">
                  <!-- MaxCount Violation - PHOENIX Style -->
                  <div v-if="isMaxCountViolation" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      {{ getMaxCountInputLabel() }}
                    </label>
                    <!-- Single selection for maxCount = 1 -->
                    <select v-if="maxCount === 1" v-model="selectedValues[0]"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-sm">
                      <option value="">Choose the correct value to keep...</option>
                      <option v-for="val in actualValues" :key="val" :value="val">{{ val }}</option>
                    </select>
                    <!-- Multi-selection for maxCount > 1 -->
                    <div v-else class="space-y-2 p-3 border rounded-md bg-white shadow-sm">
                      <div v-for="val in actualValues" :key="val" class="flex items-center gap-2">
                        <input type="checkbox" :id="`value-${val}`" :value="val" v-model="selectedValues"
                               :disabled="selectedValues.length >= maxCount && !selectedValues.includes(val)"
                               class="h-4 w-4 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500">
                        <label :for="`value-${val}`" class="text-sm">{{ val }}</label>
                      </div>
                      <div class="text-xs text-gray-500 mt-2">
                        {{ selectedValues.length }} of {{ maxCount }} selected
                      </div>
                    </div>
                  </div>

                  <!-- Pattern Violation - PHOENIX Style with Prefix/Suffix -->
                  <div v-else-if="isPatternViolation" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      Enter the correct value:
                    </label>
                    <!-- Pattern Input with Prefix/Suffix -->
                    <div v-if="patternInfo.hasVariable" class="flex items-center gap-1 p-2 border rounded-md bg-gray-50 shadow-sm">
                      <span v-if="patternInfo.prefix" class="font-mono text-gray-600 text-sm select-none">
                        {{ patternInfo.prefix }}
                      </span>
                      <input v-model="patternInputValue" @input="updatePatternInput" type="text"
                             :placeholder="getPatternPlaceholder()"
                             class="flex-1 px-2 py-1 border-b border-gray-300 bg-transparent focus:border-cyan-500 focus:outline-none font-mono text-sm">
                      <span v-if="patternInfo.suffix" class="font-mono text-gray-600 text-sm select-none">
                        {{ patternInfo.suffix }}
                      </span>
                    </div>
                    <!-- Fallback for patterns without clear structure -->
                    <input v-else v-model="userProvidedValue" type="text"
                           :placeholder="getPatternPlaceholder()"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-sm font-mono">
                    <div v-if="getPatternExample()" class="text-xs text-gray-500 flex items-center gap-1">
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      Example: {{ getPatternExample() }}
                    </div>
                  </div>

                  <!-- InConstraint Violation - PHOENIX Style -->
                  <div v-else-if="isInConstraintViolation && allowedValues.length > 0" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      Select the correct value:
                    </label>
                    <select v-model="selectedAllowedValue"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-sm">
                      <option value="">Choose from the list of allowed values...</option>
                      <option v-for="val in allowedValues" :key="val" :value="val">{{ val }}</option>
                    </select>
                  </div>

                  <!-- MinInclusive Violation - PHOENIX Style -->
                  <div v-else-if="isMinInclusiveViolation && allowedValues.length > 0" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      Select a value greater than or equal to the minimum:
                    </label>
                    <select v-model="selectedAllowedValue"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-sm">
                      <option value="">Choose a value that meets the minimum requirement...</option>
                      <option v-for="val in allowedValues" :key="val" :value="val">{{ val }}</option>
                    </select>
                    <div v-if="explanationData?.constraint_info?.minValue" class="text-xs text-gray-500">
                      Minimum required value: {{ explanationData.constraint_info.minValue }}
                    </div>
                  </div>

                  <!-- MaxInclusive Violation - PHOENIX Style -->
                  <div v-else-if="isMaxInclusiveViolation && allowedValues.length > 0" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      Select a value less than or equal to the maximum:
                    </label>
                    <select v-model="selectedAllowedValue"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-sm">
                      <option value="">Choose a value that meets the maximum requirement...</option>
                      <option v-for="val in allowedValues" :key="val" :value="val">{{ val }}</option>
                    </select>
                    <div v-if="explanationData?.constraint_info?.maxValue" class="text-xs text-gray-500">
                      Maximum allowed value: {{ explanationData.constraint_info.maxValue }}
                    </div>
                  </div>

                  <!-- General User Input -->
                  <div v-else-if="needsUserInput" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      Enter the correct value:
                    </label>
                    <input v-model="userProvidedValue" type="text"
                           :placeholder="getInputPlaceholder()"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 text-sm">
                  </div>

                  <!-- Value to Remove - PHOENIX Style -->
                  <div v-if="value && getActionType(explanationData.proposed_repair?.query) === 'DELETE'" class="space-y-2">
                    <label class="block text-sm font-semibold text-gray-700">
                      Value to remove:
                    </label>
                    <div class="p-2 bg-red-50 rounded border border-red-200">
                      <code class="text-sm text-red-800">{{ value }}</code>
                    </div>
                  </div>
                </div>

                <!-- Advanced: Edit SPARQL Query -->
                <details class="border rounded-lg mt-4">
                  <summary class="p-3 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    Advanced: Edit SPARQL Query
                  </summary>
                  <div class="p-3 border-t bg-gray-50">
                    <textarea v-model="editableQuery"
                              class="w-full p-3 bg-white rounded text-xs font-mono text-gray-700 border border-gray-300 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none resize-none"
                              rows="8"></textarea>
                  </div>
                </details>

                <!-- Current SPARQL Query -->
                <details class="border rounded-lg">
                  <summary class="p-3 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    Current SPARQL Query
                  </summary>
                  <div class="p-3 border-t bg-gray-50">
                    <pre class="text-xs font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto">{{ displayQuery }}</pre>
                  </div>
                </details>

                <!-- Action Buttons - PHOENIX Style -->
                <div class="flex flex-wrap items-center gap-2 pt-4">
                  <button @click="rejectRepair"
                          class="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                    Reject
                  </button>
                  
                  <button v-if="!isMaxCountViolation" @click="toggleEditMode"
                          class="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                    </svg>
                    Edit Query
                  </button>
                  
                  <button @click="acceptRepair" :disabled="!canAcceptRepair"
                          :class="{'opacity-50 cursor-not-allowed': !canAcceptRepair}"
                          class="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-cyan-600 hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    Accept Fix
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </td>
  </tr>
</template>

<script setup>
import { defineProps, ref, computed, watch } from 'vue';
import api from '@/utils/api';

const props = defineProps({
  rowNumber: Number,
  focusNode: String,
  resultPath: String,
  value: [String, Number],
  message: String,
  propertyShape: String,
  severity: String,
  shapes: Object,
  targetClass: [String, Array],
  targetNode: [String, Array],
  targetSubjectsOf: [String, Array],
  targetObjectsOf: [String, Array],
  nodeShape: String,
  constraintComponent: String,
  context: Object, // PHOENIX-style context with example values
});

// State
const showDetails = ref(false);
const explanationData = ref(null);
const explanationLoading = ref(false);
const autoLoadingExplanations = ref(false);
const editableQuery = ref('');
const editMode = ref(false);

// Input states
const userProvidedValue = ref('');
const selectedValues = ref([]);
const selectedAllowedValue = ref('');
const patternInputValue = ref('');
const patternInfo = ref({ prefix: '', suffix: '', hasVariable: false });
const maxCount = ref(1);
const actualValues = ref([]);
const allowedValues = ref([]);

// Computed properties
const isMaxCountViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  return constraint.includes('MaxCountConstraintComponent') || constraint.includes('MaxCount');
});

const isPatternViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  return constraint.includes('PatternConstraintComponent') || constraint.includes('Pattern');
});

const isInConstraintViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  return constraint.includes('InConstraintComponent') || constraint.includes('InConstraint');
});

const isMinInclusiveViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  return constraint.includes('MinInclusiveConstraintComponent') || constraint.includes('MinInclusive');
});

const isMaxInclusiveViolation = computed(() => {
  const constraint = props.constraintComponent || '';
  return constraint.includes('MaxInclusiveConstraintComponent') || constraint.includes('MaxInclusive');
});

const needsUserInput = computed(() => {
  const query = explanationData.value?.proposed_repair?.query || '';
  return query.includes('$user_provided_value');
});

// Helper functions for formatting URIs and names (PHOENIX-style)
const formatNodeName = (uri) => {
  if (!uri) return '';

  // If it's already formatted (has prefix), return as is
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri;
  }

  // Extract local name from URI
  const parts = uri.split(/[#\/]/);
  return parts[parts.length - 1] || uri;
};

const formatPropertyName = (uri) => {
  if (!uri) return '';

  // If it's already formatted (has prefix), return as is
  if (uri.includes(':') && !uri.startsWith('http')) {
    return uri;
  }

  // Extract local name from URI
  const parts = uri.split(/[#\/]/);
  return parts[parts.length - 1] || uri;
};

// PHOENIX-style helper methods
const getActionType = (query) => {
  if (!query) return 'MODIFY';
  if (query.includes('INSERT') && !query.includes('DELETE')) return 'ADD';
  if (query.includes('DELETE')) return 'DELETE';
  return 'MODIFY';
};

const getActionBadgeClass = (actionType) => {
  const classMap = {
    'ADD': 'bg-green-100 text-green-800 border border-green-200',
    'DELETE': 'bg-red-100 text-red-800 border border-red-200',
    'MODIFY': 'bg-blue-100 text-blue-800 border border-blue-200'
  };
  return classMap[actionType] || classMap['MODIFY'];
};

const getMaxCountInputLabel = () => {
  if (maxCount.value === 1) {
    return 'Select the value to keep:';
  }
  return `Select up to ${maxCount.value} values to keep:`;
};

const updatePatternInput = () => {
  // Combine prefix, input, and suffix for pattern constraints
  const fullValue = `${patternInfo.value.prefix}${patternInputValue.value}${patternInfo.value.suffix}`;
  userProvidedValue.value = fullValue;
};

const parsePattern = (pattern) => {
  // Parse regex pattern into prefix and suffix (similar to PHOENIX's PatternInput)
  try {
    const match = pattern.match(/^(.*?)(\(.*?\))(.*)$/);
    if (match) {
      return {
        prefix: match[1].replace(/\\/g, ''),
        suffix: match[3].replace(/\\/g, ''),
        hasVariable: true
      };
    }
    return { prefix: '', suffix: '', hasVariable: false };
  } catch (e) {
    return { prefix: '', suffix: '', hasVariable: false };
  }
};

const getInputPlaceholder = () => {
  const propertyLower = props.resultPath?.toLowerCase() || '';

  if (propertyLower.includes('name')) return 'e.g., John Doe';
  if (propertyLower.includes('email')) return 'e.g., user@example.com';
  if (propertyLower.includes('date')) return 'e.g., 2024-01-01';
  if (propertyLower.includes('age') || propertyLower.includes('count')) return 'e.g., 25';
  if (propertyLower.includes('url')) return 'e.g., https://example.com';

  return 'Enter a value...';
};

const getPatternExample = () => {
  // Try to get example value from multiple sources (like PHOENIX does)
  let example = '';

  if (props.context?.exampleValue) {
    example = props.context.exampleValue;
    console.log('Found exampleValue in props.context:', example);
  } else if (explanationData.value?.constraint_info?.exampleValue) {
    example = explanationData.value.constraint_info.exampleValue;
    console.log('Found exampleValue in explanationData:', example);
  } else if (patternInfo.value?.example) {
    example = patternInfo.value.example;
    console.log('Found exampleValue in patternInfo:', example);
  }

  console.log('getPatternExample returning:', example);
  return example;
};

const getPatternPlaceholder = () => {
  const example = getPatternExample();
  if (example) {
    return `e.g., ${example}`;
  }
  return getInputPlaceholder();
};

const initializeConstraintSpecificData = () => {
  // Initialize MaxCount data
  if (isMaxCountViolation.value) {
    // Extract from multiple sources in priority order: context from backend, then explanation data
    const contextData = props.context || {};
    const constraintInfo = explanationData.value?.constraint_info || {};

    maxCount.value = contextData.maxCount || constraintInfo.maxCount || 1;
    actualValues.value = contextData.actualValues || constraintInfo.actualValues || [props.value].filter(Boolean);

    // Pre-select first maxCount values (PHOENIX behavior)
    selectedValues.value = actualValues.value.slice(0, maxCount.value);
  }

  // Initialize Pattern data
  if (isPatternViolation.value) {
    // Extract from multiple sources in priority order: context from backend, then explanation data
    const contextData = props.context || {};
    const constraintInfo = explanationData.value?.constraint_info || {};

    const pattern = contextData.pattern || constraintInfo.pattern;
    if (pattern) {
      patternInfo.value = parsePattern(pattern);
      patternInfo.value.example = contextData.exampleValue || constraintInfo.exampleValue || '';

      // Debug logging for pattern initialization
      console.log('Pattern violation detected:', {
        constraintComponent: props.constraintComponent,
        pattern,
        contextData,
        exampleValue: contextData.exampleValue,
        patternInfo: patternInfo.value,
        getPatternExample: getPatternExample()
      });
    } else {
      console.log('Pattern violation but no pattern found:', {
        constraintComponent: props.constraintComponent,
        contextData,
        constraintInfo
      });
    }
  }

  // Initialize InConstraint data
  if (isInConstraintViolation.value) {
    // Extract from multiple sources in priority order: context from backend, then explanation data
    const contextData = props.context || {};
    const constraintInfo = explanationData.value?.constraint_info || {};

    allowedValues.value = contextData.allowedValues || constraintInfo.allowedValues || [];

    // Debug logging
    console.log('InConstraint detected:', {
      constraintComponent: props.constraintComponent,
      contextData,
      allowedValues: allowedValues.value,
      allowedValuesLength: allowedValues.value.length
    });
  }

  // Initialize MinInclusive data
  if (isMinInclusiveViolation.value) {
    // Extract from multiple sources in priority order: context from backend, then explanation data
    const contextData = props.context || {};
    const constraintInfo = explanationData.value?.constraint_info || {};

    allowedValues.value = contextData.allowedValues || constraintInfo.allowedValues || [];

    // Debug logging
    console.log('MinInclusive detected:', {
      constraintComponent: props.constraintComponent,
      contextData,
      constraintInfo,
      allowedValues: allowedValues.value,
      minValue: contextData.minValue || constraintInfo.minValue
    });
  }

  // Initialize MaxInclusive data
  if (isMaxInclusiveViolation.value) {
    // Extract from multiple sources in priority order: context from backend, then explanation data
    const contextData = props.context || {};
    const constraintInfo = explanationData.value?.constraint_info || {};

    allowedValues.value = contextData.allowedValues || constraintInfo.allowedValues || [];

    // Debug logging
    console.log('MaxInclusive detected:', {
      constraintComponent: props.constraintComponent,
      contextData,
      constraintInfo,
      allowedValues: allowedValues.value,
      maxValue: contextData.maxValue || constraintInfo.maxValue
    });
  }
};

// Helper methods to provide contextual information like PHOENIX
const getConstraintTypeLabel = (constraintComponent) => {
  if (!constraintComponent) return 'Unknown';

  const labelMap = {
    'MinCountConstraintComponent': 'Missing Required Value',
    'MaxCountConstraintComponent': 'Too Many Values',
    'DatatypeConstraintComponent': 'Incorrect Data Type',
    'PatternConstraintComponent': 'Pattern Mismatch',
    'InConstraintComponent': 'Value Not in Allowed List',
    'MinLengthConstraintComponent': 'Value Too Short',
    'MaxLengthConstraintComponent': 'Value Too Long',
    'MinInclusiveConstraintComponent': 'Value Too Small',
    'MaxInclusiveConstraintComponent': 'Value Too Large',
    'NodeKindConstraintComponent': 'Wrong Node Type',
    'ClassConstraintComponent': 'Wrong Class Type'
  };

  const componentName = constraintComponent.split('#').pop() || constraintComponent;
  return labelMap[componentName] || componentName.replace(/([A-Z])/g, ' $1').trim();
};

const getConstraintHint = (constraintComponent) => {
  if (!constraintComponent) return '';

  const hints = {
    'MinCountConstraintComponent': 'Use INSERT DATA to add a missing required value.',
    'MaxCountConstraintComponent': 'Use DELETE WHERE to remove extra values.',
    'DatatypeConstraintComponent': 'Use DELETE/INSERT to fix the data type (e.g., add xsd:integer for numbers).',
    'PatternConstraintComponent': 'Ensure the value matches the required pattern (like email format).',
    'InConstraintComponent': 'Value must be one of the allowed values in the constraint.',
    'MinLengthConstraintComponent': 'Value needs more characters to meet minimum length.',
    'MaxLengthConstraintComponent': 'Value has too many characters, needs to be shortened.',
    'MinInclusiveConstraintComponent': 'Value must be greater than or equal to the minimum.',
    'MaxInclusiveConstraintComponent': 'Value must be less than or equal to the maximum.',
    'NodeKindConstraintComponent': 'Expected either a literal value or a URI/IRI node.',
    'ClassConstraintComponent': 'Resource must be an instance of the specified class.'
  };

  const componentName = constraintComponent.split('#').pop() || constraintComponent;
  return hints[componentName] || '';
};

const getQueryPlaceholder = (constraintComponent) => {
  const componentName = constraintComponent?.split('#').pop() || '';

  if (componentName.includes('MinCount')) {
    return `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "EXAMPLE_VALUE" .
  }
}`;
  } else if (componentName.includes('MaxCount')) {
    return `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
}`;
  } else if (componentName.includes('Datatype')) {
    return `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_XXX> {
    <${props.focusNode}> <${props.resultPath}> "CORRECTED_VALUE"^^xsd:datatype .
  }
}`;
  } else {
    return `# Modify the SPARQL query based on the specific constraint
# Make sure to use the correct graph URI and actual values`;
  }
};

const generateSampleQuery = () => {
  const componentName = props.constraintComponent?.split('#').pop() || '';

  let sampleQuery = '';

  if (componentName.includes('MinCount')) {
    // Generate a sensible default based on property name
    const defaultValue = getDefaultValueForProperty(props.resultPath);
    sampleQuery = `INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> ${defaultValue} .
  }
}`;
  } else if (componentName.includes('MaxCount')) {
    sampleQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
}`;
  } else if (componentName.includes('Datatype')) {
    const correctedValue = getCorrectedDatatypeValue(props.value, props.resultPath);
    sampleQuery = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> ${correctedValue} .
  }
}`;
  } else {
    sampleQuery = `# Example SPARQL query for ${componentName}
# Modify according to your specific needs
DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    <${props.focusNode}> <${props.resultPath}> "CORRECTED_VALUE" .
  }
}`;
  }

  editableQuery.value = sampleQuery;
};

// Helper functions to generate sensible defaults (similar to PHOENIX's approach)
const getDefaultValueForProperty = (propertyPath) => {
  if (!propertyPath) return '""';

  const lowerPath = propertyPath.toLowerCase();

  if (lowerPath.includes('name') || lowerPath.includes('label') || lowerPath.includes('title')) {
    return '"Unknown Name"';
  } else if (lowerPath.includes('email') || lowerPath.includes('mail')) {
    return '"unknown@example.com"';
  } else if (lowerPath.includes('date') || lowerPath.includes('created') || lowerPath.includes('modified')) {
    return `"${new Date().toISOString().split('T')[0]}"^^xsd:date`;
  } else if (lowerPath.includes('age') || lowerPath.includes('count') || lowerPath.includes('number')) {
    return '"0"^^xsd:integer';
  } else if (lowerPath.includes('description') || lowerPath.includes('comment') || lowerPath.includes('text')) {
    return '""';
  } else if (lowerPath.includes('url') || lowerPath.includes('link') || lowerPath.includes('uri')) {
    return '"http://example.org"';
  } else {
    return '""';
  }
};

const getCorrectedDatatypeValue = (value, propertyPath) => {
  if (!value) return '""';

  // Try to determine appropriate datatype based on property name
  const lowerPath = propertyPath?.toLowerCase() || '';

  if (lowerPath.includes('age') || lowerPath.includes('count') || lowerPath.includes('number')) {
    return isNaN(value) ? `"0"^^xsd:integer` : `"${value}"^^xsd:integer`;
  } else if (lowerPath.includes('date') || lowerPath.includes('created') || lowerPath.includes('modified')) {
    return `"${value}"^^xsd:date`;
  } else if (lowerPath.includes('email') || lowerPath.includes('url') || lowerPath.includes('uri')) {
    return `"${value}"`;
  } else {
    // Default to string
    return `"${value}"`;
  }
};

// Watchers to initialize constraint-specific data when context or explanation data changes
watch(() => props.context, () => {
  initializeConstraintSpecificData();
}, { immediate: true });

watch(() => explanationData.value, () => {
  initializeConstraintSpecificData();
}, { immediate: true });

// Auto-load explanations when details are opened
watch(() => showDetails.value, (newValue) => {
  if (newValue && !explanationData.value && !explanationLoading.value && !autoLoadingExplanations.value) {
    // Automatically try to load explanation when user opens details
    autoLoadExplanation();
  }
});

// Watcher to handle auto-loading state changes
watch(() => autoLoadingExplanations.value, (newValue) => {
  if (newValue && !explanationData.value && !explanationLoading.value) {
    loadExplanation();
  }
});

// PHOENIX-style watchers to automatically update SPARQL queries
watch(editableQuery, (newValue) => {
  // This watcher now primarily serves to keep the advanced edit field in sync
  // The main query logic is handled by the `finalQuery` computed property.
});


watch(selectedAllowedValue, (newValue) => {
  if (!newValue) return;
  userProvidedValue.value = newValue;

  // Update SPARQL query for InConstraint and range violations
  if ((isInConstraintViolation.value || isMinInclusiveViolation.value || isMaxInclusiveViolation.value) && props.value) {
    const session_id = localStorage.getItem('shacl_session_id') || 'PLACEHOLDER';
    editableQuery.value = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_${session_id}> {
    <${props.focusNode}> <${props.resultPath}> "${props.value}" .
  }
};
INSERT DATA {
  GRAPH <http://ex.org/ValidationReport/Session_${session_id}> {
    <${props.focusNode}> <${props.resultPath}> "${newValue}" .
  }
}`;
  }
});

watch(selectedValues, (newValues) => {
  if (!isMaxCountViolation.value || !editableQuery.value) return;

  // For MaxCount violations, generate DELETE query for values to remove
  const valuesToDelete = actualValues.value.filter(v => !newValues.includes(v));
  if (valuesToDelete.length > 0) {
    const deleteClauses = valuesToDelete.map(val =>
      `<${props.focusNode}> <${props.resultPath}> "${val}" .`
    ).join('\n    ');

    editableQuery.value = `DELETE WHERE {
  GRAPH <http://ex.org/ValidationReport/Session_PLACEHOLDER> {
    ${deleteClauses}
  }
}`;
  }
}, { deep: true });

// Event handlers
const toggleDetails = () => {
  showDetails.value = !showDetails.value;
};

const loadExplanation = async () => {
  if (!props.focusNode) return;

  explanationLoading.value = true;
  autoLoadingExplanations.value = false; // Reset auto-loading state
  try {
    const session_id = localStorage.getItem('shacl_session_id');
    const response = await api.post('/api/explanation', {
      violation: {
        focus_node: props.focusNode,
        property_path: props.resultPath,
        constraint_id: props.constraintComponent,
        value: props.value,
        message: props.message
      },
      session_id
    });

    explanationData.value = response.data;
  } catch (error) {
    console.error('Error loading explanation:', error);
  } finally {
    explanationLoading.value = false;
  }
};

const autoLoadExplanation = () => {
  // Auto-load explanation with a short delay to show "checking" state
  autoLoadingExplanations.value = true;
  // Small delay to show the checking state
  setTimeout(() => {
    if (autoLoadingExplanations.value) {
      loadExplanation();
    }
  }, 500);
};

const toggleEditMode = () => {
  editMode.value = !editMode.value;
  if (editMode.value && explanationData.value?.proposed_repair?.query) {
    editableQuery.value = explanationData.value.proposed_repair.query;
  }
};

const acceptRepair = async () => {
  // Implementation for accepting repair
  console.log('Accepting repair...');
};

const rejectRepair = async () => {
  // Implementation for rejecting repair
  console.log('Rejecting repair...');
};

// Computed properties
const displayQuery = computed(() => {
  return explanationData.value?.proposed_repair?.query || editableQuery.value || 'No query available';
});

const canAcceptRepair = computed(() => {
  // Basic validation - can be enhanced
  if (isMaxCountViolation.value) {
    return selectedValues.value.length > 0;
  }
  if (isInConstraintViolation.value || isMinInclusiveViolation.value || isMaxInclusiveViolation.value) {
    return selectedAllowedValue.value;
  }
  if (needsUserInput.value) {
    return userProvidedValue.value.trim();
  }
  return true;
});
</script>


<style scoped>
table {
  width: 100%;
  border-collapse: collapse; /* Ensures no extra spacing */
}

td,th {
  padding: 1px 1px; /* Reduce padding inside cells */
}

div {
  text-align: left;
}

tr {
  cursor: pointer;
}

tr:hover {
  background-color: #f0f8ff;
}

/* Styling for the toggle button */
.toggle-column {
  text-align: right;
}

.toggle-btn {
  background-color: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.toggle-btn:hover {
  color: #007bff;
}

/* Symbols for toggle: triangle left and down */
.triangle-left {
  display: inline-block;
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 7px solid black; /* Left triangle */
}

.triangle-down {
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid black; /* Downward triangle */
}

.details-cell {
  background-color: #f9fafb; /* Light gray background for better contrast */
  border-radius: 8px; /* Rounded corners for a smoother look */
}

.details-list p {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #4a5568;
  margin-bottom: 8px;
}

.details-list strong {
  color: #2d3748; /* Darker text color for labels */
}

.shape-details {
  padding: 12px;
  font-size: 0.85rem;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
}

.text-xl {
  font-size: 1.25rem; /* Slightly larger font for headings */
}

.font-semibold {
  font-weight: 600; /* Semi-bold for better emphasis */
}

.text-gray-700 {
  color: #4a5568; /* Darker text for better contrast */
}

.text-gray-800 {
  color: #2d3748; /* Even darker for important text */
}

.mb-3 {
  margin-bottom: 16px; /* Adds space after headings */
}

.cursor-pointer:hover {
  background-color: #f0f4f8; /* Subtle hover effect */
}

.details-list p {
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 4px;
}

.details-list ul {
  padding-left: 1.5rem;
}

.details-list strong {
  color: #2d3748;
}

/* Styling for violated triple display */
.violation-triple {
  max-width: 250px;
}

.triple-line {
  margin-bottom: 4px;
  line-height: 1.3;
  word-break: break-all;
}

.triple-subject {
  color: #2563eb;
  font-weight: 500;
}

.triple-predicate {
  color: #059669;
  font-weight: 500;
}

.triple-object {
  color: #dc2626;
  font-weight: 500;
}

/* Styling for error message display */
.error-message {
  max-width: 200px;
}

.message-text {
  word-break: break-word;
  line-height: 1.4;
  color: #374151;
}

/* Enhanced styling for details section */
.details-cell {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 16px !important;
}

.details-cell table {
  word-break: break-word;
  line-height: 1.5;
}

.details-cell table td {
  vertical-align: top;
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.details-cell table td:last-child {
  border-bottom: none;
}

.details-cell .font-bold {
  min-width: 140px;
  color: #1f2937;
  font-weight: 600;
}

/* Improved styling for explanation section */
.grid.grid-cols-1 {
  gap: 24px;
}

.grid.grid-cols-1 > div {
  line-height: 1.5;
  word-break: break-word;
}

/* Make sure long URIs in explanation section wrap */
.text-gray-800 {
  word-break: break-all;
  overflow-wrap: break-word;
}
</style>
