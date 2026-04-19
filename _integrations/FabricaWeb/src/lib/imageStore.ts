// 📷 ImageStore — Persistencia y compresión de imágenes para Pastelito IA
// Convierte archivos a base64 Data URLs, comprime, y almacena en localStorage.

const STORAGE_PREFIX = 'pastelito_img_';
const MAX_WIDTH = 800;
const QUALITY = 0.7;
const MAX_STORAGE_MB = 4; // Límite seguro para localStorage

/**
 * Convierte un File a Data URL (base64)
 */
export const fileToDataUrl = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

/**
 * Comprime una imagen Data URL redimensionándola y reduciendo calidad.
 * Usa canvas para procesar en el navegador.
 */
export const compressImage = (
    dataUrl: string,
    maxWidth: number = MAX_WIDTH,
    quality: number = QUALITY
): Promise<string> => {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            let { width, height } = img;

            // Escalar proporcionalmente si excede maxWidth
            if (width > maxWidth) {
                height = Math.round((height * maxWidth) / width);
                width = maxWidth;
            }

            canvas.width = width;
            canvas.height = height;

            const ctx = canvas.getContext('2d');
            if (!ctx) {
                reject(new Error('No se pudo crear contexto de canvas'));
                return;
            }

            ctx.drawImage(img, 0, 0, width, height);

            // Convertir a JPEG comprimido (o WebP si el navegador lo soporta)
            const compressed = canvas.toDataURL('image/jpeg', quality);
            resolve(compressed);
        };
        img.onerror = reject;
        img.src = dataUrl;
    });
};

/**
 * Almacena una imagen comprimida en localStorage.
 * @returns true si se guardó correctamente, false si no hay espacio.
 */
export const storeImage = (id: string, dataUrl: string): boolean => {
    try {
        // Verificar espacio disponible aproximado
        const currentSize = getStorageUsage();
        const newSize = dataUrl.length * 2; // Cada char = 2 bytes en JS

        if (currentSize + newSize > MAX_STORAGE_MB * 1024 * 1024) {
            console.warn('📷 ImageStore: No hay espacio suficiente en localStorage');
            return false;
        }

        localStorage.setItem(`${STORAGE_PREFIX}${id}`, dataUrl);
        return true;
    } catch (error) {
        console.error('📷 ImageStore: Error al guardar', error);
        return false;
    }
};

/**
 * Recupera una imagen de localStorage por su ID.
 */
export const getImage = (id: string): string | null => {
    return localStorage.getItem(`${STORAGE_PREFIX}${id}`);
};

/**
 * Elimina una imagen de localStorage.
 */
export const removeImage = (id: string): void => {
    localStorage.removeItem(`${STORAGE_PREFIX}${id}`);
};

/**
 * Lista todas las imágenes almacenadas.
 */
export const listImages = (): { id: string; sizeKB: number }[] => {
    const images: { id: string; sizeKB: number }[] = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(STORAGE_PREFIX)) {
            const value = localStorage.getItem(key) || '';
            images.push({
                id: key.replace(STORAGE_PREFIX, ''),
                sizeKB: Math.round((value.length * 2) / 1024),
            });
        }
    }
    return images;
};

/**
 * Pipeline completo: File → compresión → almacenamiento
 * Retorna el Data URL comprimido o null si falló.
 */
export const processAndStoreImage = async (
    file: File,
    id?: string
): Promise<string | null> => {
    try {
        const rawDataUrl = await fileToDataUrl(file);
        const compressed = await compressImage(rawDataUrl);

        const imageId = id || `product_${Date.now()}`;
        const stored = storeImage(imageId, compressed);

        if (!stored) {
            console.warn('📷 ImageStore: Imagen no almacenada (sin espacio), pero se retorna el data URL');
        }

        return compressed;
    } catch (error) {
        console.error('📷 ImageStore: Error en pipeline', error);
        return null;
    }
};

/**
 * Calcula el uso actual de localStorage en bytes.
 */
function getStorageUsage(): number {
    let total = 0;
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
            const value = localStorage.getItem(key) || '';
            total += (key.length + value.length) * 2; // UTF-16 = 2 bytes/char
        }
    }
    return total;
}
