/**
 * @deprecated This monolithic client is being split into domain modules under `src/api/`.
 * Please migrate your imports:
 *
 *   Before: import { apiUnternehmen } from '@/api/client'
 *   After:  import { apiCompanies } from '@/api/companies'
 *
 * All existing exports remain functional for backward compatibility.
 */

export { request, ApiError } from './core';
export * from './types';

// Domain modules (re-exported with legacy German names for compat)
export { apiAuth } from './auth';
export { apiCompanies as apiUnternehmen } from './companies';
export { apiAgents as apiExperten, apiPermissions } from './agents';
export { apiTasks as apiAufgaben } from './tasks';
export { apiProjects as apiProjekte } from './projects';
export { apiApprovals as apiGenehmigungen } from './approvals';
export { apiDashboard } from './dashboard';
export { apiCosts as apiKosten } from './costs';
export { apiActivity as apiAktivitaet } from './activity';
export { apiSettings as apiEinstellungen } from './settings';
export { apiBudget } from './budget';
export { apiPortability } from './portability';
export { apiDependencies } from './dependencies';
export { apiMemberships } from './memberships';
export { apiChannels } from './channels';
export { apiNodes } from './nodes';
export { apiHealth } from './health';
