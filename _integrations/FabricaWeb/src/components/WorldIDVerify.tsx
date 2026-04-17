"use client";

import { IDKitWidget, VerificationLevel, ISuccessResult } from '@worldcoin/idkit';
import { useToast } from '@/context/ToastContext';

/**
 * 🌎 Worldcoin Verification Component
 * Ensures "One Person, One Reward" for Dulces Momentos.
 */
export default function WorldIDVerify() {
    const { showToast } = useToast();

    const handleVerify = async (proof: ISuccessResult) => {
        // En un entorno real, enviaríamos este 'proof' a nuestro backend
        // para validarlo con la API de Worldcoin.
        console.log("Proof received from World ID:", proof);

        // Simulación de validación exitosa
        const response = await fetch('/api/verify-human', {
            method: 'POST',
            body: JSON.stringify(proof),
        });

        if (response.ok) {
            showToast("¡Humano Verificado! 🍰 Has desbloqueado el cupón: HUMANO10", "success");
        }
    };

    const onSuccess = () => {
        // Acciones tras cerrar el modal con éxito
        localStorage.setItem('pastelito_human_verified', 'true');
    };

    return (
        <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-3xl border border-blue-100 shadow-inner">
            <div className="flex flex-col items-center text-center space-y-4">
                <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-md">
                    <span className="text-3xl">🌎</span>
                </div>
                <div>
                    <h3 className="text-lg font-bold text-indigo-900 leading-tight">Prueba de Humanidad</h3>
                    <p className="text-xs text-indigo-700/70">
                        Verifícate con World ID para obtener beneficios exclusivos y evitar el spam de bots.
                    </p>
                </div>

                <IDKitWidget
                    app_id="app_f46e5db6f7c46cfaa400aefc65f52c99" // Dulces Momentos Official App ID
                    action="verify-human-customer"
                    onSuccess={onSuccess}
                    handleVerify={handleVerify}
                    verification_level={VerificationLevel.Device} // O 'Orb' para máxima seguridad
                >
                    {({ open }: { open: () => void }) => (
                        <button
                            onClick={open}
                            className="bg-indigo-600 text-white px-6 py-2 rounded-full font-bold text-sm hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200"
                        >
                            Verificar mi identitad
                        </button>
                    )}
                </IDKitWidget>

                <p className="text-[9px] text-indigo-400 font-medium">✨ Privacidad garantizada por Prueba de Conocimiento Cero (ZKP)</p>
            </div>
        </div>
    );
}
