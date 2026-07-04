/**
 * AnalysesList.jsx — Lista paginada de análises (GET /api/v1/analyses),
 * com seleção de item para exibir o detalhe (AnalysisDetailPanel).
 */

import { useEffect, useState } from 'react';
import { fetchAnalyses } from '../../api.js';
import AnalysisDetailPanel from './AnalysisDetailPanel.jsx';

const PAGE_SIZE = 10;

function formatSkills(skills) {
  if (!skills || skills.length === 0) return '—';
  if (skills.length <= 3) return skills.join(', ');
  return `${skills.slice(0, 3).join(', ')} +${skills.length - 3}`;
}

function AnalysesList() {
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      const { ok, status, data } = await fetchAnalyses({ limit: PAGE_SIZE, offset });

      if (cancelled) return;

      if (!ok) {
        setError(
          status === 404
            ? 'Lista de análises indisponível neste ambiente.'
            : 'Não foi possível carregar a lista de análises.'
        );
        setItems([]);
        setTotal(0);
      } else {
        setItems(data?.items || []);
        setTotal(data?.total || 0);
      }
      setLoading(false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [offset]);

  const hasPrevious = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <div className="dashboard-panel">
      <h3 className="dashboard-panel-title">Análises recentes</h3>

      {loading && <p className="dashboard-loading-text">Carregando análises...</p>}

      {!loading && error && <p className="dashboard-error-text">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="dashboard-empty-text">Nenhuma análise encontrada.</p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <ul className="analyses-list">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`analyses-list-row ${selectedId === item.id ? 'analyses-list-row--selected' : ''}`}
                  onClick={() => setSelectedId(item.id)}
                >
                  <span className="analyses-list-score">{item.score}</span>
                  <span className="analyses-list-skills">
                    <strong>Atendidas:</strong> {formatSkills(item.matched_skills)}
                    {' · '}
                    <strong>Faltantes:</strong> {formatSkills(item.missing_skills)}
                  </span>
                  <span className="analyses-list-date">
                    {new Date(item.created_at).toLocaleString('pt-BR')}
                  </span>
                </button>
              </li>
            ))}
          </ul>

          <div className="dashboard-pagination">
            <button
              type="button"
              className="dashboard-pagination-button"
              disabled={!hasPrevious}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Anterior
            </button>
            <span className="dashboard-pagination-info">
              {Math.min(offset + 1, total)}–{Math.min(offset + PAGE_SIZE, total)} de {total}
            </span>
            <button
              type="button"
              className="dashboard-pagination-button"
              disabled={!hasNext}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Próxima
            </button>
          </div>
        </>
      )}

      {selectedId && (
        <AnalysisDetailPanel analysisId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}

export default AnalysesList;
