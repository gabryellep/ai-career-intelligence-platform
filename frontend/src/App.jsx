/**
 * App.jsx — Componente raiz da aplicação AI Resume Analyzer.
 *
 * Gerencia o estado global e orquestra todos os componentes filhos.
 * Fluxo: UploadForm → API → ScoreCard + SkillsPanel + InsightsPanel + Recommendations
 */

import { useState, useRef } from 'react';
import UploadForm from './components/UploadForm.jsx';
import ScoreCard from './components/ScoreCard.jsx';
import SkillsPanel from './components/SkillsPanel.jsx';
import Recommendations from './components/Recommendations.jsx';
import InsightsPanel from './components/InsightsPanel.jsx';
import { analyzeResume } from './api.js';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB em bytes

function App() {
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

  return (
    <div className="app-container">

      <header className="app-header">
        <h1 className="app-title">AI Resume Analyzer</h1>
        <p className="app-description">
          Envie seu currículo em PDF e cole a descrição de uma vaga para
          descobrir sua compatibilidade, identificar skills faltantes e
          receber recomendações de melhoria.
        </p>
      </header>

      <main className="app-main">

        <UploadForm onSubmit={handleAnalyze} loading={loading} />

        {!result && !error && !loading && (
          <p className="initial-hint">
            Envie um currículo e uma descrição para começar.
          </p>
        )}

        {error && (
          <div className="error-banner" role="alert">
            ⚠️ {error}
          </div>
        )}

        {result && (
          <div className="result-container" ref={resultRef}>

            {/* Score de compatibilidade */}
            <ScoreCard score={result.score} />

            {/* Skills: encontradas, faltantes e parciais */}
            <SkillsPanel
              matchedSkills={result.matched_skills || []}
              missingSkills={result.missing_skills || []}
              partialSkills={result.partial_skills || []}
              extraSkills={result.extra_skills || []}
            />

            {/* Análise do perfil: pontos fortes, fracos e ações */}
            {result.insights && (
              <InsightsPanel
                insights={result.insights}
                partialSkills={result.partial_skills || []}
                extraSkills={result.extra_skills || []}
              />
            )}

            {/* Recomendações de melhoria */}
            <Recommendations recommendations={result.recommendations || []} />

          </div>
        )}

      </main>

    </div>
  );
}

export default App;
