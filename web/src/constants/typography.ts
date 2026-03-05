export const typography = {
  fontFamily:
    'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, Arial, "Noto Sans", "Helvetica Neue", sans-serif',
  monoFamily:
    'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',

  sizes: {
    xxs: 11,
    xs: 12,
    sm: 13,
    md: 14,
    lg: 16,
    xl: 18,
    '2xl': 22,
    '3xl': 24,
  },

  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  lineHeights: {
    tight: 1.18,
    normal: 1.45,
    relaxed: 1.6,
  },

  h1: { size: 24, weight: 700, lineHeight: 1.18 },
  h2: { size: 18, weight: 700, lineHeight: 1.18 },
  body: { size: 14, weight: 500, lineHeight: 1.45 },
  small: { size: 12, weight: 500, lineHeight: 1.45 },
} as const
