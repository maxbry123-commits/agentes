/**
 * Run: node --test frontend/src/app/pages/Dashboard/desktop/helpSearch.test.ts
 *
 * The offline answer path. Every case below is a ranking bug caught live in the real panel: a
 * help answer that is confidently the WRONG surface is worse than no answer, so they stay pinned.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { searchHelp, type HelpKnowledge } from './helpSearch.ts';

const KNOWLEDGE: HelpKnowledge = {
  system_prompt: 'x',
  app_version: '1.6.0',
  known_issues: [],
  shortcuts: [
    { keys: '⌘L', action: 'Open the new-chat composer' },
    { keys: '⌘⇧D', action: 'Start or stop voice dictation' },
    { keys: '⌘K', action: 'Search everything, across all dashboards' },
    { keys: '⌘F', action: 'Find cards on this canvas; inside a browser card it finds text on the page' },
    { keys: '⌘⇧T', action: 'Reopen the card you just closed' },
  ],
  topics: [
    {
      id: 'applications',
      title: 'Applications, your app library',
      where: 'The grid icon at the very bottom of the left dock.',
      body: 'Lists every app you have built or imported.',
      keywords: ['applications', 'apps', 'library', 'grid'],
    },
    {
      id: 'apps',
      title: 'Building apps',
      where: 'Ask any agent chat.',
      body: 'Ask an agent for a tool and it calls CreateApp.',
      keywords: ['app', 'build', 'create'],
    },
    {
      id: 'workflows',
      title: 'Workflows and scheduled tasks',
      where: 'The repeating-calendar icon in the left dock.',
      body: 'Runs agent steps on a schedule, for example every weekday at 9am.',
      keywords: ['workflow', 'schedule', 'task', 'recurring'],
    },
    {
      id: 'settings',
      title: 'Settings',
      where: 'The gear icon in the left dock.',
      body: 'Theme, accent color, and text size live under Appearance.',
      keywords: ['settings', 'theme', 'appearance'],
    },
  ],
};

const top = (q: string): string => searchHelp(KNOWLEDGE, q)[0]?.title ?? '(none)';

test('"where are my apps" leads with the app library, not the app builder', () => {
  assert.equal(top('where are my apps'), 'Applications, your app library');
});

test('a shortcut question leads with the right key', () => {
  assert.equal(top('reopen a closed card'), '⌘⇧T');
});

test('stopwords never pull in a shortcut: "the" must not match "Open the new-chat composer"', () => {
  assert.equal(top('change the theme'), 'Settings');
  assert.ok(!searchHelp(KNOWLEDGE, 'change the theme').some((m) => m.title === '⌘L'));
});

test('partial words never match: "every" must not hit "Search everything"', () => {
  assert.equal(top('schedule a task every weekday'), 'Workflows and scheduled tasks');
  assert.ok(!searchHelp(KNOWLEDGE, 'schedule a task every weekday').some((m) => m.title === '⌘K'));
});

test('plurals still match their singular keyword', () => {
  assert.equal(top('cards'), '⌘F');
});

test('no knowledge, an empty query, or pure stopwords return nothing rather than noise', () => {
  assert.deepEqual(searchHelp(null, 'apps'), []);
  assert.deepEqual(searchHelp(KNOWLEDGE, ''), []);
  assert.deepEqual(searchHelp(KNOWLEDGE, 'how do i'), []);
});

test('a question we have no answer for returns nothing, never a bad guess', () => {
  assert.deepEqual(searchHelp(KNOWLEDGE, 'kubernetes ingress'), []);
});
