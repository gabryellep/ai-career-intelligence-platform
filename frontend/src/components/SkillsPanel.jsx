/**
 * SkillsPanel.jsx — Painéis de skills encontradas, faltantes, parciais e extras.
 *
 * Props:
 *   matchedSkills  (string[]) — skills presentes no currículo e na vaga
 *   missingSkills  (string[]) — skills da vaga ausentes no currículo
 *   partialSkills  (string[]) — skills parcialmente atendidas (ex: idioma nível inferior)
 *   extraSkills    (string[]) — skills do currículo além do exigido pela vaga
 *
 * Todos os props têm fallback para [] — não quebra se vier undefined.
 */

function SkillBadgeList({ skills, badgeClass, emptyMessage, ariaLabel }) {
  return skills.length > 0 ? (
    <ul className="skills-list" aria-label={ariaLabel}>
      {skills.map((skill) => (
        <li key={skill} className={`skill-badge ${badgeClass}`}>
          {skill}
        </li>
      ))}
    </ul>
  ) : (
    <p className="skills-empty">{emptyMessage}</p>
  );
}

function SkillsPanel({
  matchedSkills  = [],
  missingSkills  = [],
  partialSkills  = [],
  extraSkills    = [],
}) {
  const hasPartial = partialSkills.length > 0;
  const hasExtra   = extraSkills.length > 0;
  const totalRelevant = matchedSkills.length + missingSkills.length + partialSkills.length;
  const safeTotal = Math.max(1, totalRelevant);
  const bars = [
    { label: 'Atendidas', value: matchedSkills.length, className: 'skills-meter-fill--matched' },
    { label: 'Faltantes', value: missingSkills.length, className: 'skills-meter-fill--missing' },
    { label: 'Parciais', value: partialSkills.length, className: 'skills-meter-fill--partial' },
  ];

  return (
    <section className="skills-card">
      <div className="panel-heading">
        <div>
          <p className="section-eyebrow">Mapa de skills</p>
          <h3>O que a vaga pede vs. o que aparece no currículo</h3>
        </div>
        <span className="panel-count">{totalRelevant} requisitos identificados</span>
      </div>

      <div className="skills-meter" aria-label="Distribuição de skills por status">
        {bars.map((bar) => (
          <div key={bar.label} className="skills-meter-row">
            <span>{bar.label}</span>
            <div className="skills-meter-track">
              <div
                className={`skills-meter-fill ${bar.className}`}
                style={{ width: `${Math.round((bar.value / safeTotal) * 100)}%` }}
              />
            </div>
            <strong>{bar.value}</strong>
          </div>
        ))}
      </div>

      <div className="skills-panel-container">

        <div className="skills-panel skills-panel--matched">
          <h3 className="skills-panel-title skills-panel-title--matched">
            Encontradas
          </h3>
          <SkillBadgeList
            skills={matchedSkills}
            badgeClass="skill-badge--matched"
            emptyMessage="Nenhuma skill identificada."
            ariaLabel="Skills encontradas"
          />
        </div>

        <div className="skills-panel skills-panel--missing">
          <h3 className="skills-panel-title skills-panel-title--missing">
            Faltantes
          </h3>
          <SkillBadgeList
            skills={missingSkills}
            badgeClass="skill-badge--missing"
            emptyMessage="Nenhuma skill faltante."
            ariaLabel="Skills faltantes"
          />
        </div>

      </div>

      {(hasPartial || hasExtra) && (
        <div className="skills-panel-container skills-panel-container--secondary">

          {hasPartial && (
            <div className="skills-panel skills-panel--partial">
              <h3 className="skills-panel-title skills-panel-title--partial">
                Parcialmente Atendidas
              </h3>
              <p className="skills-panel-hint">
                Skill exigida, mas atendida em nível inferior ao solicitado.
              </p>
              <SkillBadgeList
                skills={partialSkills}
                badgeClass="skill-badge--partial"
                emptyMessage=""
                ariaLabel="Skills parcialmente atendidas"
              />
            </div>
          )}

          {hasExtra && (
            <div className="skills-panel skills-panel--extra">
              <h3 className="skills-panel-title skills-panel-title--extra">
                Extras no Currículo
              </h3>
              <p className="skills-panel-hint">
                Skills que você tem além do exigido pela vaga.
              </p>
              <SkillBadgeList
                skills={extraSkills}
                badgeClass="skill-badge--extra"
                emptyMessage=""
                ariaLabel="Skills extras"
              />
            </div>
          )}

        </div>
      )}

    </section>
  );
}

export default SkillsPanel;
