/**
 * Recommendations.jsx — Lista de recomendações de melhoria do currículo.
 *
 * Props:
 *   recommendations (string[]) — lista de recomendações geradas pelo backend
 *
 * Não renderiza se a lista estiver vazia ou undefined.
 */

function Recommendations({ recommendations }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="recommendations-card">
      <h2 className="recommendations-title">
        <span className="recommendations-icon">📋</span> Recomendações
      </h2>
      <p className="recommendations-subtitle">
        Ações concretas para melhorar sua compatibilidade com esta vaga.
      </p>
      <ol className="recommendations-list">
        {recommendations.map((rec, index) => (
          <li key={index} className="recommendation-item">
            <span className="recommendation-number">{index + 1}</span>
            <span className="recommendation-text">{rec}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default Recommendations;
