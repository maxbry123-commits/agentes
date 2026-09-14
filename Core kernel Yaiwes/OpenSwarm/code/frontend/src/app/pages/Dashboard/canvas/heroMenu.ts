import { Search, Hammer, Globe, Laptop } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { PersonalizedMenu, PersonalizedStarter } from '@/shared/state/settingsSlice';

// The hero's two levels: 4 GENERAL categories (what OpenSwarm can do), each opening 4 SPECIFIC
// starters tailored to this user by onboarding prep. When prep never wrote a menu (older installs,
// prep failure), we bucket whatever personalized starters exist and fill the rest from statics,
// so the drill-in is always complete.

export type HeroCategoryId = 'computer' | 'research' | 'web' | 'build';

export interface HeroCategory {
  id: HeroCategoryId;
  label: string;
  Icon: LucideIcon;
}

export const HERO_CATEGORIES: HeroCategory[] = [
  { id: 'computer', label: 'Do something on my computer', Icon: Laptop },
  { id: 'research', label: 'Research something for me', Icon: Search },
  { id: 'web', label: 'Send an agent to the web', Icon: Globe },
  { id: 'build', label: 'Build me a tiny app', Icon: Hammer },
];

const MENU_SIZE = 4;

const FALLBACK_MENU: PersonalizedMenu = {
  computer: [
    { title: 'Clean up Downloads', prompt: 'Sort my Downloads folder into tidy subfolders. Show me the plan before moving anything.' },
    { title: 'Find my biggest files', prompt: 'Scan my home folder for the largest files and folders and write me a reviewable page listing them with sizes. Do not delete anything.' },
    { title: 'Index my documents', prompt: 'Look through my Documents folder and build one searchable index page listing files by name and date so I can find things fast. Write only the new page.' },
    { title: 'Find duplicate files', prompt: 'Look for duplicate files across my Downloads and Desktop and write a report listing them side by side. Never delete anything without my review.' },
  ],
  research: [
    { title: 'Compare before I buy', prompt: "Ask me what I'm shopping for, then research current options and give me a tight comparison table with dated sources." },
    { title: "What's new in AI", prompt: 'Search the web for the most useful AI tools and model releases from the past month and summarize the ones worth my time, with dated sources.' },
    { title: 'Settle a question', prompt: "Ask me one question I've been meaning to look into, then research it properly and give me a current, sourced answer." },
    { title: 'Plan a weekend trip', prompt: "Ask me where I'd like to go, then research a realistic 3-day itinerary with current prices and opening hours, and turn it into a printable page." },
  ],
  web: [
    { title: 'Find a table tonight', prompt: 'Open OpenTable and find three well-reviewed restaurants near me with availability tonight, compare them, and report back.' },
    { title: 'Watch a flight price', prompt: 'Ask me for a route, then open Google Flights, search it, compare dates and airlines across a few pages, and report the best current options.' },
    { title: 'Best rated near me', prompt: 'Open Google Maps, search for the best-rated coffee shops nearby, read through reviews on a few of them, and tell me which one to try and why.' },
    { title: 'Catch me up on tech', prompt: "Open Hacker News, read through today's top discussions, and give me the three most interesting threads with what people are actually saying." },
  ],
  build: [
    { title: 'Habit tracker', prompt: 'Build me a simple habit tracker app I can use right now.' },
    { title: 'Bill splitter', prompt: 'Build me a tool where I enter a bill total, tip, and the people involved, and it computes exactly who owes what.' },
    { title: 'CSV instant charts', prompt: 'Build me a tool where I paste CSV data and it instantly renders clean charts I can screenshot.' },
    { title: 'Countdown to a date', prompt: 'Build me a countdown page for a date that matters to me; ask me the date and label, then make it look great.' },
  ],
};

function classifyStarter(s: PersonalizedStarter): HeroCategoryId {
  const t = `${s.title} ${s.prompt}`.toLowerCase();
  if (/build me|small app|tiny app|tool that|tracker/.test(t)) return 'build';
  if (/open [a-z]|browse|website|browser|opentable|maps|flights/.test(t)) return 'web';
  if (/folder|files|downloads|desktop|documents|screenshot|my mac|my computer|repo/.test(t)) return 'computer';
  return 'research';
}

export function heroMenuFor(menu: PersonalizedMenu | null | undefined, starters: PersonalizedStarter[]): PersonalizedMenu {
  const out: PersonalizedMenu = { computer: [], research: [], web: [], build: [] };
  if (menu) {
    for (const cat of HERO_CATEGORIES) out[cat.id] = [...(menu[cat.id] ?? [])];
  } else {
    for (const s of starters) {
      const cat = classifyStarter(s);
      if (out[cat].length < MENU_SIZE) out[cat].push(s);
    }
  }
  for (const cat of HERO_CATEGORIES) {
    for (const extra of FALLBACK_MENU[cat.id]) {
      if (out[cat.id].length >= MENU_SIZE) break;
      if (out[cat.id].every((row) => row.title !== extra.title)) out[cat.id].push(extra);
    }
    out[cat.id] = out[cat.id].slice(0, MENU_SIZE);
  }
  return out;
}
