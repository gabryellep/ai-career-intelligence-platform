/**
 * api.js — Camada de comunicação com o backend FastAPI.
 *
 * Usa:
 * - /analyze em desenvolvimento local, com proxy do Vite
 * - VITE_API_BASE_URL em produção, apontando para o backend no Render
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// ---------------------------------------------------------------------------
// Sessão anônima (SPEC 0009) — um UUID gerado uma única vez por navegador,
// persistido em localStorage, enviado em todas as chamadas via X-Session-Id.
// Não identifica uma pessoa; é usado apenas para isolar histórico/analytics
// por "sessão de navegador" (ver PRIVACY.md).
// ---------------------------------------------------------------------------

const SESSION_STORAGE_KEY = 'ai_resume_analyzer_session_id';

/**
 * Retorna o session_id já salvo em localStorage, ou gera e salva um novo
 * (UUID v4) na primeira chamada de cada navegador.
 *
 * @returns {string} UUID da sessão anônima deste navegador.
 */
export function getOrCreateSessionId() {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

/**
 * Envia o currículo em PDF e a descrição da vaga para análise.
 *
 * @param {File} file - Arquivo PDF do currículo selecionado pelo usuário.
 * @param {string} jobDescription - Texto da descrição da vaga.
 * @returns {Promise<Object>} Resultado da análise com score, matched_skills,
 *                            missing_skills, partial_skills, extra_skills,
 *                            insights, recommendations e, quando houver gaps,
 *                            career_improvement_plan.
 * @throws {Error} Se a requisição falhar ou o servidor retornar erro.
 */
export async function analyzeResume(file, jobDescription) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('job_description', jobDescription);

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
    // Não definir Content-Type manualmente — o browser define automaticamente
    // com o boundary correto para multipart/form-data
    headers: {
      'X-Session-Id': getOrCreateSessionId(),
    },
  });

  let data;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(
      data?.detail || 'Erro ao analisar o currículo. Tente novamente.'
    );
  }

  return data;
}

// ---------------------------------------------------------------------------
// Histórico e Analytics (SPEC 0005/0006) — consumidos pela área de
// Histórico e Dashboard (SPEC 0007).
//
// Diferente de analyzeResume() acima, estas funções NUNCA lançam exceção —
// sempre retornam { status, ok, data }, para que os componentes do
// dashboard distingam 200 (sucesso), 404 (feature flag desligada, ou
// análise não encontrada no detalhe), 422 (X-Session-Id ausente/inválido)
// e 503 (banco indisponível) sem precisar de try/catch em cada chamada.
//
// Todas enviam X-Session-Id (SPEC 0009) — obrigatório nestas rotas.
// ---------------------------------------------------------------------------

function buildQueryString(params) {
  if (!params) return '';
  const entries = Object.entries(params).filter(
    ([, value]) => value !== undefined && value !== null && value !== ''
  );
  if (entries.length === 0) return '';
  return `?${new URLSearchParams(entries).toString()}`;
}

async function apiGet(path, params) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}${buildQueryString(params)}`, {
      headers: {
        'X-Session-Id': getOrCreateSessionId(),
      },
    });
  } catch {
    // Falha de rede (backend fora do ar, DNS, etc.) — status 0 sinaliza isso.
    return { status: 0, ok: false, data: null };
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  return { status: response.status, ok: response.ok, data };
}

/**
 * Lista análises persistidas (GET /api/v1/analyses). Nunca lança exceção.
 *
 * @param {Object} [options]
 * @param {number} [options.limit=20]
 * @param {number} [options.offset=0]
 * @param {number} [options.minScore]
 * @param {string} [options.skillStatus] - matched | partial | missing | extra
 * @param {string} [options.skillName]
 * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
 */
export async function fetchAnalyses({
  limit = 20,
  offset = 0,
  minScore,
  skillStatus,
  skillName,
} = {}) {
  return apiGet('/api/v1/analyses', {
    limit,
    offset,
    min_score: minScore,
    skill_status: skillStatus,
    skill_name: skillName,
  });
}

/**
 * Detalhe de uma análise (GET /api/v1/analyses/{id}). Nunca lança exceção.
 *
 * @param {string} analysisId
 * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
 */
export async function fetchAnalysisDetail(analysisId) {
  return apiGet(`/api/v1/analyses/${analysisId}`);
}

/**
 * Resumo agregado (GET /api/v1/analytics/summary). Nunca lança exceção.
 *
 * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
 */
export async function fetchAnalyticsSummary() {
  return apiGet('/api/v1/analytics/summary');
}

/**
 * Ranking de skills (GET /api/v1/analytics/skills). Nunca lança exceção.
 *
 * @param {string} [status] - matched | partial | missing | extra
 * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
 */
export async function fetchAnalyticsSkills(status) {
  return apiGet('/api/v1/analytics/skills', { status });
}

/**
 * Evolução diária (GET /api/v1/analytics/timeline). Nunca lança exceção.
 *
 * @param {number} [days=30]
 * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
 */
export async function fetchAnalyticsTimeline(days = 30) {
  return apiGet('/api/v1/analytics/timeline', { days });
}
