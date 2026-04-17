"use client";

import { useSiteConfig } from '@/context/SiteConfigContext';
import { themePresets } from '@/lib/themeEngine';

interface QuickThemeEditorProps {
    onToast?: (msg: string, type: 'success' | 'error') => void;
}

export function QuickThemeEditor({ onToast }: QuickThemeEditorProps) {
    const { config, setTheme, resetTheme } = useSiteConfig();
    const currentTheme = config?.theme;
    const isDark = currentTheme?.darkMode ?? false;

    const handlePreset = (presetKey: string) => {
        const preset = themePresets[presetKey];
        if (!preset) return;
        setTheme({
            primary: preset.primary,
            secondary: preset.secondary,
            accent: preset.accent,
            paper: preset.paper,
        });
        onToast?.(`Tema "${preset.label}" aplicado`, 'success');
    };

    const handleToggleDark = () => {
        setTheme({ darkMode: !isDark });
        onToast?.(`Modo ${isDark ? 'claro' : 'oscuro'} activado`, 'success');
    };

    const handleColorChange = (field: 'primary' | 'secondary' | 'accent' | 'paper', value: string) => {
        setTheme({ [field]: value });
    };

    const handleReset = () => {
        resetTheme();
        onToast?.('Tema restaurado al original', 'success');
    };

    const presetKeys = Object.keys(themePresets);

    // Current theme values for preview
    const primary = currentTheme?.primary || '#4E342E';
    const secondary = currentTheme?.secondary || '#D4AF37';
    const accent = currentTheme?.accent || '#FF6B6B';
    const paper = currentTheme?.paper || '#FFF8F0';
    const borderRadius = currentTheme?.borderRadius || 'rounded';
    const radiusMap = { sharp: '0px', rounded: '12px', pill: '24px' };
    const radius = radiusMap[borderRadius] || '12px';

    return (
        <div className="space-y-6">
            {/* Live Preview Card */}
            <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
                <h2 className="text-xl font-playfair font-bold text-secondary mb-4">👁️ Preview en Vivo</h2>
                <div
                    className="border border-dash-border/30 overflow-hidden transition-all duration-500"
                    style={{
                        borderRadius: radius,
                        backgroundColor: isDark ? '#1a1a2e' : paper,
                    }}
                >
                    {/* Mini Header */}
                    <div
                        className="px-4 py-3 flex items-center justify-between transition-all duration-500"
                        style={{ backgroundColor: primary }}
                    >
                        <span className="text-white text-sm font-bold tracking-wide">{config?.content?.businessName || 'Mi Pastelería'}</span>
                        <div className="flex gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-white/30" />
                            <div className="w-2 h-2 rounded-full bg-white/30" />
                            <div className="w-2 h-2 rounded-full bg-white/50" />
                        </div>
                    </div>

                    {/* Mini Body */}
                    <div className="p-4 space-y-3">
                        <p className="text-xs font-medium" style={{ color: isDark ? '#e0e0e0' : '#333' }}>
                            Nuestros Productos Destacados
                        </p>

                        {/* Mini Product Cards */}
                        <div className="flex gap-2">
                            {[1, 2, 3].map(i => (
                                <div
                                    key={i}
                                    className="flex-1 p-2 transition-all duration-500"
                                    style={{
                                        borderRadius: radius,
                                        backgroundColor: isDark ? '#16213e' : '#fff',
                                        border: `1px solid ${isDark ? '#333' : '#eee'}`,
                                    }}
                                >
                                    <div
                                        className="w-full h-8 mb-1.5 transition-all duration-500"
                                        style={{
                                            borderRadius: `calc(${radius} - 4px)`,
                                            background: `linear-gradient(135deg, ${primary}33, ${secondary}33)`,
                                        }}
                                    />
                                    <div className="h-1.5 rounded-full mb-1" style={{ backgroundColor: isDark ? '#444' : '#ddd', width: '70%' }} />
                                    <div className="text-[9px] font-bold" style={{ color: secondary }}>
                                        S/ {(15 + i * 5).toFixed(2)}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Mini CTA Button */}
                        <button
                            className="w-full py-1.5 text-white text-[10px] font-bold transition-all duration-500"
                            style={{
                                borderRadius: radius,
                                background: `linear-gradient(135deg, ${secondary}, ${accent})`,
                            }}
                        >
                            Ver Catálogo Completo
                        </button>
                    </div>
                </div>
                <p className="text-dash-border text-[10px] text-center mt-2">Los cambios se reflejan en tiempo real ↑</p>
            </div>

            {/* Theme Controls */}
            <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-playfair font-bold text-secondary">🎨 Editor de Tema</h2>
                    <button
                        onClick={handleReset}
                        className="text-dash-border text-xs hover:text-red-400 transition-colors"
                    >
                        🔄 Restaurar
                    </button>
                </div>

                {/* Dark Mode Toggle */}
                <div className="flex items-center justify-between bg-dash-bg/50 rounded-xl p-4 border border-dash-border/50 mb-6">
                    <div>
                        <p className="text-white text-sm font-medium">Modo Oscuro</p>
                        <p className="text-dash-border text-xs">{isDark ? 'Activado' : 'Desactivado'}</p>
                    </div>
                    <button
                        onClick={handleToggleDark}
                        className={`w-14 h-7 rounded-full transition-all relative ${isDark ? 'bg-secondary' : 'bg-dash-border/30'}`}
                    >
                        <span className={`absolute w-6 h-6 bg-white rounded-full top-0.5 transition-all flex items-center justify-center text-xs ${isDark ? 'left-7' : 'left-0.5'}`}>
                            {isDark ? '🌙' : '☀️'}
                        </span>
                    </button>
                </div>

                {/* Color Pickers */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                    <div className="bg-dash-bg/50 rounded-xl p-3 border border-dash-border/50">
                        <label className="text-dash-border text-xs uppercase tracking-wider">Primario</label>
                        <div className="flex items-center gap-2 mt-2">
                            <input
                                type="color"
                                value={primary}
                                onChange={e => handleColorChange('primary', e.target.value)}
                                className="w-8 h-8 rounded cursor-pointer border-0"
                            />
                            <span className="text-white text-xs font-mono">{primary}</span>
                        </div>
                    </div>
                    <div className="bg-dash-bg/50 rounded-xl p-3 border border-dash-border/50">
                        <label className="text-dash-border text-xs uppercase tracking-wider">Secundario</label>
                        <div className="flex items-center gap-2 mt-2">
                            <input
                                type="color"
                                value={secondary}
                                onChange={e => handleColorChange('secondary', e.target.value)}
                                className="w-8 h-8 rounded cursor-pointer border-0"
                            />
                            <span className="text-white text-xs font-mono">{secondary}</span>
                        </div>
                    </div>
                    <div className="bg-dash-bg/50 rounded-xl p-3 border border-dash-border/50">
                        <label className="text-dash-border text-xs uppercase tracking-wider">Acento</label>
                        <div className="flex items-center gap-2 mt-2">
                            <input
                                type="color"
                                value={accent}
                                onChange={e => handleColorChange('accent', e.target.value)}
                                className="w-8 h-8 rounded cursor-pointer border-0"
                            />
                            <span className="text-white text-xs font-mono">{accent}</span>
                        </div>
                    </div>
                    <div className="bg-dash-bg/50 rounded-xl p-3 border border-dash-border/50">
                        <label className="text-dash-border text-xs uppercase tracking-wider">Fondo</label>
                        <div className="flex items-center gap-2 mt-2">
                            <input
                                type="color"
                                value={paper}
                                onChange={e => handleColorChange('paper', e.target.value)}
                                className="w-8 h-8 rounded cursor-pointer border-0"
                            />
                            <span className="text-white text-xs font-mono">{paper}</span>
                        </div>
                    </div>
                </div>

                {/* Preset Gallery */}
                <p className="text-dash-border text-xs uppercase tracking-wider mb-3">Presets Rápidos</p>
                <div className="grid grid-cols-3 gap-2">
                    {presetKeys.map(key => {
                        const preset = themePresets[key];
                        return (
                            <button
                                key={key}
                                onClick={() => handlePreset(key)}
                                className="bg-dash-bg/50 border border-dash-border/50 rounded-xl p-3 text-center hover:border-secondary/50 transition-all group"
                            >
                                <div className="flex justify-center gap-1 mb-2">
                                    <div className="w-4 h-4 rounded-full border border-white/10" style={{ backgroundColor: preset.primary }} />
                                    <div className="w-4 h-4 rounded-full border border-white/10" style={{ backgroundColor: preset.secondary }} />
                                </div>
                                <span className="text-white text-[11px] group-hover:text-secondary transition-colors">{preset.label}</span>
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
