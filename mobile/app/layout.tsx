import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.LIFE_OS_PUBLIC_ORIGIN || 'http://127.0.0.1:3000',
  ),
  title: 'Life OS',
  description: 'Your private team for planning, accountability, and progress.',
  manifest: '/manifest.webmanifest',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Life OS',
  },
  openGraph: {
    title: 'Life OS',
    description:
      'Your private team for planning, accountability, and progress.',
    type: 'website',

  },
  twitter: {
    card: 'summary_large_image',
    title: 'Life OS',
    description:
      'Your private team for planning, accountability, and progress.',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  interactiveWidget: 'resizes-content',
  themeColor: '#356c4d',
};

const themeScript = `
  (() => {
    try {
      const preference = localStorage.getItem('life-os-community-theme') || 'system';
      const dark = preference === 'dark' ||
        (preference === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      document.documentElement.classList.toggle('dark', dark);
      document.documentElement.dataset.theme = preference;
    } catch (_) {}
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body
        className="antialiased"
      >
        {children}
      </body>
    </html>
  );
}
