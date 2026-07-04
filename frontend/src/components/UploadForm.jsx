/**
 * UploadForm.jsx — Formulário de upload do currículo e descrição da vaga.
 *
 * Props:
 *   onSubmit(file, jobDescription) — chamado ao submeter o formulário
 *   loading (bool) — desabilita o botão e exibe "Analisando..." durante a requisição
 */

import { useState } from 'react';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB em bytes
const MIN_JOB_LENGTH = 10; // alinhado com o backend

function UploadForm({ onSubmit, loading }) {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [consentGiven, setConsentGiven] = useState(false);
  const [error, setError] = useState('');

  function handleFileChange(e) {
    const selected = e.target.files[0] || null;
    setFile(selected);
    setError('');
  }

  function handleJobDescriptionChange(e) {
    setJobDescription(e.target.value);
    setError('');
  }

  function handleConsentChange(e) {
    setConsentGiven(e.target.checked);
    setError('');
  }

  function handleSubmit(e) {
    e.preventDefault();

    // Validação: arquivo obrigatório + tipo + tamanho (agrupados)
    if (!file) {
      setError('Por favor, selecione um arquivo PDF.');
      return;
    }

    if (file.type !== 'application/pdf' || file.size > MAX_FILE_SIZE) {
      setError('Selecione um PDF válido de até 5MB.');
      return;
    }

    // Validação: descrição mínima de 10 caracteres
    if (jobDescription.trim().length < MIN_JOB_LENGTH) {
      setError('Descreva melhor a vaga (mínimo de 10 caracteres).');
      return;
    }

    // Validação: consentimento obrigatório antes do envio
    if (!consentGiven) {
      setError('Marque a caixa de consentimento para continuar.');
      return;
    }

    setError('');
    onSubmit(file, jobDescription);
  }

  return (
    <form onSubmit={handleSubmit} className="upload-form" noValidate>

      {/* Campo de upload de arquivo PDF */}
      <div className="form-group">
        <label htmlFor="resume-file" className="form-label">
          Currículo (PDF)
        </label>
        <input
          id="resume-file"
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="file-input"
          disabled={loading}
        />
        {file && (
          <span className="file-name">
            📄 {file.name}
          </span>
        )}
      </div>

      {/* Textarea para descrição da vaga */}
      <div className="form-group">
        <label htmlFor="job-description" className="form-label">
          Descrição da Vaga
        </label>
        <textarea
          id="job-description"
          value={jobDescription}
          onChange={handleJobDescriptionChange}
          placeholder="Cole aqui a descrição completa da vaga..."
          className="job-textarea"
          rows={8}
          disabled={loading}
          aria-label="Descrição da vaga"
        />
      </div>

      {/* Consentimento de tratamento de dados (LGPD básica) */}
      <div className="form-group consent-group">
        <label className="consent-label" htmlFor="consent-checkbox">
          <input
            id="consent-checkbox"
            type="checkbox"
            checked={consentGiven}
            onChange={handleConsentChange}
            disabled={loading}
          />
          <span>
            Autorizo o processamento temporário do meu currículo para gerar
            esta análise. O arquivo é usado apenas durante esta requisição e
            não é salvo, nem gera histórico nesta versão. Saiba mais em{' '}
            <a href="https://github.com/gabryellep/ai-resume-analyzer/blob/main/PRIVACY.md" target="_blank" rel="noopener noreferrer">
              PRIVACY.md
            </a>.
          </span>
        </label>
      </div>

      {/* Mensagem de erro de validação */}
      {error && (
        <p className="validation-error" role="alert">
          {error}
        </p>
      )}

      {/* Botão de análise */}
      <button
        type="submit"
        className="analyze-button"
        disabled={loading || !consentGiven}
        aria-busy={loading}
      >
        {loading ? 'Analisando...' : 'Analisar Currículo'}
      </button>

    </form>
  );
}

export default UploadForm;
