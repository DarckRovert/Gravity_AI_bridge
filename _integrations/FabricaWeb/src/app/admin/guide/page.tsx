"use client";

import React from 'react';
import Link from 'next/link';

export default function AdminGuidePage() {
    return (
        <div className="min-h-screen bg-paper text-primary p-8 font-sans">
            <div className="max-w-3xl mx-auto bg-white p-10 rounded-3xl shadow-xl border border-primary/10">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold font-playfair text-primary">🦊 Guía de Conexión Web3</h1>
                    <Link href="/admin" className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm font-bold transition">
                        ⬅️ Volver al Dashboard
                    </Link>
                </div>

                <div className="prose prose-stone max-w-none">
                    <p className="lead text-lg mb-6">Esta guía te ayudará a conectar <strong>PastelChain</strong> con billeteras digitales, permitiéndote acuñar NFTs y gestionar la identidad de tu negocio.</p>

                    <hr className="my-8 border-primary/10" />

                    <h2 className="text-2xl font-bold mb-4 text-purple-800">🦊 Opción 1: Metamask (PC/Laptop)</h2>
                    <p className="mb-4">Ideal para cuando administras la tienda desde una computadora de escritorio.</p>
                    <ol className="list-decimal pl-5 space-y-2 mb-6">
                        <li><strong>Instalar</strong>: Descarga la extensión de <a href="https://metamask.io" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Metamask.io</a> para Chrome o Edge.</li>
                        <li><strong>Crear cuenta</strong>: Sigue los pasos para crear tu billetera (guarda bien tus 12 palabras clave).</li>
                        <li><strong>Conectar</strong>:
                            <ul className="list-disc pl-5 mt-1 text-gray-600">
                                <li>En Antojitos Express, haz clic en el botón <strong>"Conectar Wallet"</strong> (esquina superior derecha).</li>
                                <li>Selecciona <strong>Metamask</strong>.</li>
                                <li>Aprueba la conexión en la ventana emergente.</li>
                            </ul>
                        </li>
                    </ol>
                    <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200 text-sm mb-8">
                        <strong>💡 Nota:</strong> Usamos la red <strong>Polygon Amoy (Testnet)</strong> para pruebas gratuitas.
                    </div>

                    <hr className="my-8 border-primary/10" />

                    <h2 className="text-2xl font-bold mb-4 text-gray-900">🌍 Opción 2: World App (Celular)</h2>
                    <p className="mb-4">Ideal para identificarte con tu <strong>World ID</strong> (prueba de humanidad) y gestionar el negocio desde el móvil.</p>

                    <h3 className="text-xl font-bold mb-3 mt-6">🔑 Paso 0: Configuración Previa (Solo una vez)</h3>
                    <p className="mb-4">Para que el código QR funcione, necesitamos un <strong>Project ID</strong> de WalletConnect.</p>
                    <ol className="list-decimal pl-5 space-y-2 mb-6">
                        <li>Ve a <a href="https://cloud.reown.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Reown Cloud</a> (antes WalletConnect).</li>
                        <li>Regístrate (es gratis).</li>
                        <li>Crea un nuevo proyecto llamado "Antojitos Express".</li>
                        <li>Copia el <strong>Project ID</strong>.</li>
                        <li>Abre el archivo <code>.env.local</code> (o créalo si no existe) en la raíz del proyecto.</li>
                        <li>Agrega la línea: <code>NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=TU_ID_AQUI</code>.</li>
                    </ol>

                    <h3 className="text-xl font-bold mb-3 mt-6">📱 Conexión Diaria</h3>
                    <ol className="list-decimal pl-5 space-y-2 mb-6">
                        <li>Abre la <strong>World App</strong> en tu celular.</li>
                        <li>En Antojitos Express (PC), haz clic en <strong>"Conectar Wallet"</strong>.</li>
                        <li>Selecciona <strong>"WalletConnect"</strong> (o aparecerá el código QR automáticamente).</li>
                        <li>Escanea el QR con tu World App.</li>
                        <li>Autoriza la conexión en tu celular.</li>
                    </ol>
                </div>
            </div>
        </div>
    );
}
