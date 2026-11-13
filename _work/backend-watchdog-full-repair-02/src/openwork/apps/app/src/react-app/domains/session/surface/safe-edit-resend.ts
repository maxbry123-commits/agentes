export type SafeEditResendInput = {
  revertMessageId?: string | undefined;
  abort: () => Promise<unknown>;
  revert: (messageId: string) => Promise<unknown>;
  prompt: () => Promise<void>;
  unrevert: () => Promise<unknown>;
  onUnrevertError?: (error: unknown) => void;
};

/**
 * Keep edit/resend's destructive work inside the send closure. A successful
 * revert is rolled back when the replacement prompt cannot be dispatched.
 */
export async function sendWithRevertRollback(input: SafeEditResendInput): Promise<void> {
  const revertMessageId = input.revertMessageId?.trim();
  if (!revertMessageId) {
    await input.prompt();
    return;
  }

  await input.abort();
  await input.revert(revertMessageId);
  try {
    await input.prompt();
  } catch (error) {
    try {
      await input.unrevert();
    } catch (unrevertError) {
      input.onUnrevertError?.(unrevertError);
    }
    throw error;
  }
}
