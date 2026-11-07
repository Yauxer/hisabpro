export function FormSection({ icon, title, description, action, children, className = '' }) {
  return (
    <section className={`hp-form-section ${className}`.trim()}>
      <div className="hp-form-section__head">
        <div>
          <div className="hp-form-section__title">
            {icon && <i className={`ti ${icon}`} aria-hidden="true" />}
            <span>{title}</span>
          </div>
          {description && <div className="hp-form-section__desc">{description}</div>}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="hp-form-section__body">{children}</div>
    </section>
  )
}

export function AdvancedSection({ title = 'Options avancées', icon = 'ti-adjustments', children, open = false }) {
  return (
    <details className="hp-advanced" open={open}>
      <summary><i className={`ti ${icon}`} aria-hidden="true" /> {title}</summary>
      <div className="hp-advanced__body">{children}</div>
    </details>
  )
}

export function InlineNotice({ tone = 'info', icon, children }) {
  const cls = tone === 'warning' ? ' hp-inline-notice--warning'
    : tone === 'danger' ? ' hp-inline-notice--danger'
    : tone === 'success' ? ' hp-inline-notice--success' : ''
  const defaultIcon = tone === 'warning' ? 'ti-alert-triangle'
    : tone === 'danger' ? 'ti-alert-circle'
    : tone === 'success' ? 'ti-circle-check' : 'ti-info-circle'
  return <div className={`hp-inline-notice${cls}`}><i className={`ti ${icon || defaultIcon}`} aria-hidden="true" /><div>{children}</div></div>
}

export function ActionBar({ hint, children }) {
  return (
    <div className="hp-action-bar">
      {hint && <div className="hp-action-bar__hint">{hint}</div>}
      <div className="hp-action-bar__buttons">{children}</div>
    </div>
  )
}
