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
    <section className="recommendations-card">
      <div className="panel-heading">
        <div>
          <p className="section-eyebrow">Prioridades</p>
          <h3>Recomendações acionáveis</h3>
          <p>Ações concretas para melhorar sua compatibilidade com esta vaga.</p>
        </div>
      </div>
      <ol className="recommendations-list">
        {recommendations.map((rec, index) => (
          <li key={index} className="recommendation-item">
            <span className="recommendation-number">{index + 1}</span>
            <span className="recommendation-text">{rec}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default Recommendations;
