const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  fetchOpenAIData: async () => {
    const result = await ipcRenderer.invoke('fetch-openai-data');
    return result;
  }
});