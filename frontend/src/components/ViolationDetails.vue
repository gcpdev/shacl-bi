<template>
  <div>
    <h2>Violation Details</h2>
    <div v-if="violation">
      <pre>{{ violation }}</pre>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  props: ['id'],
  data() {
    return {
      violation: null,
    };
  },
  created() {
    this.fetchViolationDetails();
  },
  methods: {
    async fetchViolationDetails() {
      try {
        const response = await axios.get(`/api/violations/${this.id}`);
        this.violation = response.data;
      } catch (error) {
        console.error(error);
      }
    },
  },
};
</script>
