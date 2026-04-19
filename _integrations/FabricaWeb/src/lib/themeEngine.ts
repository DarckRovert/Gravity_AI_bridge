// ⚡ ThemeEngine — El Pintor de Pastelito God Mode
// Transforma la apariencia de la página en tiempo real

export interface ThemePreset {
    name: string;
    label: string;
    emoji: string;
    primary: string;
    secondary: string;
    accent: string;
    paper: string;
}

export const themePresets: Record<string, ThemePreset> = {
    original: { name: 'original', label: 'Original', emoji: '🏠', primary: '#4E342E', secondary: '#D4AF37', accent: '#C2185B', paper: '#FFF8E1' },
    navidad: { name: 'navidad', label: 'Navidad', emoji: '🎄', primary: '#1B5E20', secondary: '#C62828', accent: '#FFD54F', paper: '#FFF3E0' },
    coquette: { name: 'coquette', label: 'Coquette', emoji: '💗', primary: '#F48FB1', secondary: '#CE93D8', accent: '#F06292', paper: '#FCE4EC' },
    elegante: { name: 'elegante', label: 'Elegante', emoji: '🖤', primary: '#212121', secondary: '#FFD700', accent: '#B71C1C', paper: '#FAFAFA' },
    oceano: { name: 'oceano', label: 'Océano', emoji: '🌊', primary: '#0D47A1', secondary: '#00BCD4', accent: '#FF6F00', paper: '#E3F2FD' },
    tropical: { name: 'tropical', label: 'Tropical', emoji: '🌴', primary: '#E65100', secondary: '#FFAB00', accent: '#00C853', paper: '#FFF8E1' },
    sakura: { name: 'sakura', label: 'Sakura', emoji: '🌸', primary: '#AD1457', secondary: '#F8BBD0', accent: '#880E4F', paper: '#FFF0F5' },
    midnight: { name: 'midnight', label: 'Midnight', emoji: '🌙', primary: '#1A1A2E', secondary: '#E94560', accent: '#0F3460', paper: '#16213E' },
    san_valentin: { name: 'san_valentin', label: 'San Valentín', emoji: '💝', primary: '#C62828', secondary: '#F48FB1', accent: '#FF1744', paper: '#FCE4EC' },
    patrio: { name: 'patrio', label: 'Fiestas Patrias', emoji: '🇵🇪', primary: '#D32F2F', secondary: '#FFFFFF', accent: '#C62828', paper: '#FFF8E1' },
};

// Diccionario de colores naturales en español
export const colorDictionary: Record<string, string> = {
    'rojo': '#C62828',
    'azul': '#1565C0',
    'azul marino': '#0D47A1',
    'azul cielo': '#03A9F4',
    'rosa': '#E91E63',
    'rosado': '#F48FB1',
    'verde': '#2E7D32',
    'verde oscuro': '#1B5E20',
    'dorado': '#FFD700',
    'oro': '#FFD700',
    'negro': '#212121',
    'morado': '#7B1FA2',
    'violeta': '#6A1B9A',
    'turquesa': '#00BCD4',
    'naranja': '#E65100',
    'amarillo': '#F9A825',
    'plateado': '#9E9E9E',
    'plata': '#9E9E9E',
    'coral': '#FF7043',
    'lavanda': '#7E57C2',
    'esmeralda': '#00897B',
    'burdeos': '#880E4F',
    'crema': '#FFF8E1',
    'marfil': '#FFFFF0',
    'salmon': '#FF8A65',
    'vino': '#6A1B9A',
    'blanco': '#FFFFFF',
    'gris': '#757575',
    'café': '#4E342E',
    'chocolate': '#3E2723',
    'beige': '#F5F5DC',
    'menta': '#00BFA5',
    'celeste': '#81D4FA',
    'fucsia': '#F50057',
    'magenta': '#E91E63',
};

export class ThemeEngine {
    /**
     * Resolve a natural language color name to a hex code.
     * Returns null if not found.
     */
    parseColor(input: string): string | null {
        const normalized = input.toLowerCase().trim();

        // Direct hex match
        if (/^#[0-9a-f]{6}$/i.test(normalized)) return normalized;

        // Check dictionary
        if (colorDictionary[normalized]) return colorDictionary[normalized];

        // Partial match — find the closest key
        const partial = Object.entries(colorDictionary).find(([key]) =>
            key.includes(normalized) || normalized.includes(key)
        );
        if (partial) return partial[1];

        return null;
    }

    /**
     * Find a preset by natural language name
     */
    findPreset(input: string): ThemePreset | null {
        const normalized = input.toLowerCase().trim()
            .replace(/é/g, 'e').replace(/á/g, 'a').replace(/í/g, 'i')
            .replace(/ó/g, 'o').replace(/ú/g, 'u').replace(/ñ/g, 'n');

        // Direct match
        if (themePresets[normalized]) return themePresets[normalized];

        // Fuzzy match based on label or name
        for (const preset of Object.values(themePresets)) {
            const presetNorm = preset.label.toLowerCase()
                .replace(/é/g, 'e').replace(/á/g, 'a').replace(/í/g, 'i')
                .replace(/ó/g, 'o').replace(/ú/g, 'u').replace(/ñ/g, 'n');

            if (presetNorm.includes(normalized) || normalized.includes(presetNorm)) {
                return preset;
            }
            if (normalized.includes(preset.name)) return preset;
        }

        // Alias mapping
        const aliases: Record<string, string> = {
            'navideño': 'navidad', 'christmas': 'navidad',
            'rosa': 'coquette', 'kawaii': 'coquette', 'cute': 'coquette',
            'lujo': 'elegante', 'luxury': 'elegante', 'premium': 'elegante', 'dark': 'elegante',
            'mar': 'oceano', 'ocean': 'oceano', 'marino': 'oceano', 'azul': 'oceano',
            'selva': 'tropical', 'jungle': 'tropical', 'calido': 'tropical',
            'japan': 'sakura', 'japones': 'sakura', 'floral': 'sakura', 'flores': 'sakura',
            'noche': 'midnight', 'nocturno': 'midnight', 'night': 'midnight',
            'amor': 'san_valentin', 'valentine': 'san_valentin', 'love': 'san_valentin', 'corazon': 'san_valentin',
            'peru': 'patrio', 'peruano': 'patrio', 'fiestas': 'patrio', 'patria': 'patrio',
            'default': 'original', 'normal': 'original', 'clasico': 'original', 'reset': 'original',
        };

        for (const [alias, presetName] of Object.entries(aliases)) {
            if (normalized.includes(alias)) return themePresets[presetName];
        }

        return null;
    }

    /**
     * Get all available presets for listing
     */
    getAllPresets(): ThemePreset[] {
        return Object.values(themePresets);
    }
}

export const themeEngine = new ThemeEngine();
