import { useCallback, useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/shared/hooks';
import { updateSettingsPatch, AppSettings } from '@/shared/state/settingsSlice';
import { fetchModels } from '@/shared/state/modelsSlice';
import { useThemeMode, useThemeAccent } from '@/shared/styles/ThemeContext';

export interface SettingsForm {
  form: AppSettings;
  setForm: React.Dispatch<React.SetStateAction<AppSettings>>;
  saveError: boolean;
  dismissSaveError: () => void;
  /** Push whatever is still inside the debounce window; the host calls this on close so nothing is lost. */
  flushPendingSave: () => void;
}

// Apply-on-change settings editing (System Settings style), shared by both hosts of the settings UI: the modal and the on-canvas window. `active` gates every effect so an unmounted-but-alive host never saves.
export function useSettingsForm(active: boolean): SettingsForm {
  const dispatch = useAppDispatch();
  const settings = useAppSelector((s) => s.settings.data);
  const loaded = useAppSelector((s) => s.settings.loaded);
  const { setMode: setThemeMode } = useThemeMode();
  const { setAccent, setGradient } = useThemeAccent();
  const [form, setForm] = useState<AppSettings>({ ...settings });
  const [saveError, setSaveError] = useState(false);

  // Re-seed form on user change; otherwise the dirty detector falsely lights up Save/Discard.
  useEffect(() => {
    setForm({ ...settings });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.user_id, settings.user_email]);

  // Sync form on open + first load only; including `settings` in deps wipes in-flight edits on background fetches (issue #25). baseline = the snapshot the user started editing from, so we can tell user edits apart from fields the backend changed underneath us (OAuth connects, free-trial mints).
  const baselineRef = useRef<AppSettings>(settings);
  useEffect(() => {
    if (active && loaded) {
      setForm({ ...settings });
      baselineRef.current = settings;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, loaded]);

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlight = useRef(false);

  // Only the fields the user touched ride on top of the LATEST settings; submitting the whole stale form would clobber background updates and ping-pong with server-owned fields.
  const buildSubmit = useCallback((): { touched: string[]; patch: Partial<AppSettings> } | null => {
    const base = baselineRef.current as unknown as Record<string, unknown>;
    const f = form as unknown as Record<string, unknown>;
    const touched = Array.from(new Set([...Object.keys(base), ...Object.keys(f)]))
      .filter((k) => JSON.stringify(f[k]) !== JSON.stringify(base[k]));
    if (touched.length === 0) return null;
    // Send ONLY what the user changed; the server merges it onto fresh state, so we never re-send (and clobber) a field something else updated underneath us.
    const patch: Record<string, unknown> = {};
    for (const k of touched) patch[k] = f[k];
    return { touched, patch: patch as Partial<AppSettings> };
  }, [form]);

  // Theme is local UI state; apply it the moment the toggle flips, the debounced save persists it.
  useEffect(() => {
    if (active && loaded) setThemeMode(form.theme);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.theme]);

  // Accent + gradient apply live too, same contract as theme: instant paint, debounced persist.
  useEffect(() => {
    if (active && loaded) {
      setAccent(form.accent_color ?? null);
      setGradient(form.accent_gradient ?? null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.accent_color, form.accent_gradient]);

  // Text size applies live too; AppShell re-applies the persisted value on every boot.
  useEffect(() => {
    if (active && loaded) {
      const scale = Math.min(1.4, Math.max(0.8, form.ui_font_scale ?? 1));
      document.documentElement.style.fontSize = `${scale * 100}%`;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.ui_font_scale]);

  useEffect(() => {
    if (!active || !loaded) return;
    if (!buildSubmit()) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      // A save already in flight will update `settings` when it lands, re-running this effect to pick up whatever is still unsaved.
      if (inFlight.current) return;
      const payload = buildSubmit();
      if (!payload) return;
      inFlight.current = true;
      try {
        await dispatch(updateSettingsPatch(payload.patch)).unwrap();
        // Absorb the saved edits so they stop counting as touched (prevents re-save loops).
        const nextBase = { ...baselineRef.current } as Record<string, unknown>;
        for (const k of payload.touched) nextBase[k] = (form as unknown as Record<string, unknown>)[k];
        baselineRef.current = nextBase as unknown as AppSettings;
        dispatch(fetchModels());
      } catch {
        setSaveError(true);
      } finally {
        inFlight.current = false;
      }
    }, 900);
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, [form, active, loaded, settings, dispatch, buildSubmit]);

  const flushPendingSave = useCallback(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    const payload = loaded ? buildSubmit() : null;
    if (!payload) return;
    // Refetch only AFTER the patch lands, or it races the save and reads the pre-change list (stale Haiku until you reopen Settings). Not awaited, so the host still closes instantly.
    dispatch(updateSettingsPatch(payload.patch))
      .unwrap()
      .then(() => dispatch(fetchModels()))
      .catch(() => {});
    baselineRef.current = form;
  }, [dispatch, form, loaded, buildSubmit]);

  // Esc, backdrop click or a closing window unmounts the UI without touching the close button, so flush there too or an edit inside the 900ms debounce dies with the host.
  const flushRef = useRef(flushPendingSave);
  useEffect(() => { flushRef.current = flushPendingSave; }, [flushPendingSave]);
  useEffect(() => () => flushRef.current(), []);

  const dismissSaveError = useCallback(() => setSaveError(false), []);

  return { form, setForm, saveError, dismissSaveError, flushPendingSave };
}
