/**
 * SkillsRankingPanel.jsx — Ranking de skills por status
 * (GET /api/v1/analytics/skills), com filtro opcional por status.
 *
 * Renderiza barras horizontais proporcionais em CSS puro — sem biblioteca
 * de gráficos (ver SPEC 0007, decisão técnica).
 */

import { useEffect, useState } from 'react';
import { fetchAnalyticsSkills } from '../../api.js';

const STATUS_OPTIONS = [
  { value: '', label: 'Todas' },
  { value: 'matched', label: 'Atendidas' },
  { value: 'partial', label: 'Parciais' },
  { value: 'missing', label: 'Faltantes' },
  { value: 'extra', label: 'Extras' },
];

function countForStatus(item, status) {
  if (!status) return item.total_count;
  return item[`${status}_count`] ?? 0;
}

function SkillsRankingPanel() {
  const [status, setStatus] = useState('');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      const { status: httpStatus, ok, data } = await fetchAnalyticsSkills(status || undefined);

      if (cancelled) return;

      if (!ok) {
        setError(
          httpStatus === 404
            ? 'Ranking de skills indisponível neste ambiente.'
            : 'Não foi possível carregar o ranking de skills.'
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
  }, [status]);

  const maxCount = Math.max(1, ...items.map((item) => countForStatus(item, status)));

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <h3 className="dashboard-panel-title">Ranking de skills</h3>
        <select
          className="dashboard-select"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          aria-label="Filtrar ranking por status"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="dashboard-loading-text">Carregando ranking...</p>}

      {!loading && error && <p className="dashboard-error-text">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="dashboard-empty-text">Ainda não há dados suficientes para este filtro.</p>
      )}

      {!loading && !error && items.length > 0 && (
        <ul className="skills-ranking-list">
          {items.map((item) => {
            const count = countForStatus(item, status);
            const widthPercent = Math.max(4, Math.round((count / maxCount) * 100));
            return (
              <li key={item.skill_name} className="skills-ranking-row">
                <span className="skills-ranking-name">{item.skill_name}</span>
                <div className="skills-ranking-bar-track">
                  <div className="skills-ranking-bar-fill" style={{ width: `${widthPercent}%` }} />
                </div>
                <span className="skills-ranking-count">{count}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default SkillsRankingPanel;
