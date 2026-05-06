/**
 * ScoreCard.jsx — Card de score de compatibilidade.
 *
 * Props:
 *   score (number) — valor entre 0 e 100
 */

function ScoreCard({ score }) {
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

  const barColor = getBarColor(safeScore);
  const scoreLabel = getScoreLabel(safeScore);

  return (
    <div className="score-card">
      <h2 className="score-card-title">Score de Compatibilidade</h2>

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
    </div>
  );
}

export default ScoreCard;
