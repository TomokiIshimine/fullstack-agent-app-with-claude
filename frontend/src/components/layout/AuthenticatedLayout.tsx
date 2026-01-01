import type { ReactNode } from 'react'
import { Navbar } from './Navbar'

interface AuthenticatedLayoutProps {
  children: ReactNode
}

export function AuthenticatedLayout({ children }: AuthenticatedLayoutProps) {
  return (
    <div className="pt-16 min-h-screen">
      <Navbar />
      {children}
    </div>
  )
}
