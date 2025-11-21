import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { GlobalErrorBoundary } from './components/GlobalErrorBoundary';

const theme = createTheme();

console.log('Main.tsx: Starting execution');

try {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    console.error('Main.tsx: Root element not found');
    throw new Error('Root element not found');
  }
  console.log('Main.tsx: Root element found', rootElement);

  const root = createRoot(rootElement);
  console.log('Main.tsx: Root created');

  root.render(
    <StrictMode>
      <GlobalErrorBoundary>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <App />
        </ThemeProvider>
      </GlobalErrorBoundary>
    </StrictMode>,
  );
  console.log('Main.tsx: Render called');
} catch (e) {
  console.error('Main.tsx: Error during initialization', e);
  document.body.innerHTML = `<div style="color: red; padding: 20px;"><h1>Fatal Error</h1><pre>${e}</pre></div>`;
}
