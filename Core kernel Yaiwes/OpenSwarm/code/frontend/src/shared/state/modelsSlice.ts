import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { API_BASE } from '@/shared/config';

const AGENTS_API = `${API_BASE}/agents`;

export interface ModelOption {
  value: string;
  label: string;
  version?: string;
  context_window: number;
  reasoning?: boolean;
  input_cost_per_1m?: number;
  output_cost_per_1m?: number;
  is_free?: boolean;
  max_completion_tokens?: number | null;
  /** (intelligence, speed, cost), 1-5. */
  tiers?: [number, number, number];
  billing_kind?: 'paid' | 'subscription' | 'free' | 'api_key';
}

interface ModelsState {
  byProvider: Record<string, ModelOption[]>;
  loaded: boolean;
  failed: boolean;
}

const initialState: ModelsState = {
  byProvider: {},
  loaded: false,
  failed: false,
};

export const fetchModels = createAsyncThunk('models/fetchModels', async () => {
  const res = await fetch(`${AGENTS_API}/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  const data = await res.json();
  const models = data.models || data;
  return models as Record<string, ModelOption[]>;
});

const modelsSlice = createSlice({
  name: 'models',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchModels.fulfilled, (state, action) => {
        state.byProvider = action.payload;
        state.loaded = true;
      })
      .addCase(fetchModels.rejected, (state) => {
        // Mark loaded even on failure so callers fall back to hardcoded options.
        state.loaded = true;
        // ...but remember it FAILED: a boot-race miss used to read as "loaded with no models" and lit the red banner on a fully configured install (ENG-207).
        state.failed = true;
      })
      .addCase(fetchModels.pending, (state) => {
        state.failed = false;
      });
  },
});

export default modelsSlice.reducer;
