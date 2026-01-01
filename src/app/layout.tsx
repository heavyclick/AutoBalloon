import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

// Force dynamic rendering for all pages
export const dynamic = 'force-dynamic';
export const dynamicParams = true;
export const revalidate = 0;

export const metadata = {
  title: 'AutoBalloon - Canonical Inspection Engine',
  description: 'AI-powered dimension detection for First Article Inspection. Drop a blueprint, get AS9102 reports in seconds.',
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
