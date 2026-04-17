"use client";

import { useState, useRef, useCallback } from 'react';
import { processAndStoreImage } from '@/lib/imageStore';
import { pastelitoEngine, ExtractedEntities } from '@/lib/pastelitoEngine';

interface ImageUploadResult {
    type: 'admin_product' | 'customer_ack' | 'resource_saved' | 'error';
    message: string;
    pendingConfirmation?: boolean;
    entities?: ExtractedEntities;
}

/**
 * Hook that encapsulates all file upload logic for the chatbot.
 * Handles admin product creation, customer image ack, and generic file storage.
 */
export function useChatImageUpload() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    }, []);

    const openFilePicker = useCallback(() => {
        fileInputRef.current?.click();
    }, []);

    const clearFile = useCallback(() => {
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    }, []);

    /**
     * Process the selected file based on context (admin vs customer, image vs other).
     */
    const processFile = useCallback(async (
        file: File,
        userText: string,
        isAdmin: boolean
    ): Promise<ImageUploadResult> => {
        const isImage = file.type.startsWith('image/');

        if (isImage && isAdmin) {
            try {
                const imageDataUrl = await processAndStoreImage(file);

                const fileName = file.name.toLowerCase();
                const isFoodImage = /cake|torta|pastel|pionono|alfajor|postre|dulce|chocolate/i.test(fileName);

                // Persist resource metadata
                const newResource = {
                    id: Date.now().toString(),
                    name: file.name,
                    type: file.type,
                    tags: isFoodImage ? ['food', 'bakery'] : ['image'],
                    date: new Date().toISOString(),
                    isNFT: false,
                };
                const existing = JSON.parse(localStorage.getItem('dm_resources') || '[]');
                localStorage.setItem('dm_resources', JSON.stringify([...existing, newResource]));

                if (imageDataUrl) {
                    const baseName = file.name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ');
                    const userCommand = userText || `agrega producto ${baseName}`;
                    const parseResult = pastelitoEngine.parse(userCommand, true);

                    const productName = parseResult.entities.product || baseName;
                    const category = parseResult.entities.category || (isFoodImage ? 'bocaditos' : 'tortas');
                    const price = parseResult.entities.price || 0;

                    const fullEntities: ExtractedEntities = {
                        ...parseResult.entities,
                        product: productName,
                        image: imageDataUrl,
                        category: category,
                        price: price,
                        rawText: userCommand,
                    };

                    pastelitoEngine.remember('lastConfirmedIntent', 'agregar_producto');
                    pastelitoEngine.setPending('agregar_producto', fullEntities, `Agregar ${productName} a ${category}`, 'medium');

                    const priceNote = price > 0 ? ` a **S/${price.toFixed(2)}**` : '';
                    return {
                        type: 'admin_product',
                        message:
                            `📷 **Producto detectado:**\n` +
                            `• Nombre: **${productName}**\n` +
                            `• Categoría: **${category}**${priceNote}\n` +
                            `• Imagen: ✅ Capturada\n\n` +
                            `¿Confirmas agregar este producto al catálogo? (Sí/No)`,
                        pendingConfirmation: true,
                        entities: fullEntities,
                    };
                } else {
                    return {
                        type: 'error',
                        message: `¡Recibido! 💾 Guardado en recursos.\n\n⚠️ No pude almacenar la imagen (espacio insuficiente).`,
                    };
                }
            } catch (error) {
                console.error(error);
                return {
                    type: 'error',
                    message: `¡Recibido! 💾 (No pude analizar la imagen, pero está guardada).`,
                };
            }
        } else if (isImage) {
            // Customer: simple ack
            return {
                type: 'customer_ack',
                message: `📸 ¡Bonita imagen! Si necesitas pedir algo, escríbenos qué te gustaría. 🧁`,
            };
        } else {
            // Non-image file
            const newResource = {
                id: Date.now().toString(),
                name: file.name,
                type: file.type,
                date: new Date().toISOString(),
            };
            const existing = JSON.parse(localStorage.getItem('dm_resources') || '[]');
            localStorage.setItem('dm_resources', JSON.stringify([...existing, newResource]));

            return {
                type: 'resource_saved',
                message: `¡Recibido! 💾 He guardado "${file.name}" en mi banco de recursos. (ID: ${newResource.id})`,
            };
        }
    }, []);

    return {
        selectedFile,
        fileInputRef,
        handleFileSelect,
        openFilePicker,
        clearFile,
        processFile,
    };
}
