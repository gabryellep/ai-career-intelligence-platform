/**
 * main.jsx — Entrypoint da aplicação React.
 *
 * Monta o componente App no elemento #root do index.html.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './styles.css';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
