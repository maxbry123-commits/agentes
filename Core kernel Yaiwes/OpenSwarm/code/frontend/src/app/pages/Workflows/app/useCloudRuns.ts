import { useEffect, useRef, useState } from 'react';
import { fetchCloudRuns } from './cloudApi';
import type { CloudRunsResponse } from './cloudApi';

export type CloudRunsProbe =
  | { phase: 'idle' }
  | { phase: 'checking' }
  | { phase: 'answered'; response: CloudRunsResponse };

/** Run history for the cloud copy. Only asks when the workflow is actually up there, so a
 *  device-only workflow never makes a network call to find out it has no cloud runs. */
export function useCloudRuns(workflowId: string, hosted: boolean, revision: string): CloudRunsProbe {
  const [probe, setProbe] = useState<CloudRunsProbe>({ phase: 'idle' });
  const live = useRef(true);

  useEffect(() => {
    live.current = true;
    return () => { live.current = false; };
  }, []);

  useEffect(() => {
    if (!hosted) {
      setProbe({ phase: 'idle' });
      return;
    }
    setProbe((prev) => (prev.phase === 'answered' ? prev : { phase: 'checking' }));
    fetchCloudRuns(workflowId).then((response) => {
      if (live.current) setProbe({ phase: 'answered', response });
    });
  }, [workflowId, hosted, revision]);

  // A cloud run reports to the cloud, not to us, so a run in flight is the one case worth asking again about. The poll stops itself the moment nothing is live.
  const watching =
    probe.phase === 'answered' &&
    probe.response.state === 'ready' &&
    probe.response.runs.some((r) => r.status === 'pending' || r.status === 'running');

  useEffect(() => {
    if (!hosted || !watching) return undefined;
    const timer = setInterval(() => {
      fetchCloudRuns(workflowId).then((response) => {
        if (live.current) setProbe({ phase: 'answered', response });
      });
    }, 30000);
    return () => clearInterval(timer);
  }, [hosted, watching, workflowId]);

  return probe;
}
