export const ui = {
  color: {
    muted: 'var(--muted)',
    danger: 'var(--danger)',
    text: 'var(--text)',
  },
  fontWeight: {
    medium: 700,
    bold: 800,
    extraBold: 900,
  },
  space: {
    s1: 'var(--space-1)',
    s2: 'var(--space-2)',
    s3: 'var(--space-3)',
    s4: 'var(--space-4)',
    s5: 'var(--space-5)',
    s6: 'var(--space-6)',
    s8: 'var(--space-8)',
  },
  mt: {
    none: { marginTop: 0 },
    s2: { marginTop: 'var(--space-2)' },
    s3: { marginTop: 'var(--space-3)' },
    s4: { marginTop: 'var(--space-4)' },
    s6: { marginTop: 'var(--space-6)' },
  },
  mb: {
    s2: { marginBottom: 'var(--space-2)' },
  },
  mx: {
    auto: { marginLeft: 'auto', marginRight: 'auto' },
  },
  text: {
    muted: { color: 'var(--muted)', fontWeight: 700 },
    mutedOnly: { color: 'var(--muted)' },
    title: { fontWeight: 900 },
    titleRow: { fontWeight: 900, marginBottom: 'var(--space-2)' },
  },
  rowWrap: {
    display: 'flex',
    gap: 'var(--space-2)',
    flexWrap: 'wrap',
  } as const,
  rowBetweenWrap: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 'var(--space-3)',
    flexWrap: 'wrap',
  } as const,
  inputGrow: {
    flex: 1,
    minWidth: 220,
  } as const,
} as const
