// Endpointing: decide when the speaker has finished so tap-to-dictate stops itself instead of
// recording (and transcribing) the gap between "done talking" and "remembered to press again".
// Energy based on purpose: the mic stream is already float PCM in hand, and a Silero ONNX model
// would mean shipping onnxruntime into the renderer for a decision this cheap.
//
// Every constant is borrowed from shipping code rather than guessed: the 0.004 RMS speech floor is
// TypeWhisper's, the 0.02 peak companion is openwhispr's, and the 1400ms silence window with a
// 400ms minimum-speech guard is what Whispering's Silero endpointer uses.
//
// The peak test is the load-bearing half. Speech is spiky and room tone is flat, so RMS alone calls
// a noisy room "talking" forever and the recording never ends; requiring a real peak separates them.

const FRAME_MS = 20;
const SPEECH_RMS = 0.004;
const SPEECH_PEAK = 0.02;
const MIN_SPEECH_MS = 400;
const SILENCE_HOLD_MS = 1400;
const MAX_UTTERANCE_MS = 120_000;

export type SilenceVerdict = 'listening' | 'ended' | 'too-long';

export interface SilenceDetector {
  // Feed every captured chunk; any verdict other than 'listening' means stop recording now.
  push(samples: Float32Array): SilenceVerdict;
}

export function createSilenceDetector(sampleRate: number): SilenceDetector {
  const frameSize = Math.max(1, Math.round((sampleRate * FRAME_MS) / 1000));
  let elapsedMs = 0;
  let speechMs = 0;
  let silenceMs = 0;
  // Frames straddle chunk boundaries, so carry the partial frame across pushes; dropping the
  // remainder would make every constant here quietly run ~6% long.
  let sumSquares = 0;
  let peak = 0;
  let framed = 0;

  return {
    push(samples: Float32Array): SilenceVerdict {
      for (let i = 0; i < samples.length; i++) {
        const v = samples[i];
        sumSquares += v * v;
        const mag = v < 0 ? -v : v;
        if (mag > peak) peak = mag;
        if (++framed < frameSize) continue;
        const rms = Math.sqrt(sumSquares / frameSize);
        const isSpeech = rms >= SPEECH_RMS && peak >= SPEECH_PEAK;
        sumSquares = 0;
        peak = 0;
        framed = 0;
        elapsedMs += FRAME_MS;
        if (elapsedMs >= MAX_UTTERANCE_MS) return 'too-long';
        if (isSpeech) {
          speechMs += FRAME_MS;
          silenceMs = 0;
        } else if (speechMs >= MIN_SPEECH_MS) {
          // Only count quiet AFTER real speech, so an empty room never ends a recording by itself.
          silenceMs += FRAME_MS;
        }
        if (speechMs >= MIN_SPEECH_MS && silenceMs >= SILENCE_HOLD_MS) return 'ended';
      }
      return 'listening';
    },
  };
}
