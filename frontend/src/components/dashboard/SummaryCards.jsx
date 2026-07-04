/**
 * SummaryCards.jsx — Cards de resumo do dashboard (GET /api/v1/analytics/summary).
 *
 * Props:
 *   summary: AnalyticsSummaryResponse — total_analyses, average_score,
 *            best_score, worst_score, total_matched_skills,
 *            total_missing_skills, most_common_missing_skills.
 */

function SummaryCards({ summary }) {
  const {
    total_analyses: totalAnalyses,
    average_score: averageScore,
    best_score: bestScore,
    worst_score: worstScore,
    most_common_missing_skills: mostCommonMissingSkills = [],
  } = summary;

  if (totalAnalyses === 0) {
    return (
      <div className="dashboard-card dashboard-card--empty">
        <p className="dashboard-empty-text">
          Ainda não há análises persistidas neste ambiente. Realize uma análise na aba
          "Analisar" para começar a ver dados aqui.
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard-cards-grid">
      <div className="dashboard-card">
        <span className="dashboard-card-label">Total de análises</span>
        <span className="dashboard-card-value">{totalAnalyses}</span>
      </div>
      <div className="dashboard-card">
        <span className="dashboard-card-label">Score médio</span>
        <span className="dashboard-card-value">{averageScore.toFixed(1)}</span>
      </div>
      <div className="dashboard-card">
        <span className="dashboard-card-label">Melhor score</span>
        <span className="dashboard-card-value dashboard-card-value--good">{bestScore}</span>
      </div>
      <div className="dashboard-card">
        <span className="dashboard-card-label">Pior score</span>
        <span className="dashboard-card-value dashboard-card-value--bad">{worstScore}</span>
      </div>
      <div className="dashboard-card dashboard-card--wide">
        <span className="dashboard-card-label">Skills mais faltantes</span>
        {mostCommonMissingSkills.length === 0 ? (
          <span className="dashboard-empty-text">Nenhuma skill faltante registrada ainda.</span>
        ) : (
          <ul className="dashboard-missing-skills-list">
            {mostCommonMissingSkills.map((item) => (
              <li key={item.skill_name} className="dashboard-missing-skill-item">
                <span className="skill-badge skill-badge--missing">{item.skill_name}</span>
                <span className="dashboard-missing-skill-count">{item.count}x</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default SummaryCards;
