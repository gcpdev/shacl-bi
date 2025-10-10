<template>
  <div class="landing-page flex items-center justify-center min-h-screen bg-gray-100" :class="{ 'phoenix-mode': phoenixMode }">
    <div class="card w-full max-w-lg p-8 space-y-6 bg-white rounded-lg shadow-md">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-800">SHACL-BI</h1>
        <p class="mt-2 text-gray-600">Welcome! Please select your mode.</p>
      </div>

      <v-switch v-model="phoenixMode" label="PHOENIX Mode" color="primary"></v-switch>

      <form v-if="!phoenixMode" @submit.prevent="goToHome">
        <div class="space-y-4">
          <v-text-field
            v-model="directoryPath"
            label="Directory Path"
            placeholder="Enter directory path"
            outlined
            dense
          ></v-text-field>
          <v-text-field
            v-model="shapesGraphName"
            label="Shapes Graph Name"
            placeholder="Enter shapes graph name"
            outlined
            dense
          ></v-text-field>
          <v-text-field
            v-model="validationReportName"
            label="Validation Report Name"
            placeholder="Enter validation report name"
            outlined
            dense
          ></v-text-field>
        </div>
        <v-btn type="submit" class="w-full mt-6" color="primary" large>ENTER</v-btn>
      </form>

      <form v-if="phoenixMode" @submit.prevent="validateAndGoToHome">
        <div class="space-y-4">
          <v-file-input v-model="dataGraphFile" label="Data Graph File" outlined dense></v-file-input>
          <v-file-input v-model="shapesGraphFile" label="Shapes Graph File" outlined dense></v-file-input>
        </div>
        <v-btn type="submit" class="w-full mt-6" color="primary" large>VALIDATE</v-btn>
      </form>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'pinia';
import { useStore } from '@/store';

export default {
  data() {
    return {
      phoenixMode: false,
      directoryPath: '',
      shapesGraphName: '',
      validationReportName: '',
      dataGraphFile: null,
      shapesGraphFile: null,
    };
  },
  methods: {
    ...mapActions(useStore, ['setMainContentData', 'setShaclDashboardData']),
    goToHome() {
      // Logic to navigate to the home page for SHACL-Dashboard mode
      this.setShaclDashboardData({
        directoryPath: this.directoryPath,
        shapesGraphName: this.shapesGraphName,
        validationReportName: this.validationReportName,
      });
      this.$router.push({ name: 'Home' });
    },
    validateAndGoToHome() {
      if (!this.dataGraphFile || !this.shapesGraphFile) {
        alert('Please select both data graph and shapes graph files.');
        return;
      }

      console.log('Starting validation...');
      console.log('Data file:', this.dataGraphFile);
      console.log('Shapes file:', this.shapesGraphFile);

      const formData = new FormData();
      formData.append('dataGraphFile', this.dataGraphFile);
      formData.append('shapesGraphFile', this.shapesGraphFile);

      fetch('/api/validate-phoenix', {
        method: 'POST',
        body: formData,
      })
        .then(response => {
          console.log('Response received:', response);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Validation response:', data);
          if (data.error) {
            console.error('Validation failed:', data.error);
            alert(`Validation failed: ${data.error}`);
          } else {
            console.log('Validation successful:', data);
            console.log('Setting main content data and redirecting...');
            this.setMainContentData(data);
            this.$router.push('/dashboard');
          }
        })
        .catch(error => {
          console.error('Error during validation:', error);
          alert(`Error during validation: ${error.message}`);
        });
    },
  },
};
</script>

<style scoped>
.landing-page {
  font-family: 'Inter', sans-serif;
}

.phoenix-mode .card {
  border: 2px solid var(--primary);
}

.phoenix-mode {
  background-color: #f0f8ff;
}
</style>