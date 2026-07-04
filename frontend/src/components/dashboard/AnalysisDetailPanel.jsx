/**
 * AnalysisDetailPanel.jsx — Detalhe de uma análise selecionada na lista
 * (GET /api/v1/analyses/{id}).
 *
 * Reaproveita os componentes já existentes da tela de análise individual
 * (ScoreCard, SkillsPanel, InsightsPanel, Recommendations) — o detalhe de
 * uma análise histórica tem exatamente o mesmo formato de dados que o
 * resultado de POST /analyze, então não há necessidade de duplicar UI.
 */

import { useEffect, useState } from 'react';
import { fetchAnalysisDetail } from '../../api.js';
import ScoreCard from '../ScoreCard.jsx';
import SkillsPanel from '../SkillsPanel.jsx';
import InsightsPanel from '../InsightsPanel.jsx';
import Recommendations from '../Recommendations.jsx';

function AnalysisDetailPanel({ analysisId, onClose }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setAnalysis(null);

      const { ok, status, data } = await fetchAnalysisDetail(analysisId);

      if (cancelled) return;

      if (!ok) {
        // Neste ponto o dashboard já confirmou que a API está habilitada
        // (ver DashboardPage) — um 404 aqui significa que esta análise
        // específica não foi encontrada, não que a API está desligada.
        setError(
          status === 404
            ? 'Esta análise não foi encontrada (pode ter sido removida).'
            : 'Não foi possível carregar o detalhe desta análise.'
        );
      } else {
        setAnalysis(data);
      }
      setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [analysisId]);

  return (
    <div className="dashboard-panel analysis-detail-panel">
      <div className="dashboard-panel-header">
        <h3 className="dashboard-panel-title">Detalhe da análise</h3>
        <button type="button" className="dashboard-close-button" onClick={onClose}>
          Fechar
        </button>
      </div>

      {loading && <p className="dashboard-loading-text">Carregando detalhe...</p>}

      {!loading && error && <p className="dashboard-error-text">{error}</p>}

      {!loading && !error && analysis && (
        <div className="result-container">
          <ScoreCard score={analysis.score} />
          <SkillsPanel
            matchedSkills={analysis.matched_skills || []}
            missingSkills={analysis.missing_skills || []}
            partialSkills={analysis.partial_skills || []}
            extraSkills={analysis.extra_skills || []}
          />
          {analysis.insights && (
            <InsightsPanel
              insights={analysis.insights}
              partialSkills={analysis.partial_skills || []}
              extraSkills={analysis.extra_skills || []}
            />
          )}
          <Recommendations recommendations={analysis.recommendations || []} />
        </div>
      )}
    </div>
  );
}

export default AnalysisDetailPanel;
