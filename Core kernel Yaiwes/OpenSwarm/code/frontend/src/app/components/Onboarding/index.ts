// Public surface for the Onboarding v2 system. AppShell mounts <OnboardingRoot/> once; everything else is internal.

export { default as OnboardingRoot } from './OnboardingRoot';
export { onboardingDirector } from './OnboardingDirector';
export { onboardingBus } from './eventBus';
export type { OnboardingEvent } from './eventBus';
export { S as OnboardingSelectors } from './selectors';
export { useOnboardingProgress } from './hooks/useOnboardingProgress';
