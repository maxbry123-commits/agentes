import { request } from './core';

export const apiPortability = {
  exportieren: (uid: string) => request<any>(`/companies/${uid}/export`),
  importPreview: (uid: string, manifest: any) =>
    request<{ unternehmenName: string; agentenCount: number; aufgabenCount: number; skillsCount: number; collisions: Array<{ name: string; typ: string }> }>(
      `/companies/${uid}/import/preview`, { method: 'POST', body: JSON.stringify(manifest) }),
  importieren: (uid: string, manifest: any, options: any) =>
    request<{ success: boolean; agentsImported: number; tasksImported: number; errors: string[] }>(
      `/companies/${uid}/import`, { method: 'POST', body: JSON.stringify({ manifest, options }) }),
};
