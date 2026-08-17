import Providers from './providers'

export const metadata = {
  title: 'SentinelIntel - Fake Profile Detection Threat Intelligence',
  description: 'Threat Intelligence Dashboard for Fake Social Media Profile Detection',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
