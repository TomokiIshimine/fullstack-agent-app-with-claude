import type { SVGProps } from 'react'

export type IconProps = SVGProps<SVGSVGElement>

const defaultIconProps: IconProps = {
  viewBox: '0 0 16 16',
  fill: 'currentColor',
  width: 12,
  height: 12,
}

/** Default props for UI icons (24x24 viewBox, stroke-based) */
const uiIconProps: IconProps = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  className: 'w-5 h-5',
}

/**
 * Token/circle icon for displaying token counts
 */
export function TokenIcon(props: IconProps) {
  return (
    <svg {...defaultIconProps} {...props}>
      <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm3.5 7.5a.5.5 0 0 1 0 1H8a.5.5 0 0 1-.5-.5V4a.5.5 0 0 1 1 0v3h3z" />
    </svg>
  )
}

/**
 * Clock icon for displaying response time
 */
export function ClockIcon(props: IconProps) {
  return (
    <svg {...defaultIconProps} {...props}>
      <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z" />
      <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z" />
    </svg>
  )
}

/**
 * Dollar/currency icon for displaying cost
 */
export function CostIcon(props: IconProps) {
  return (
    <svg {...defaultIconProps} {...props}>
      <path d="M4 10.781c.148 1.667 1.513 2.85 3.591 3.003V15h1.043v-1.216c2.27-.179 3.678-1.438 3.678-3.3 0-1.59-.947-2.51-2.956-3.028l-.722-.187V3.467c1.122.11 1.879.714 2.07 1.616h1.47c-.166-1.6-1.54-2.748-3.54-2.875V1H7.591v1.233c-1.939.23-3.27 1.472-3.27 3.156 0 1.454.966 2.483 2.661 2.917l.61.162v4.031c-1.149-.17-1.94-.8-2.131-1.718H4zm3.391-3.836c-1.043-.263-1.6-.825-1.6-1.616 0-.944.704-1.641 1.8-1.828v3.495l-.2-.05zm1.591 1.872c1.287.323 1.852.859 1.852 1.769 0 1.097-.826 1.828-2.2 1.939V8.73l.348.086z" />
    </svg>
  )
}

/* ============================================
 * UI Component Icons (24x24 stroke-based)
 * ============================================ */

/**
 * Close/X icon for modals and dismissible elements
 */
export function CloseIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

/**
 * Eye icon for showing password
 */
export function EyeIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
      />
    </svg>
  )
}

/**
 * Eye-off icon for hiding password
 */
export function EyeOffIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
      />
    </svg>
  )
}

/**
 * Warning triangle icon for alerts and CAPS LOCK warning
 */
export function WarningIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  )
}

/**
 * Check icon for success alerts
 */
export function CheckIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}

/**
 * Error/exclamation circle icon for error alerts
 */
export function ErrorCircleIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  )
}

/**
 * Info circle icon for info alerts
 */
export function InfoIcon(props: IconProps) {
  return (
    <svg {...uiIconProps} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  )
}
