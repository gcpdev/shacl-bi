<template>
  <div>
    <h2>SHACL Validation</h2>
    <form @submit.prevent="validate">
      <div>
        <label for="data-graph">Data Graph (Turtle):</label>
        <textarea id="data-graph" v-model="dataGraph" rows="10" cols="50"></textarea>
      </div>
      <div>
        <label for="shapes-graph">Shapes Graph (Turtle):</label>
        <textarea id="shapes-graph" v-model="shapesGraph" rows="10" cols="50"></textarea>
      </div>
      <button type="submit">Validate</button>
    </form>
    <div v-if="validationResults">
      <h3>Validation Results</h3>
      <pre>{{ validationResults }}</pre>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      dataGraph: '',
      shapesGraph: '',
      validationResults: null,
    };
  },
  methods: {
    async validate() {
      try {
        const response = await axios.post('/api/validate', {
          data_graph: this.dataGraph,
          shapes_graph: this.shapesGraph,
        });
        this.validationResults = response.data;
        this.$emit('validation-complete', response.data);
      } catch (error) {
        console.error(error);
        this.validationResults = { error: 'An error occurred during validation.' };
      }
    },
  },
};
</script>
