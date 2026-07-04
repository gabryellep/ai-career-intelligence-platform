/**
 * FeatureDisabledNotice.jsx — Mensagem exibida quando o histórico/analytics
 * está desligado (feature flag ENABLE_HISTORY_API/ENABLE_ANALYTICS_API=false
 * no backend) ou temporariamente indisponível (banco fora do ar).
 */

function FeatureDisabledNotice({ variant = 'disabled', message }) {
  const defaultMessage =
    variant === 'unavailable'
      ? 'Não foi possível carregar o histórico e os analytics no momento. Tente novamente em instantes.'
      : 'Histórico e analytics estão desativados neste ambiente.';

  return (
    <div className="dashboard-notice" role="status">
      <span className="dashboard-notice-icon">{variant === 'unavailable' ? '⚠️' : 'ℹ️'}</span>
      <p className="dashboard-notice-text">{message || defaultMessage}</p>
    </div>
  );
}

export default FeatureDisabledNotice;
