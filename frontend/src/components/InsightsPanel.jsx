/**
 * InsightsPanel.jsx — Painel de análise do perfil do candidato.
 *
 * Props:
 *   insights       (object)   — { strengths, weaknesses, priority_actions }
 *   partialSkills  (string[]) — skills parcialmente atendidas (opcional)
 *   extraSkills    (string[]) — skills extras do currículo (opcional)
 */

function InsightsPanel({ insights, partialSkills = [], extraSkills = [] }) {
  if (!insights) return null;

  const {
    strengths       = [],
    weaknesses      = [],
    priority_actions = [],
  } = insights;

  const hasContent = strengths.length || weaknesses.length || priority_actions.length;
  if (!hasContent) return null;

  return (
    <div className="insights-card">
      <h2 className="insights-title">Análise do Perfil</h2>

      {/* Grade: pontos fortes + pontos de atenção */}
      <div className="insights-grid">

        {strengths.length > 0 && (
          <div className="insights-section insights-section--strengths">
            <h3 className="insights-section-title">
              <span className="insights-icon">💪</span> Pontos Fortes
            </h3>
            <ul className="insights-list">
              {strengths.map((item, i) => (
                <li key={i} className="insights-item insights-item--strength">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {weaknesses.length > 0 && (
          <div className="insights-section insights-section--weaknesses">
            <h3 className="insights-section-title">
              <span className="insights-icon">⚠️</span> Pontos de Atenção
            </h3>
            <ul className="insights-list">
              {weaknesses.map((item, i) => (
                <li key={i} className="insights-item insights-item--weakness">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>

      {/* Skills parcialmente atendidas */}
      {partialSkills.length > 0 && (
        <div className="insights-section insights-section--partial-detail">
          <h3 className="insights-section-title">
            <span className="insights-icon">◑</span> Skills Parcialmente Atendidas
          </h3>
          <p className="insights-hint">
            Você tem essas skills, mas em nível inferior ao exigido pela vaga.
          </p>
          <ul className="skills-list">
            {partialSkills.map((skill) => (
              <li key={skill} className="skill-badge skill-badge--partial">
                {skill}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Skills extras do currículo */}
      {extraSkills.length > 0 && (
        <div className="insights-section insights-section--extra-detail">
          <h3 className="insights-section-title">
            <span className="insights-icon">＋</span> Skills Extras no Currículo
          </h3>
          <p className="insights-hint">
            Você tem essas skills além do exigido — podem ser diferenciais em outras vagas.
          </p>
          <ul className="skills-list">
            {extraSkills.map((skill) => (
              <li key={skill} className="skill-badge skill-badge--extra">
                {skill}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Próximos passos */}
      {priority_actions.length > 0 && (
        <div className="insights-section insights-section--actions">
          <h3 className="insights-section-title">
            <span className="insights-icon">🎯</span> Próximos Passos
          </h3>
          <ol className="insights-actions-list">
            {priority_actions.map((action, i) => (
              <li key={i} className="insights-action-item">
                <span className="insights-action-number">{i + 1}</span>
                <span className="insights-action-text">{action}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

    </div>
  );
}

export default InsightsPanel;
