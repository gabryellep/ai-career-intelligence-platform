/**
 * ScoreCard.jsx — Card de score de compatibilidade.
 *
 * Props:
 *   score (number) — valor entre 0 e 100
 *   stats (object) — contagens reais de matched/missing/partial/extra
 */

function ScoreCard({ score, stats }) {
  // Garante que o score fique sempre no intervalo válido
  const safeScore = Math.max(0, Math.min(100, score));

  function getBarColor(value) {
    if (value >= 80) return '#38a169'; // verde
    if (value >= 40) return '#d69e2e'; // amarelo
    return '#e53e3e';                  // vermelho
  }

  function getScoreLabel(value) {
    if (value >= 80) return 'Alta compatibilidade';
    if (value >= 40) return 'Compatibilidade moderada';
    return 'Baixa compatibilidade';
  }

  function getScoreDescription(value) {
    if (value >= 80) return 'O currículo cobre a maior parte das skills identificadas na vaga.';
    if (value >= 40) return 'Há uma base útil, mas alguns gaps ainda merecem prioridade.';
    return 'A vaga exige várias skills que ainda não aparecem no currículo enviado.';
  }

  const barColor = getBarColor(safeScore);
  const scoreLabel = getScoreLabel(safeScore);

  return (
    <section className="score-card">
      <div className="score-card-copy">
        <p className="section-eyebrow">Score explicável</p>
        <h3>Compatibilidade geral</h3>
        <p>{getScoreDescription(safeScore)}</p>
      </div>

      <div className="score-value" aria-label={`Score: ${safeScore} de 100`}>
        <span className="score-number">{safeScore}</span>
        <span className="score-max">/100</span>
      </div>

      <p className="score-label" style={{ color: barColor }}>
        {scoreLabel}
      </p>

      <div
        className="score-bar-track"
        role="progressbar"
        aria-valuenow={safeScore}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="score-bar-fill"
          style={{
            width: `${safeScore}%`,
            backgroundColor: barColor,
          }}
        />
      </div>

      {stats && (
        <dl className="score-breakdown" aria-label="Resumo das skills">
          <div>
            <dt>Atendidas</dt>
            <dd>{stats.matched}</dd>
          </div>
          <div>
            <dt>Faltantes</dt>
            <dd>{stats.missing}</dd>
          </div>
          <div>
            <dt>Parciais</dt>
            <dd>{stats.partial}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}

export default ScoreCard;
