/**
 * api.js — Camada de comunicação com o backend FastAPI.
 *
 * Usa:
 * - /analyze em desenvolvimento local, com proxy do Vite
 * - VITE_API_BASE_URL em produção, apontando para o backend no Render
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Envia o currículo em PDF e a descrição da vaga para análise.
 *
 * @param {File} file - Arquivo PDF do currículo selecionado pelo usuário.
 * @param {string} jobDescription - Texto da descrição da vaga.
 * @returns {Promise<Object>} Resultado da análise com score, matched_skills,
 *                            missing_skills, partial_skills, extra_skills,
 *                            insights e recommendations.
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
