import type { Metadata } from "next";
import { Fredoka, Nunito } from "next/font/google";
import PromoBanner from "@/components/PromoBanner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import NewsletterModal from "@/components/NewsletterModal";
import ScrollToTop from "@/components/ScrollToTop";
import PWARegistration from "@/components/PWARegistration";
import ChatbotLoader from "@/components/ChatbotLoader";
import PushNotificationBanner from "@/components/PushNotificationBanner";
import { CartProvider } from "@/context/CartContext";
import { ToastProvider } from "@/context/ToastContext";
import { SiteConfigProvider } from "@/context/SiteConfigContext";
import { SoundProvider } from "@/context/SoundContext";
import "./globals.css";

const fredoka = Fredoka({
  subsets: ["latin"],
  variable: "--font-fredoka",
});

const nunito = Nunito({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-nunito",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://antojitos-express.netlify.app"),
  title: "Antojitos Express - Fuente de Soda & Delivery",
  description: "Jugos, empanadas, sandwiches, pasteles y postres. Pedido online con delivery a tu casa u oficina.",
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    url: "https://antojitos-express.netlify.app/",
    title: "Antojitos Express - Fuente de Soda",
    description: "Los mejores antojos, de nuestra cocina a tu mesa. Jugos, empanadas, postres y más rápido y delicioso.",
    images: ["/img/products/pionono-choco-frutos.jpg"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Antojitos Express - Fuente de Soda",
    description: "Los mejores antojos, rápidos y deliciosos con delivery.",
    images: ["/img/products/pionono-choco-frutos.jpg"],
  },
  authors: [{ name: "Rodrigo Alejandro Vega Rojas (DarckRovert)", url: "https://github.com/DarckRovert" }],
  creator: "Rodrigo Alejandro Vega Rojas (DarckRovert)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <head>
        <script src="https://identity.netlify.com/v1/netlify-identity-widget.js" async />
        <link rel="icon" href="/img/favicon.svg" sizes="any" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/img/favicon.svg" />
      </head>
      <body
        className={`${fredoka.variable} ${nunito.variable} font-sans antialiased bg-paper text-primary flex flex-col min-h-screen`}
      >
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Restaurant",
              "name": "Antojitos Express",
              "description": "Fuente de soda y cafetería. Jugos, empanadas, postres y más.",
              "url": "https://antojitos-express.netlify.app",
              "telephone": "+51965968723",
              "address": {
                "@type": "PostalAddress",
                "addressLocality": "Santiago de Surco",
                "addressRegion": "Lima",
                "addressCountry": "PE"
              },
              "priceRange": "S/5 - S/70",
              "servesCuisine": "Peruana / Fuente de Soda",
              "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.9",
                "reviewCount": "15"
              },
              "openingHoursSpecification": {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "opens": "09:00",
                "closes": "20:00"
              }
            })
          }}
        />
        <SiteConfigProvider>
          <SoundProvider>
            <ToastProvider>
              <CartProvider>
                <a
                  href="#main-content"
                  className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[200] focus:bg-primary focus:text-white focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg"
                >
                  Ir al contenido principal
                </a>
                <PWARegistration />
                <NewsletterModal />
                <PromoBanner />
                <Navbar />
                <CartSidebar />
                <ScrollToTop />
                <main id="main-content" className="flex-grow pt-16">
                  {children}
                </main>
                <ChatbotLoader />
                <PushNotificationBanner />
                <Footer />
              </CartProvider>
            </ToastProvider>
          </SoundProvider>
        </SiteConfigProvider>
      </body>
    </html>
  );
}
