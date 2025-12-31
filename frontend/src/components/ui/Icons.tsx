import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement>

const defaultIconProps: IconProps = {
  viewBox: '0 0 16 16',
  fill: 'currentColor',
  width: 12,
  height: 12,
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
