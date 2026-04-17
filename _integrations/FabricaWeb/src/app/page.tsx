"use client";

import { useState } from 'react';
import Image from 'next/image';
import Hero from '@/components/Hero';
import FeaturedProducts from '@/components/FeaturedProducts';
import DeliveryZones from '@/components/DeliveryZones';
import Lightbox from '@/components/Lightbox';
import TestimonialCarousel from '@/components/TestimonialCarousel';
import ReviewsSection from '@/components/ReviewsSection';
// NFTCard removed
import { useLayout } from '@/context/SiteConfigContext';

export default function Home() {
  const { layout } = useLayout();
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  const isVisible = (id: string) => layout.sections.find(s => s.id === id)?.visible ?? true;

  const instagramImages = [
    '/img/products/pionono-choco-frutos.jpg',
    '/img/products/cake-chocolate.jpg',
    '/img/products/alfajores.jpg',
    '/img/products/pionono-clasico.jpg',
    '/img/products/cake-marmoleado.jpg'
  ];

  return (
    <>
      {isVisible('hero') && <Hero />}
      {isVisible('featured') && <FeaturedProducts />}

      {isVisible('delivery') && <DeliveryZones />}

      {/* Nosotros Section */}
      {isVisible('nosotros') && (
        <section className="py-20 bg-white" id="nosotros">
          <div className="container mx-auto px-4 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6 animate-fade-up">
              <h2 className="text-4xl font-fredoka font-bold text-primary">Nuestra Historia</h2>
              <p className="text-lg text-gray-600 leading-relaxed">
                En Antojitos Express, creemos que un buen antojo te cambia el día.
                Nacimos de la pasión por la comida al paso bien hecha, con ingredientes fresquitos,
                preparados al momento y con todo el sabor de nuestro Perú.
              </p>
              <ul className="space-y-3 font-medium text-primary">
                <li className="flex items-center gap-3">🧑‍🍳 Elaboración diaria y fresca</li>
                <li className="flex items-center gap-3">🥤 Frutas de estación de primera</li>
                <li className="flex items-center gap-3">🥪 Sánguches contundentes</li>
                <li className="flex items-center gap-3">❤️ Preparado con harto cariño</li>
              </ul>
            </div>
            <div className="rounded-3xl overflow-hidden shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500 relative h-[400px]">
              <Image
                src="/img/products/pionono-choco-frutos.jpg"
                alt="Nuestra Cocina"
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, 50vw"
              />
            </div>
          </div>
        </section>
      )}

      {/* Testimonials Carousel */}
      {isVisible('testimonials') && <TestimonialCarousel />}

      {/* Customer Reviews */}
      <ReviewsSection />

      {/* Contact Info Section */}
      {isVisible('contact') && (
        <section className="py-16 bg-white" id="contacto">
          <div className="container mx-auto px-4">
            <h2 className="text-4xl font-fredoka font-bold text-primary text-center mb-2">Realiza tu Pedido</h2>
            <p className="text-center text-secondary font-medium mb-12 uppercase tracking-widest text-xs">Llevamos tus antojitos a tu puerta. ¡Envío gratis en Surco!</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {[
                { icon: '📱', title: 'Pedidos WhatsApp', desc: '+51 965 968 723', highlight: false },
                { icon: '⏰', title: 'Horario de Atención', desc: 'Lun - Sab: 9:00 - 20:00', highlight: false },
                { icon: '📍', title: 'Zona de Cobertura', desc: 'Surco (Envío Gratis) y Lima', highlight: false },
                { icon: '💳', title: 'Pago Contra Entrega', desc: 'Yape, Plin o Efectivo', highlight: true },
              ].map((card, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-4 p-6 rounded-2xl shadow-md border transition-transform hover:-translate-y-1 ${card.highlight
                    ? 'bg-secondary text-primary border-secondary'
                    : 'bg-paper border-primary/5'
                    }`}
                >
                  <span className="text-3xl">{card.icon}</span>
                  <div>
                    <h3 className="font-bold text-sm">{card.title}</h3>
                    <p className={`text-sm ${card.highlight ? 'text-primary/80' : 'text-gray-500'}`}>{card.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Como Funciona Section */}
      {isVisible('how-it-works') && (
        <section className="py-20 bg-gray-50 relative overflow-hidden" id="como-funciona">
          <div className="container mx-auto px-4 relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-fredoka font-bold text-primary mb-4">
                ¿Cómo hacer tu <span className="text-accent">pedido?</span>
              </h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Tu antojito favorito está a solo 3 pasos de distancia. Rápido, fácil y seguro.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {[
                { step: '1', title: 'Elige tu Antojo', desc: 'Navega por nuestro menú y agrega a tu carrito jugos, empadas o postres.', icon: '📜' },
                { step: '2', title: 'Confirma y Paga', desc: 'Ingresa tus datos y paga fácil con Yape, Plin o contra entrega.', icon: '📱' },
                { step: '3', title: 'Disfruta en Casa', desc: 'Preparamos tu pedido al momento y un repartidor lo lleva volando.', icon: '🛵' },
              ].map((item, i) => (
                <div key={i} className="bg-white rounded-3xl p-8 shadow-lg text-center hover:-translate-y-2 transition-transform duration-300 border border-gray-100">
                  <div className="w-16 h-16 mx-auto bg-amber-100 text-3xl flex items-center justify-center rounded-2xl mb-6 shadow-inner">
                    {item.icon}
                  </div>
                  <h3 className="text-xl font-bold text-primary mb-3 font-fredoka">{item.step}. {item.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Instagram Gallery */}
      {isVisible('gallery') && (
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4 text-center">
            <p className="text-gray-400 mb-8 font-medium italic">Síguenos en Instagram @antojitosexpress</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {instagramImages.slice(1).map((img, idx) => (
                <div
                  key={img}
                  onClick={() => setLightboxIndex(idx + 1)}
                  className="aspect-square rounded-2xl overflow-hidden group relative cursor-pointer shadow-md hover:shadow-xl transition-all"
                >
                  <Image src={img} alt="Instagram post" fill className="object-cover group-hover:scale-110 transition-transform duration-500" sizes="(max-width: 768px) 50vw, 25vw" />
                  <div className="absolute inset-0 bg-primary/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-2xl">❤️</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <Lightbox
        images={instagramImages}
        index={lightboxIndex}
        onClose={() => setLightboxIndex(null)}
      />
    </>
  );
}
