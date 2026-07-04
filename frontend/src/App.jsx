/**
 * App.jsx — Componente raiz da aplicação AI Career Intelligence Platform.
 *
 * Gerencia o estado global e orquestra todos os componentes filhos.
 * Fluxo: UploadForm → API → ScoreCard + SkillsPanel + InsightsPanel + Recommendations
 *
 * A partir da SPEC 0007, alterna entre duas visões via estado local
 * (sem react-router-dom, ver decisão técnica da Spec): "Analisar" (fluxo
 * acima, inalterado) e "Histórico e Dashboard" (DashboardPage.jsx).
 */

import { useState, useRef } from 'react';
import UploadForm from './components/UploadForm.jsx';
import ScoreCard from './components/ScoreCard.jsx';
import SkillsPanel from './components/SkillsPanel.jsx';
import Recommendations from './components/Recommendations.jsx';
import InsightsPanel from './components/InsightsPanel.jsx';
import DashboardPage from './components/dashboard/DashboardPage.jsx';
import { analyzeResume } from './api.js';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB em bytes

function App() {
  const [view, setView] = useState('analyze');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const resultRef = useRef(null);

  async function handleAnalyze(file, jobDescription) {
    if (loading) return;

    if (file.type !== 'application/pdf') {
      setError('Por favor, selecione um arquivo PDF válido.');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('O arquivo excede o tamanho máximo permitido de 5 MB.');
      return;
    }

    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const data = await analyzeResume(file, jobDescription);
      setResult(data);

      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      const message = err.message?.trim()
        ? err.message
        : 'Não foi possível analisar o currículo. Verifique o arquivo e tente novamente.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const resultStats = result
    ? {
        matched: result.matched_skills?.length || 0,
        missing: result.missing_skills?.length || 0,
        partial: result.partial_skills?.length || 0,
        extra: result.extra_skills?.length || 0,
      }
    : null;

  return (
    <div className="app-shell">

      <header className="app-header">
        <p className="app-eyebrow">Career intelligence for tech roles</p>
        <h1 className="app-title">AI Career Intelligence Platform</h1>
        <p className="app-description">
          Compare seu currículo com uma vaga de tecnologia, IA, dados ou
          engenharia de software e receba um score explicável com prioridades
          práticas.
        </p>
        <p className="app-scope-note">
          Projetado para vagas tech. Resultados fora desse contexto podem ser
          menos precisos.
        </p>
      </header>

      <nav className="app-nav" aria-label="Navegação principal">
        <button
          type="button"
          className={`app-nav-button ${view === 'analyze' ? 'app-nav-button--active' : ''}`}
          onClick={() => setView('analyze')}
        >
          Analisar
        </button>
        <button
          type="button"
          className={`app-nav-button ${view === 'dashboard' ? 'app-nav-button--active' : ''}`}
          onClick={() => setView('dashboard')}
        >
          Histórico e Dashboard
        </button>
      </nav>

      {view === 'analyze' && (
        <main className="app-main">

          <UploadForm onSubmit={handleAnalyze} loading={loading} />

          {!result && !error && !loading && (
            <section className="empty-state" aria-label="Resumo do fluxo">
              <div>
                <span className="empty-state-step">1</span>
                <strong>Envie um PDF</strong>
                <p>O arquivo é validado antes da análise.</p>
              </div>
              <div>
                <span className="empty-state-step">2</span>
                <strong>Cole a vaga</strong>
                <p>Use a descrição completa para melhorar a extração.</p>
              </div>
              <div>
                <span className="empty-state-step">3</span>
                <strong>Revise os gaps</strong>
                <p>Priorize skills faltantes, parciais e recomendações.</p>
              </div>
            </section>
          )}

          {loading && (
            <section className="loading-card" aria-live="polite">
              <div className="loading-spinner" aria-hidden="true" />
              <div>
                <strong>Analisando compatibilidade...</strong>
                <p>Extraindo texto do PDF, identificando skills e calculando o score explicável.</p>
              </div>
            </section>
          )}

          {error && (
            <div className="error-banner" role="alert">
              <strong>Não foi possível concluir a análise.</strong>
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="result-container" ref={resultRef}>

              <section className="result-header" aria-label="Resumo da análise">
                <div>
                  <p className="section-eyebrow">Resultado da análise</p>
                  <h2>Compatibilidade com a vaga</h2>
                </div>
                <div className="result-stat-strip">
                  <span><strong>{resultStats.matched}</strong> atendidas</span>
                  <span><strong>{resultStats.missing}</strong> faltantes</span>
                  <span><strong>{resultStats.partial}</strong> parciais</span>
                  <span><strong>{resultStats.extra}</strong> extras</span>
                </div>
              </section>

              <ScoreCard score={result.score} stats={resultStats} />

              <SkillsPanel
                matchedSkills={result.matched_skills || []}
                missingSkills={result.missing_skills || []}
                partialSkills={result.partial_skills || []}
                extraSkills={result.extra_skills || []}
              />

              {result.insights && (
                <InsightsPanel
                  insights={result.insights}
                  partialSkills={result.partial_skills || []}
                  extraSkills={result.extra_skills || []}
                />
              )}

              <Recommendations recommendations={result.recommendations || []} />

            </div>
          )}

        </main>
      )}

      {view === 'dashboard' && (
        <main className="app-main">
          <DashboardPage />
        </main>
      )}

    </div>
  );
}

export default App;
