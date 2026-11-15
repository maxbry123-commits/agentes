import React, { useState, useEffect, useRef, useCallback } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import InputBase from '@mui/material/InputBase';
import Tooltip from '@mui/material/Tooltip';
import SendIcon from '@mui/icons-material/Send';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import PanToolOutlinedIcon from '@mui/icons-material/PanToolOutlined';
import StopIcon from '@mui/icons-material/Stop';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { AgentSession, stopAgent, handleApproval } from '@/shared/state/agentsSlice';
import { useAppDispatch, useAppSelector } from '@/shared/hooks';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';

interface Props {
  session: AgentSession;
  browserWidth: number;
  browserHeight: number;
}

// The action log this overlay used to carry is gone on purpose (ENG-201, Eric's call): the live
// page IS the progress display, so the overlay is now just a slim status pill with a Stop button,
// or the full intervention card when the model itself asked for help.
const BrowserAgentOverlay: React.FC<Props> = ({ session, browserWidth, browserHeight }) => {
  const c = useClaudeTokens();
  const dispatch = useAppDispatch();
  const [confirmStop, setConfirmStop] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [showSkipInput, setShowSkipInput] = useState(false);
  const [skipReason, setSkipReason] = useState('');
  const confirmTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fadeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Parent session may send another BrowserAgent call; treat overlay as done only when both sub-task and parent are terminal.
  const parentStatus = useAppSelector((state) => {
    if (!session.parent_session_id) return null;
    return state.agents.sessions[session.parent_session_id]?.status ?? null;
  });
  const parentStillActive = parentStatus === 'running' || parentStatus === 'waiting_approval';

  const isRunning = session.status === 'running' || session.status === 'waiting_approval';
  const browserDone = session.status === 'completed' || session.status === 'error' || session.status === 'stopped';
  // Only fade+hide when parent is finished too; otherwise show a "waiting" state between sub-tasks.
  const isDone = browserDone && !parentStillActive;

  const intervention = session.pending_approvals?.find(
    (a) => a.tool_name === 'RequestHumanIntervention',
  );
  const interventionProblem = (intervention?.tool_input as any)?.problem || 'The browser agent needs your help.';
  const interventionInstruction = (intervention?.tool_input as any)?.instruction || '';

  const prevSessionId = useRef(session.id);
  useEffect(() => {
    if (session.id !== prevSessionId.current) {
      prevSessionId.current = session.id;
      setFadeOut(false);
      setHidden(false);
      setConfirmStop(false);
      setShowSkipInput(false);
      setSkipReason('');
    }
  }, [session.id]);

  useEffect(() => {
    if (!intervention) {
      setShowSkipInput(false);
      setSkipReason('');
    }
  }, [intervention]);

  useEffect(() => {
    if (isDone) {
      fadeTimer.current = setTimeout(() => setFadeOut(true), 2000);
    }
    return () => { if (fadeTimer.current) clearTimeout(fadeTimer.current); };
  }, [isDone]);

  useEffect(() => {
    if (fadeOut) {
      hideTimer.current = setTimeout(() => setHidden(true), 400);
    }
    return () => { if (hideTimer.current) clearTimeout(hideTimer.current); };
  }, [fadeOut]);

  const handleStop = useCallback(() => {
    if (!confirmStop) {
      setConfirmStop(true);
      confirmTimer.current = setTimeout(() => setConfirmStop(false), 3000);
      return;
    }
    if (confirmTimer.current) clearTimeout(confirmTimer.current);
    setConfirmStop(false);
    dispatch(stopAgent({ sessionId: session.id }));
  }, [confirmStop, dispatch, session.id]);

  useEffect(() => {
    return () => { if (confirmTimer.current) clearTimeout(confirmTimer.current); };
  }, []);

  const accentColor = c.accent.primary;

  if (hidden) return null;

  return (
    <Box
      onPointerDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      sx={{
        position: 'absolute',
        bottom: 12,
        right: 12,
        width: intervention ? Math.min(340, browserWidth - 24) : 'auto',
        maxWidth: browserWidth - 24,
        ...(intervention ? { maxHeight: Math.min(320, browserHeight - 24) } : {}),
        zIndex: 18,
        borderRadius: intervention ? '12px' : '999px',
        bgcolor: 'rgba(15, 15, 15, 0.88)',
        backdropFilter: 'blur(16px)',
        border: `1px solid ${intervention ? 'rgba(245,158,11,0.4)' : `${accentColor}30`}`,
        boxShadow: `0 4px 24px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)`,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'width 0.25s ease, opacity 0.4s ease',
        opacity: fadeOut ? 0 : isDone ? 0.7 : 1,
        animation: 'overlay-enter 0.3s ease-out',
        '@keyframes overlay-enter': {
          '0%': { opacity: 0, transform: 'translateY(8px) scale(0.95)' },
          '100%': { opacity: 1, transform: 'translateY(0) scale(1)' },
        },
      }}
    >
      {/* Header (the whole pill, when there is no intervention) */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.75,
          px: 1.25,
          py: 0.75,
          borderBottom: intervention ? `1px solid rgba(255,255,255,0.08)` : 'none',
          flexShrink: 0,
        }}
      >
        {intervention
          ? <PanToolOutlinedIcon sx={{ fontSize: 14, color: '#f59e0b' }} />
          : <SmartToyOutlinedIcon sx={{ fontSize: 14, color: accentColor }} />
        }

        {(isRunning || (browserDone && parentStillActive)) && !intervention && (
          <Box
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              bgcolor: accentColor,
              flexShrink: 0,
              animation: 'overlay-dot-pulse 1.4s ease-in-out infinite',
              '@keyframes overlay-dot-pulse': {
                '0%, 100%': { opacity: 0.4, transform: 'scale(0.8)' },
                '50%': { opacity: 1, transform: 'scale(1.3)' },
              },
            }}
          />
        )}

        {isDone && session.status === 'completed' && (
          <CheckCircleOutlineIcon sx={{ fontSize: 14, color: '#4ade80' }} />
        )}
        {isDone && session.status === 'error' && (
          <ErrorOutlineIcon sx={{ fontSize: 14, color: '#f87171' }} />
        )}

        <Typography
          sx={{
            fontSize: '0.6875rem',
            fontWeight: 600,
            color: intervention ? '#f59e0b' : 'rgba(255,255,255,0.85)',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {isDone
            ? session.status === 'completed' ? 'Done' : session.status === 'error' ? 'Error' : 'Stopped'
            : intervention ? 'Needs Help'
            : browserDone && parentStillActive ? 'Waiting…'
            : 'Browser Agent'}
        </Typography>

        {isRunning && (
          <Tooltip title={confirmStop ? 'Click again to confirm' : 'Stop'} placement="top">
            <IconButton
              size="small"
              onClick={handleStop}
              sx={{
                p: 0.3,
                color: confirmStop ? '#f87171' : 'rgba(255,255,255,0.5)',
                bgcolor: confirmStop ? 'rgba(248,113,113,0.15)' : 'transparent',
                '&:hover': {
                  color: '#f87171',
                  bgcolor: 'rgba(248,113,113,0.12)',
                },
                transition: 'all 0.15s',
              }}
            >
              <StopIcon sx={{ fontSize: 13 }} />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Body: only the intervention prompt ever needs one */}
      {intervention && (
        <Box sx={{ flex: 1, px: 1.25, py: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
          {/* The run is stopped dead until somebody reads this, so it reads like a headline, not a footnote. */}
          <Typography sx={{ fontSize: '0.8125rem', color: 'rgba(255,255,255,0.92)', fontWeight: 500, lineHeight: 1.45 }}>
            {interventionProblem}
          </Typography>
          {interventionInstruction && (
            <Typography sx={{ fontSize: '0.6875rem', color: 'rgba(255,255,255,0.62)', lineHeight: 1.45 }}>
              {interventionInstruction}
            </Typography>
          )}
          {showSkipInput ? (
            <Box sx={{ display: 'flex', gap: 0.5, mt: 'auto', pt: 0.5, alignItems: 'center' }}>
              <InputBase
                autoFocus
                placeholder="Why? (optional)"
                value={skipReason}
                onChange={(e) => setSkipReason(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    dispatch(handleApproval({ requestId: intervention.id, behavior: 'deny', message: skipReason || 'Skipped by user' }));
                  }
                  if (e.key === 'Escape') setShowSkipInput(false);
                }}
                sx={{
                  flex: 1,
                  fontSize: '0.6875rem',
                  color: 'rgba(255,255,255,0.8)',
                  bgcolor: 'rgba(255,255,255,0.08)',
                  borderRadius: '6px',
                  px: 1,
                  py: 0.3,
                  '& input::placeholder': { color: 'rgba(255,255,255,0.3)' },
                }}
              />
              <IconButton
                size="small"
                onClick={() => dispatch(handleApproval({ requestId: intervention.id, behavior: 'deny', message: skipReason || 'Skipped by user' }))}
                sx={{
                  p: 0.4,
                  color: 'rgba(255,255,255,0.5)',
                  '&:hover': { color: 'rgba(255,255,255,0.8)' },
                }}
              >
                <SendIcon sx={{ fontSize: 13 }} />
              </IconButton>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', gap: 0.75, mt: 'auto', pt: 0.5 }}>
              <Button
                size="small"
                variant="contained"
                onClick={() => dispatch(handleApproval({ requestId: intervention.id, behavior: 'allow' }))}
                sx={{
                  bgcolor: '#f59e0b',
                  '&:hover': { bgcolor: '#d97706' },
                  textTransform: 'none',
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  px: 1.5,
                  py: 0.4,
                  color: '#000',
                }}
              >
                Done, continue
              </Button>
              <Button
                size="small"
                variant="text"
                onClick={() => setShowSkipInput(true)}
                sx={{
                  color: 'rgba(255,255,255,0.4)',
                  '&:hover': { color: 'rgba(255,255,255,0.7)' },
                  textTransform: 'none',
                  fontSize: '0.6875rem',
                  px: 1,
                  py: 0.4,
                  minWidth: 'auto',
                }}
              >
                Skip
              </Button>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default React.memo(BrowserAgentOverlay);
