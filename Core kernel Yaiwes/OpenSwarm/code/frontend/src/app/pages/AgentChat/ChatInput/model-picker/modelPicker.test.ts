// Run: npx tsx --test frontend/src/app/pages/AgentChat/ChatInput/model-picker/modelPicker.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { orderGroupsByTier, groupTier } from './modelPicker.ts';

test('groups order subscriptions, then API keys, then routers, never interleaved', () => {
  const grouped = {
    'OpenRouter · DeepSeek': [{ billing_kind: 'router' }],
    'OpenAI': [{ billing_kind: 'api_key' }],
    'Anthropic': [{ billing_kind: 'subscription' }],
    'Google': [{ billing_kind: 'subscription' }, { billing_kind: 'api_key' }],
  };
  const ordered = orderGroupsByTier(grouped).map(([prov, , tier]) => `${prov}:${tier}`);
  assert.deepEqual(ordered, [
    'Anthropic:subscription',
    'Google:subscription',
    'OpenAI:api_key',
    'OpenRouter · DeepSeek:router',
  ]);
});

test('a mixed sub+api group sorts as a subscription; router prefixes and dot-separators are routers', () => {
  assert.equal(groupTier('Google', [{ billing_kind: 'api_key' }, { billing_kind: 'subscription' }]), 'subscription');
  assert.equal(groupTier('OpenRouter · Meta', [{ billing_kind: 'router' }]), 'router');
  assert.equal(groupTier('Some · Vendor', [{ billing_kind: 'api_key' }]), 'router');
  assert.equal(groupTier('OpenAI', [{ billing_kind: 'api_key' }]), 'api_key');
});
