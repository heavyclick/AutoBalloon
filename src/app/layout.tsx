import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AutoBalloon - Canonical Inspection Engine',
  description: 'AI-powered dimension detection for First Article Inspection. Drop a blueprint, get AS9102 reports in seconds.',
  keywords: ['AS9102', 'FAI', 'First Article Inspection', 'Blueprint', 'Dimension Detection', 'QC', 'Quality Control'],
  authors: [{ name: 'AutoBalloon' }],
  openGraph: {
    title: 'AutoBalloon - Stop Manually Ballooning Drawings',
    description: 'Get your AS9102 Excel Report in 10 seconds. AI-powered dimension detection.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-brand-dark text-white antialiased`}>
        {children}
      </body>
    </html>
  )
}
