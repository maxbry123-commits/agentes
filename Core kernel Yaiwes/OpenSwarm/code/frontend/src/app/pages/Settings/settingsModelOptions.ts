import { useMemo } from 'react';
import { useAppSelector } from '@/shared/hooks';

// Brand colors for provider group headers; mirrors ChatInput picker.
export const PROVIDER_COLORS: Record<string, string> = {
  anthropic: '#E8927A',
  openai: '#74AA9C',
  google: '#4285F4',
  gemini: '#4285F4',
  xai: '#8B949E',
  meta: '#0866FF',
  deepseek: '#4D6BFE',
  mistral: '#FF7000',
  qwen: '#A974FF',
  cohere: '#FF7759',
};

export const OPENSWARM_GRADIENT =
  'linear-gradient(135deg, #8FB3FF 0%, #E56BC4 45%, #FFA85C 100%)';

// Shown only in the brief window before the live model list loads from the backend. Keep the flagship current so the default-model dropdown isn't stale.
const DEFAULT_MODEL_FALLBACK = [
  { value: 'opus-5', label: 'Claude Opus 5' },
  { value: 'opus-4-8', label: 'Claude Opus 4.8' },
  { value: 'sonnet', label: 'Claude Sonnet 4.6' },
  { value: 'opus', label: 'Claude Opus 4.6' },
  { value: 'haiku', label: 'Claude Haiku 4.5' },
];

export interface ModelOptions {
  grouped: Record<string, Array<{ value: string; label: string }>>;
  flat: Array<{ value: string; label: string; provider: string }>;
}

// Model picker source matches the in-session ChatInput picker, so Settings reflects connected providers.
export function useModelOptions(): ModelOptions {
  const connectionMode = useAppSelector((s) => s.settings.data.connection_mode);
  const defaultModel = useAppSelector((s) => s.settings.data.default_model);
  const modelsByProvider = useAppSelector((s) => s.models.byProvider);
  const modelsLoaded = useAppSelector((s) => s.models.loaded);

  return useMemo(() => {
    if (!modelsLoaded || Object.keys(modelsByProvider).length === 0) {
      const key = connectionMode === 'openswarm-pro' ? 'OpenSwarm Pro' : 'Anthropic';
      return {
        grouped: { [key]: DEFAULT_MODEL_FALLBACK },
        flat: DEFAULT_MODEL_FALLBACK.map((m) => ({ ...m, provider: key })),
      };
    }
    const grouped: Record<string, Array<{ value: string; label: string }>> = {};
    const flat: Array<{ value: string; label: string; provider: string }> = [];
    for (const [prov, models] of Object.entries(modelsByProvider)) {
      grouped[prov] = models.map((m) => ({ value: m.value, label: m.label }));
      for (const m of models) flat.push({ value: m.value, label: m.label, provider: prov });
    }
    // Guarantee the currently-selected default is always a valid option, even if the live list doesn't carry it (custom/OpenRouter value, or a stored model not in the current registry). Without this the dropdown gets an MUI "out-of-range value" warning and renders blank.
    if (defaultModel && !flat.some((m) => m.value === defaultModel)) {
      const other = 'Other';
      (grouped[other] ||= []).push({ value: defaultModel, label: defaultModel });
      flat.push({ value: defaultModel, label: defaultModel, provider: other });
    }
    return { grouped, flat };
  }, [modelsByProvider, modelsLoaded, connectionMode, defaultModel]);
}
