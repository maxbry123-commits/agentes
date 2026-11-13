import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { API_BASE } from '@/shared/config';

const API = `${API_BASE}/workflows`;

export interface MissedRunItem {
  id: string;
  workflow_id: string;
  workflow_title: string;
  workflow_icon: string;
  /** ISO instant the fire was supposed to happen. */
  scheduled_for: string;
}

interface State {
  items: MissedRunItem[];
  loading: boolean;
  toastOpen: boolean;
}

const initialState: State = {
  items: [],
  loading: false,
  toastOpen: false,
};

export const fetchMissedRuns = createAsyncThunk('missedRuns/fetch', async () => {
  const res = await fetch(`${API}/missed`);
  const data = await res.json();
  return data.missed as MissedRunItem[];
});

export const runMissedRuns = createAsyncThunk('missedRuns/run', async (ids: string[]) => {
  await fetch(`${API}/missed/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  });
  return ids;
});

export const dismissMissedRuns = createAsyncThunk('missedRuns/dismiss', async (ids: string[]) => {
  await fetch(`${API}/missed/dismiss`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  });
  return ids;
});

const missedRunsSlice = createSlice({
  name: 'missedRuns',
  initialState,
  reducers: {
    hideMissedRunsToast(state) {
      state.toastOpen = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMissedRuns.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchMissedRuns.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload || [];
        state.toastOpen = (action.payload?.length ?? 0) > 0;
      })
      .addCase(fetchMissedRuns.rejected, (state) => {
        state.loading = false;
      });
    // Both run and dismiss remove the acted-on ids from the list.
    for (const thunk of [runMissedRuns, dismissMissedRuns]) {
      builder.addCase(thunk.fulfilled, (state, action) => {
        const gone = new Set(action.payload);
        state.items = state.items.filter((m) => !gone.has(m.id));
      });
    }
  },
});

export const { hideMissedRunsToast } = missedRunsSlice.actions;

export default missedRunsSlice.reducer;
