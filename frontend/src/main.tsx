import React from 'react';
import { createRoot } from 'react-dom/client';
import { AUTH_TOKEN_KEY } from './api';
import App from './App';
import './styles.css';

document.addEventListener('click', (event) => {
	if ((event.target as HTMLElement).closest('.settings')) {
		sessionStorage.removeItem(AUTH_TOKEN_KEY);
		window.location.reload();
	}
});

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
