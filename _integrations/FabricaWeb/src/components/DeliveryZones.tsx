"use client";

import { useDeliveryZones } from '@/context/SiteConfigContext';

export default function DeliveryZones() {
    const { zones } = useDeliveryZones();

    return (
        <section id="delivery" className="py-20 bg-paper">
            <div className="container mx-auto px-4">
                <div className="text-center mb-12">
                    <h2 className="text-3xl md:text-4xl font-playfair font-bold text-primary mb-4">Zonas de Delivery</h2>
                    <p className="text-gray-600 max-w-2xl mx-auto">Llevamos nuestros postres a tu puerta en toda Lima con el mayor cuidado.</p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
                    {zones.map(zone => (
                        <div key={zone.name} className={`${zone.color} p-6 rounded-2xl border border-primary/5 shadow-sm hover:shadow-md transition-all text-center group`}>
                            <div className="text-3xl mb-3 group-hover:scale-110 transition-transform">{zone.icon}</div>
                            <h3 className="font-bold text-primary mb-1">{zone.name}</h3>
                            <p className="text-xs font-bold text-secondary mb-2">{zone.price}</p>
                            <p className="text-[10px] text-gray-400 leading-tight">{zone.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
