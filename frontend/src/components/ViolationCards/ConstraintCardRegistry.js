/**
 * Constraint Card Registry
 *
 * This registry maps SHACL constraint components to their corresponding Vue components.
 * It allows for dynamic rendering of the appropriate card based on the constraint type.
 */

import ClassConstraintCard from './cards/ClassConstraintCard.vue'
import DatatypeConstraintCard from './cards/DatatypeConstraintCard.vue'
import NodeKindConstraintCard from './cards/NodeKindConstraintCard.vue'
import MinCountConstraintCard from './cards/MinCountConstraintCard.vue'
import MaxCountConstraintCard from './cards/MaxCountConstraintCard.vue'
import MinInclusiveConstraintCard from './cards/MinInclusiveConstraintCard.vue'
import MaxInclusiveConstraintCard from './cards/MaxInclusiveConstraintCard.vue'
import MinLengthConstraintCard from './cards/MinLengthConstraintCard.vue'
import MaxLengthConstraintCard from './cards/MaxLengthConstraintCard.vue'
import PatternConstraintCard from './cards/PatternConstraintCard.vue'
import LanguageInConstraintCard from './cards/LanguageInConstraintCard.vue'
import UniqueLangConstraintCard from './cards/UniqueLangConstraintCard.vue'
import EqualsConstraintCard from './cards/EqualsConstraintCard.vue'
import DisjointConstraintCard from './cards/DisjointConstraintCard.vue'
import LessThanConstraintCard from './cards/LessThanConstraintCard.vue'
import LessThanOrEqualsConstraintCard from './cards/LessThanOrEqualsConstraintCard.vue'
import NotConstraintCard from './cards/NotConstraintCard.vue'
import AndConstraintCard from './cards/AndConstraintCard.vue'
import OrConstraintCard from './cards/OrConstraintCard.vue'
import XoneConstraintCard from './cards/XoneConstraintCard.vue'
import HasValueConstraintCard from './cards/HasValueConstraintCard.vue'
import InConstraintCard from './cards/InConstraintCard.vue'
import ClosedConstraintCard from './cards/ClosedConstraintCard.vue'
import NodeConstraintCard from './cards/NodeConstraintCard.vue'
import QualifiedValueShapeConstraintCard from './cards/QualifiedValueShapeConstraintCard.vue'
import SparqlConstraintCard from './cards/SparqlConstraintCard.vue'

// Default fallback card for unknown constraint types
import DefaultConstraintCard from './cards/DefaultConstraintCard.vue'

/**
 * Registry mapping constraint component URIs to their Vue components
 */
const constraintCardRegistry = {
  // Value Type Constraints
  'http://www.w3.org/ns/shacl#ClassConstraintComponent': ClassConstraintCard,
  'http://www.w3.org/ns/shacl#DatatypeConstraintComponent': DatatypeConstraintCard,
  'http://www.w3.org/ns/shacl#NodeKindConstraintComponent': NodeKindConstraintCard,

  // Cardinality Constraints
  'http://www.w3.org/ns/shacl#MinCountConstraintComponent': MinCountConstraintCard,
  'http://www.w3.org/ns/shacl#MaxCountConstraintComponent': MaxCountConstraintCard,

  // Value Range Constraints
  'http://www.w3.org/ns/shacl#MinInclusiveConstraintComponent': MinInclusiveConstraintCard,
  'http://www.w3.org/ns/shacl#MaxInclusiveConstraintComponent': MaxInclusiveConstraintCard,
  'http://www.w3.org/ns/shacl#MinExclusiveConstraintComponent': MinInclusiveConstraintCard, // Reuse MinInclusive for now
  'http://www.w3.org/ns/shacl#MaxExclusiveConstraintComponent': MaxInclusiveConstraintCard, // Reuse MaxInclusive for now

  // String-Based Constraints
  'http://www.w3.org/ns/shacl#MinLengthConstraintComponent': MinLengthConstraintCard,
  'http://www.w3.org/ns/shacl#MaxLengthConstraintComponent': MaxLengthConstraintCard,
  'http://www.w3.org/ns/shacl#PatternConstraintComponent': PatternConstraintCard,
  'http://www.w3.org/ns/shacl#LanguageInConstraintComponent': LanguageInConstraintCard,
  'http://www.w3.org/ns/shacl#UniqueLangConstraintComponent': UniqueLangConstraintCard,

  // Property Pair Constraints
  'http://www.w3.org/ns/shacl#EqualsConstraintComponent': EqualsConstraintCard,
  'http://www.w3.org/ns/shacl#DisjointConstraintComponent': DisjointConstraintCard,
  'http://www.w3.org/ns/shacl#LessThanConstraintComponent': LessThanConstraintCard,
  'http://www.w3.org/ns/shacl#LessThanOrEqualsConstraintComponent': LessThanOrEqualsConstraintCard,

  // Logical Constraints
  'http://www.w3.org/ns/shacl#NotConstraintComponent': NotConstraintCard,
  'http://www.w3.org/ns/shacl#AndConstraintComponent': AndConstraintCard,
  'http://www.w3.org/ns/shacl#OrConstraintComponent': OrConstraintCard,
  'http://www.w3.org/ns/shacl#XoneConstraintComponent': XoneConstraintCard,

  // Shape-based & Property Constraints
  'http://www.w3.org/ns/shacl#NodeConstraintComponent': NodeConstraintCard,
  'http://www.w3.org/ns/shacl#QualifiedValueShapeConstraintComponent': QualifiedValueShapeConstraintCard,
  'http://www.w3.org/ns/shacl#ClosedConstraintComponent': ClosedConstraintCard,
  'http://www.w3.org/ns/shacl#HasValueConstraintComponent': HasValueConstraintCard,
  'http://www.w3.org/ns/shacl#InConstraintComponent': InConstraintCard,

  // Advanced Constraints
  'http://www.w3.org/ns/shacl#SPARQLConstraintComponent': SparqlConstraintCard
}

/**
 * Short name mapping for common constraint components
 */
const shortNameMapping = {
  'ClassConstraintComponent': ClassConstraintCard,
  'DatatypeConstraintComponent': DatatypeConstraintCard,
  'NodeKindConstraintComponent': NodeKindConstraintCard,
  'MinCountConstraintComponent': MinCountConstraintCard,
  'MaxCountConstraintComponent': MaxCountConstraintCard,
  'MinInclusiveConstraintComponent': MinInclusiveConstraintCard,
  'MaxInclusiveConstraintComponent': MaxInclusiveConstraintCard,
  'MinExclusiveConstraintComponent': MinInclusiveConstraintCard,
  'MaxExclusiveConstraintComponent': MaxInclusiveConstraintCard,
  'MinLengthConstraintComponent': MinLengthConstraintCard,
  'MaxLengthConstraintComponent': MaxLengthConstraintCard,
  'PatternConstraintComponent': PatternConstraintCard,
  'LanguageInConstraintComponent': LanguageInConstraintCard,
  'UniqueLangConstraintComponent': UniqueLangConstraintCard,
  'EqualsConstraintComponent': EqualsConstraintCard,
  'DisjointConstraintComponent': DisjointConstraintCard,
  'LessThanConstraintComponent': LessThanConstraintCard,
  'LessThanOrEqualsConstraintComponent': LessThanOrEqualsConstraintCard,
  'NotConstraintComponent': NotConstraintCard,
  'AndConstraintComponent': AndConstraintCard,
  'OrConstraintComponent': OrConstraintCard,
  'XoneConstraintComponent': XoneConstraintCard,
  'NodeConstraintComponent': NodeConstraintCard,
  'QualifiedValueShapeConstraintComponent': QualifiedValueShapeConstraintCard,
  'ClosedConstraintComponent': ClosedConstraintCard,
  'HasValueConstraintComponent': HasValueConstraintCard,
  'InConstraintComponent': InConstraintCard,
  'SPARQLConstraintComponent': SparqlConstraintCard
}

/**
 * Get the appropriate Vue component for a constraint type
 *
 * @param {string} constraintComponent - The constraint component URI or short name
 * @returns {Vue.Component} The Vue component for the constraint
 */
export function getConstraintCard(constraintComponent) {
  if (!constraintComponent) {
    return DefaultConstraintCard
  }

  // Try exact URI match first
  if (constraintCardRegistry[constraintComponent]) {
    return constraintCardRegistry[constraintComponent]
  }

  // Try short name match
  const shortName = constraintComponent.includes('#')
    ? constraintComponent.split('#').pop()
    : constraintComponent

  if (shortNameMapping[shortName]) {
    return shortNameMapping[shortName]
  }

  // Try to find a partial match (useful for variations)
  for (const [key, component] of Object.entries(constraintCardRegistry)) {
    if (key.includes(shortName) || shortName.includes(key.split('#').pop())) {
      return component
    }
  }

  for (const [key, component] of Object.entries(shortNameMapping)) {
    if (key.includes(shortName) || shortName.includes(key)) {
      return component
    }
  }

  // Fallback to default card
  console.warn(`Unknown constraint component: ${constraintComponent}. Using default card.`)
  return DefaultConstraintCard
}

/**
 * Register a new constraint card component
 *
 * @param {string} constraintComponent - The constraint component URI or short name
 * @param {Vue.Component} component - The Vue component to register
 */
export function registerConstraintCard(constraintComponent, component) {
  if (constraintComponent.includes('#')) {
    constraintCardRegistry[constraintComponent] = component
  } else {
    shortNameMapping[constraintComponent] = component
  }
}

/**
 * Get all registered constraint types
 *
 * @returns {Array} Array of constraint component URIs
 */
export function getRegisteredConstraints() {
  return Object.keys(constraintCardRegistry)
}

/**
 * Check if a constraint type is registered
 *
 * @param {string} constraintComponent - The constraint component URI or short name
 * @returns {boolean} True if the constraint is registered
 */
export function isConstraintRegistered(constraintComponent) {
  if (!constraintComponent) return false

  if (constraintCardRegistry[constraintComponent]) {
    return true
  }

  const shortName = constraintComponent.includes('#')
    ? constraintComponent.split('#').pop()
    : constraintComponent

  return shortNameMapping[shortName] !== undefined
}

export default {
  getConstraintCard,
  registerConstraintCard,
  getRegisteredConstraints,
  isConstraintRegistered
}