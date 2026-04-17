import { CakeSelections } from '@/types/cake';

export function CakePreview({ selections }: { selections: CakeSelections }) {
    const { base, relleno, cobertura, tamano } = selections;

    // Colors mapping
    const baseColors: Record<string, string> = {
        'Vainilla': '#F3E5AB',
        'Chocolate': '#5D4037',
        'Marmoleado': '#D7CCC8',
        'Red Velvet': '#B71C1C',
        'Zanahoria': '#E65100',
    };

    const fillingColors: Record<string, string> = {
        'Manjar Blanco': '#8D6E63',
        'Fudge de la Casa': '#3E2723',
        'Crema Pastelera': '#FFF59D',
        'Queso Crema': '#FFF9C4',
    };

    const coverageColors: Record<string, string> = {
        'Chantilly': '#FFFFFF',
        'Buttercream': '#FFF176',
        'Fudge': '#3E2723',
        'Fondant': '#E91E63', // Pink fondant default
    };

    // Size scaling
    const scales: Record<string, number> = {
        'Pequeña (10 porc.)': 0.8,
        'Mediana (18 porc.)': 1,
        'Grande (25 porc.)': 1.2,
        'Castillo (40 porc.)': 1.4,
    };

    const scale = scales[tamano] || 1;
    const baseColor = baseColors[base] || '#E0E0E0';
    const fillingColor = fillingColors[relleno] || 'transparent';
    const coverageColor = coverageColors[cobertura] || 'transparent';

    return (
        <div className="flex items-center justify-center p-8 transition-all duration-500">
            <svg
                width="200"
                height="200"
                viewBox="0 0 200 200"
                style={{ transform: `scale(${scale})`, transition: 'transform 0.5s ease-out' }}
            >
                {/* Plate */}
                <ellipse cx="100" cy="170" rx="80" ry="20" fill="#EEEEEE" stroke="#BDBDBD" strokeWidth="2" />

                {/* Base Cake Layer 1 */}
                <path d="M40 120 L40 150 A60 15 0 0 0 160 150 L160 120" fill={baseColor} stroke="rgba(0,0,0,0.1)" strokeWidth="1" />
                <ellipse cx="100" cy="120" rx="60" ry="15" fill={baseColor} />

                {/* Filling Layer (Visible on side if naked, or just abstract) */}
                {relleno && (
                    <path d="M42 118 L42 125 A58 14 0 0 0 158 125 L158 118" fill={fillingColor} />
                )}

                {/* Base Cake Layer 2 (Top) */}
                <path d="M40 90 L40 120 A60 15 0 0 0 160 120 L160 90" fill={baseColor} stroke="rgba(0,0,0,0.1)" strokeWidth="1" />
                <ellipse cx="100" cy="90" rx="60" ry="15" fill={baseColor} />

                {/* Coverage / Topping */}
                {cobertura && (
                    <>
                        <path d="M38 80 L38 120 A62 16 0 0 0 162 120 L162 80" fill={coverageColor} opacity="0.9" />
                        <ellipse cx="100" cy="80" rx="62" ry="16" fill={coverageColor} />
                        {/* Drips if fudge */}
                        {cobertura.includes('Fudge') && (
                            <path d="M40 85 Q50 100 60 85 T80 85 T100 100 T120 85 T140 85 T160 100" stroke={coverageColor} strokeWidth="5" fill="none" />
                        )}
                        {/* Swirl if chantilly */}
                        {cobertura.includes('Chantilly') && (
                            <path d="M90 70 Q100 50 110 70" stroke="#EEE" strokeWidth="3" fill="none" />
                        )}
                    </>
                )}

                {/* Candle or decoration if finished */}
                {tamano && (
                    <text x="100" y="50" textAnchor="middle" fontSize="20">🕯️</text>
                )}
            </svg>
        </div>
    );
}
