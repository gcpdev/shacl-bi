
import { defineStore } from 'pinia';

export const useStore = defineStore('main', {
  state: () => ({
    phoenixMode: false,
    directoryPath: '',
    shapesGraphName: '',
    validationReportName: '',
    dataGraphFile: null,
    shapesGraphFile: null,
    mainContentData: null,
  }),
  actions: {
    setPhoenixMode(mode) {
      this.phoenixMode = mode;
    },
    setDirectoryPath(path) {
      this.directoryPath = path;
    },
    setShapesGraphName(name) {
      this.shapesGraphName = name;
    },
    setValidationReportName(name) {
      this.validationReportName = name;
    },
    setDataGraphFile(file) {
      this.dataGraphFile = file;
    },
    setShapesGraphFile(file) {
      this.shapesGraphFile = file;
    },
    setMainContentData(data) {
      this.mainContentData = data;
    },
    setShaclDashboardData(data) {
      this.directoryPath = data.directoryPath;
      this.shapesGraphName = data.shapesGraphName;
      this.validationReportName = data.validationReportName;
    },
  },
});
