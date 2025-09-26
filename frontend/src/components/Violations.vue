<template>
  <div>
    <h2>Violations</h2>
    <button @click="sortViolations('severity', 'asc')">Sort by Severity (asc)</button>
    <button @click="sortViolations('severity', 'desc')">Sort by Severity (desc)</button>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Severity</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="violation in violations" :key="violation.id">
          <td><router-link :to="`/violations/${violation.id}`">{{ violation.id }}</router-link></td>
          <td>{{ violation.severity }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      violations: [],
    };
  },
  created() {
    this.fetchViolations();
  },
  methods: {
    async fetchViolations(sortBy = 'severity', order = 'desc') {
      try {
        const response = await axios.get(`/api/violations?sort_by=${sortBy}&order=${order}`);
        this.violations = response.data;
      } catch (error) {
        console.error(error);
      }
    },
    sortViolations(sortBy, order) {
      this.fetchViolations(sortBy, order);
    },
  },
};
</script>
