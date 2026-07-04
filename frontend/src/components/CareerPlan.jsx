/**
 * CareerPlan.jsx - Exibe o Career Improvement Plan quando o backend envia.
 */

function CareerPlan({ plan }) {
  if (!plan || !Array.isArray(plan.items) || plan.items.length === 0) return null;

  return (
    <section className="career-plan-card">
      <div className="panel-heading">
        <div>
          <p className="section-eyebrow">Plano de evolução</p>
          <h3>Career Improvement Plan</h3>
          <p>{plan.summary}</p>
        </div>
        <span className="panel-count">{plan.items.length} gaps</span>
      </div>

      <div className="career-plan-list">
        {plan.items.map((item) => (
          <article key={`${item.gap_type}-${item.skill}`} className="career-plan-item">
            <div className="career-plan-item-header">
              <div>
                <span className="career-plan-gap">{item.gap_type === 'partial' ? 'Parcial' : 'Faltante'}</span>
                <h4>{item.skill}</h4>
              </div>
              <span className="career-plan-area">{item.focus_area}</span>
            </div>

            <dl className="career-plan-actions">
              <div>
                <dt>Estudar</dt>
                <dd>{item.study}</dd>
              </div>
              <div>
                <dt>Praticar</dt>
                <dd>{item.practice}</dd>
              </div>
              <div>
                <dt>Currículo</dt>
                <dd>{item.resume_guidance}</dd>
              </div>
              <div>
                <dt>GitHub/LinkedIn</dt>
                <dd>{item.profile_guidance}</dd>
              </div>
            </dl>

            {item.resources?.length > 0 && (
              <ul className="career-plan-resources" aria-label={`Recursos para ${item.skill}`}>
                {item.resources.map((resource) => (
                  <li key={resource}>{resource}</li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>

      {plan.honesty_note && <p className="career-plan-honesty">{plan.honesty_note}</p>}
    </section>
  );
}

export default CareerPlan;
