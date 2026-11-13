import React, { Suspense } from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter, useRoutes } from 'react-router-dom';
import routes from '~react-pages';
import { store } from '../shared/state/store';
import ClaudeThemeProvider from '@/shared/styles/ThemeContext';

// No global shell. Earlier revisions wrapped every page in <AppShell>
// (sidebar + main content area). That forced a sidebar onto every app —
// great for SaaS dashboards, wrong for everything else (games, canvases,
// full-bleed previewers, the cold-start splash itself). Pages now opt
// IN to the shell: import `AppShell` from
// `@/app/components/Layout/AppShell` and wrap their own JSX in it if
// they want one. Otherwise the page is rendered full-bleed.
const Pages: React.FC = () => {
  return <Suspense fallback={null}>{useRoutes(routes)}</Suspense>;
};

const Main: React.FC = () => {
  return (
    <Provider store={store}>
      <ClaudeThemeProvider>
        <BrowserRouter>
          <Pages />
        </BrowserRouter>
      </ClaudeThemeProvider>
    </Provider>
  );
};

export default Main;
