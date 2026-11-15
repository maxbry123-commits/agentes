// OpenCognit API Client — modular exports
//
// New code should import from `src/api/` sub-modules directly.
// Example: import { apiTasks } from '@/api/tasks'
//
// This barrel file is provided for convenience.

export { request, ApiError } from './core';
export * from './types';

export { apiAuth } from './auth';
export { apiCompanies } from './companies';
export { apiAgents, apiPermissions } from './agents';
export { apiTasks } from './tasks';
export { apiProjects } from './projects';
export { apiApprovals } from './approvals';
export { apiDashboard } from './dashboard';
export { apiCosts } from './costs';
export { apiActivity } from './activity';
export { apiSettings } from './settings';
export { apiBudget } from './budget';
export { apiPortability } from './portability';
export { apiDependencies } from './dependencies';
export { apiMemberships } from './memberships';
export { apiChannels } from './channels';
export { apiNodes } from './nodes';
export { apiHealth } from './health';
