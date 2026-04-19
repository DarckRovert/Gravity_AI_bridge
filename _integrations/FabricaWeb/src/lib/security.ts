/**
 * 🛡️ Security Utilities — Dulces Momentos
 */

/**
 * Sanitize user input by escaping HTML entities to prevent XSS.
 */
export function sanitizeInput(input: string): string {
    if (!input) return '';
    return input
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
        .replace(/on\w+=/gi, ""); // Strip event handlers like onclick, onmouseover
}

/**
 * Validate that a Peruvian phone number is correctly formatted.
 * Must start with 9 and be exactly 9 digits.
 */
export function validatePeruvianPhone(phone: string): boolean {
    return /^9\d{8}$/.test(phone.replace(/\s/g, ''));
}

/**
 * Validate that an input string does not exceed a maximum length.
 * Returns the trimmed input if valid, or null if it exceeds the limit.
 */
export function validateInputLength(input: string, maxLength: number): string | null {
    const trimmed = input.trim();
    if (trimmed.length > maxLength) return null;
    return trimmed;
}

/**
 * Sanitize a filename for safe storage.
 * Removes path traversal characters and special symbols.
 */
export function sanitizeFileName(name: string): string {
    return name
        .replace(/[^a-zA-Z0-9._-]/g, '_')
        .replace(/\.\.+/g, '.')
        .replace(/^\./, '_')
        .substring(0, 100);
}
