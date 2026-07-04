/**
 * DashboardPage.jsx — Área de Histórico e Dashboard (SPEC 0007).
 *
 * Ao montar, verifica GET /api/v1/analytics/summary uma única vez para
 * decidir o estado da página inteira:
 *   - 404  → API desligada (ENABLE_HISTORY_API/ENABLE_ANALYTICS_API=false)
 *            → exibe FeatureDisabledNotice, nenhuma outra chamada é feita.
 *   - 503 / erro de rede → indisponibilidade temporária.
 *   - 200 → renderiza SummaryCards, SkillsRankingPanel, ScoreTimelineChart
 *            e AnalysesList, cada um buscando seus próprios dados.
 *
 * Essa checagem inicial resolve a ambiguidade do 404 nos endpoints de
 * detalhe: uma vez que o summary confirma que a API está habilitada,
 * qualquer 404 subsequente (ex.: ao abrir o detalhe de uma análise)
 * significa "não encontrado", não "API desligada".
 */

import { useEffect, useState } from 'react';
import { fetchAnalyticsSummary } from '../../api.js';
import FeatureDisabledNotice from './FeatureDisabledNotice.jsx';
import SummaryCards from './SummaryCards.jsx';
import SkillsRankingPanel from './SkillsRankingPanel.jsx';
import ScoreTimelineChart from './ScoreTimelineChart.jsx';
import AnalysesList from './AnalysesList.jsx';

function DashboardPage() {
  const [checking, setChecking] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function checkAvailability() {
      setChecking(true);
      setUnavailable(false);

      const { ok, status, data } = await fetchAnalyticsSummary();

      if (cancelled) return;

      if (status === 404) {
        setEnabled(false);
      } else if (!ok) {
        setEnabled(false);
        setUnavailable(true);
      } else {
        setEnabled(true);
        setSummary(data);
      }
      setChecking(false);
    }

    checkAvailability();
    return () => {
      cancelled = true;
    };
  }, []);

  if (checking) {
    return (
      <div className="dashboard-container">
        <p className="dashboard-loading-text">Verificando disponibilidade do histórico e analytics...</p>
      </div>
    );
  }

  if (!enabled) {
    return (
      <div className="dashboard-container">
        <FeatureDisabledNotice variant={unavailable ? 'unavailable' : 'disabled'} />
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {summary && <SummaryCards summary={summary} />}
      <SkillsRankingPanel />
      <ScoreTimelineChart />
      <AnalysesList />
    </div>
  );
}

export default DashboardPage;
