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

  const jobLength = jobDescription.trim().length;
  const canSubmit = Boolean(file) && jobLength >= MIN_JOB_LENGTH && consentGiven && !loading;

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
      <div className="form-header">
        <div>
          <p className="section-eyebrow">Nova análise</p>
          <h2>Currículo + descrição da vaga</h2>
        </div>
        <span className="form-badge">PDF até 5 MB</span>
      </div>

      <div className="form-grid">
        <div className="form-group upload-group">
        <label htmlFor="resume-file" className="form-label">
          Currículo
        </label>
          <label className={`file-dropzone ${file ? 'file-dropzone--selected' : ''}`} htmlFor="resume-file">
            <span className="file-dropzone-title">{file ? file.name : 'Selecionar PDF'}</span>
            <span className="file-dropzone-subtitle">
              {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Arquivo em PDF, máximo 5 MB'}
            </span>
          </label>
          <input
            id="resume-file"
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="file-input"
            disabled={loading}
          />
        </div>

        <div className="form-group job-group">
        <label htmlFor="job-description" className="form-label">
          Descrição da vaga
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
          <div className="textarea-footer">
            <span>{jobLength} caracteres</span>
            <span>{jobLength >= MIN_JOB_LENGTH ? 'Pronto para análise' : 'Mínimo de 10 caracteres'}</span>
          </div>
        </div>
      </div>

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
            esta análise. O PDF e o texto bruto não são salvos. Quando o banco
            está configurado, a aplicação pode armazenar apenas metadados e
            resultados estruturados da análise. Histórico e analytics ficam
            desativados na demo pública. Saiba mais em{' '}
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
        disabled={!canSubmit}
        aria-busy={loading}
      >
        {loading ? 'Analisando...' : 'Analisar Currículo'}
      </button>

    </form>
  );
}

export default UploadForm;
