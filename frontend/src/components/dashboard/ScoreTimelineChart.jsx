/**
 * ScoreTimelineChart.jsx — Evolução diária de score/quantidade de análises
 * (GET /api/v1/analytics/timeline).
 *
 * Renderizado com SVG nativo (polyline simples) — sem biblioteca de
 * gráficos (ver SPEC 0007, decisão técnica). Dias sem análise não
 * aparecem na resposta da API (ver SPEC 0006) e, portanto, não aparecem
 * no eixo X aqui.
 */

import { useEffect, useState } from 'react';
import { fetchAnalyticsTimeline } from '../../api.js';

const CHART_WIDTH = 600;
const CHART_HEIGHT = 160;
const PADDING = 24;

function ScoreTimelineChart() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      const { ok, status, data } = await fetchAnalyticsTimeline(30);

      if (cancelled) return;

      if (!ok) {
        setError(
          status === 404
            ? 'Evolução de score indisponível neste ambiente.'
            : 'Não foi possível carregar a evolução de score.'
        );
        setItems([]);
      } else {
        setItems(data?.items || []);
      }
      setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="dashboard-panel">
        <h3 className="dashboard-panel-title">Evolução de score (últimos 30 dias)</h3>
        <p className="dashboard-loading-text">Carregando evolução...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-panel">
        <h3 className="dashboard-panel-title">Evolução de score (últimos 30 dias)</h3>
        <p className="dashboard-error-text">{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="dashboard-panel">
        <h3 className="dashboard-panel-title">Evolução de score (últimos 30 dias)</h3>
        <p className="dashboard-empty-text">Ainda não há dados suficientes para exibir um gráfico.</p>
      </div>
    );
  }

  const usableWidth = CHART_WIDTH - PADDING * 2;
  const usableHeight = CHART_HEIGHT - PADDING * 2;
  const step = items.length > 1 ? usableWidth / (items.length - 1) : 0;

  const points = items.map((item, index) => {
    const x = PADDING + step * index;
    const y = PADDING + usableHeight - (Math.min(100, Math.max(0, item.average_score)) / 100) * usableHeight;
    return { x, y, item };
  });

  const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(' ');

  return (
    <div className="dashboard-panel">
      <h3 className="dashboard-panel-title">Evolução de score (últimos 30 dias)</h3>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="score-timeline-svg"
        role="img"
        aria-label="Gráfico de evolução do score médio ao longo dos dias"
      >
        <polyline points={polylinePoints} className="score-timeline-line" />
        {points.map((point) => (
          <circle key={point.item.date} cx={point.x} cy={point.y} r="3.5" className="score-timeline-dot">
            <title>{`${point.item.date}: score médio ${point.item.average_score.toFixed(1)} (${point.item.analyses_count} análise(s))`}</title>
          </circle>
        ))}
      </svg>
      <ul className="score-timeline-legend">
        {items.map((item) => (
          <li key={item.date} className="score-timeline-legend-item">
            <span className="score-timeline-legend-date">{item.date}</span>
            <span className="score-timeline-legend-value">
              {item.average_score.toFixed(1)} ({item.analyses_count})
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ScoreTimelineChart;
