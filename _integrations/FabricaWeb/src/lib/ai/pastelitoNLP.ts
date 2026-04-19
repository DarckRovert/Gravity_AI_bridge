// ================================================
// 🧠 PastelitoNLP — Motor de Inteligencia 100% Autónomo
// Sin dependencias externas: zero CDN, zero TensorFlow, zero HuggingFace.
// Especializado en español + dominio pastelero.
//
// Capacidades:
// 1. Normalización de texto (tildes, slang, typos)
// 2. Multi-strategy search (keyword, fuzzy, synonym, n-gram)
// 3. Intent classification (Naive Bayes mejorado)
// 4. Product search (fuzzy)
// 5. Context tracking (últimos mensajes)
// 6. Respuestas variadas (rotación de templates)
// ================================================

import { Product } from '@/data/products';
import { getCanonical, getSynonyms, SYNONYMS } from '@/data/synonyms';
import { customerKB, adminKB, KBItem, customerFlow } from '@/data/chatbot-kb';
import { FAQ_DB } from './knowledgeBase';
import goldenDataset from './distillation/golden_dataset.json';

// ========================
// 📝 TEXT PROCESSING
// ========================

const STOP_WORDS = new Set([
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'de', 'del', 'al', 'a', 'ante', 'con', 'en', 'para', 'por',
    'y', 'o', 'u', 'e', 'ni', 'que', 'es', 'son', 'fue', 'ser',
    'me', 'te', 'se', 'nos', 'le', 'les', 'lo', 'su', 'sus',
    'mi', 'tu', 'este', 'esta', 'ese', 'esa', 'pero', 'como',
    'mas', 'muy', 'ya', 'hay', 'tiene', 'hace', 'puede', 'si',
    'he', 'ha', 'han', 'era', 'eso', 'esto', 'sin',
]);

/** Normalize text: lowercase, remove accents, strip punctuation */
export function normalize(text: string): string {
    return text
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') // Remove accents
        .replace(/[¿¡!?.,:;'"()\[\]{}\-_]/g, ' ') // Punctuation → space
        .replace(/\s+/g, ' ')
        .trim();
}

/** Basic Spanish stemmer: strips common suffixes */
function stem(word: string): string {
    if (word.length <= 3) return word;
    // Diminutives: -ito, -ita, -itos, -itas
    if (/cit[oa]s?$/.test(word)) return word.replace(/cit[oa]s?$/, '');
    if (/it[oa]s?$/.test(word) && word.length > 5) return word.replace(/it[oa]s?$/, '');
    // Plurals
    if (word.endsWith('es') && word.length > 4) return word.slice(0, -2);
    if (word.endsWith('s') && word.length > 3) return word.slice(0, -1);
    // Gerund: -ando, -endo, -iendo
    if (/[aei]ndo$/.test(word)) return word.replace(/[aei]ndo$/, '');
    if (/iendo$/.test(word)) return word.replace(/iendo$/, '');
    return word;
}

/** Tokenize: normalize, split, remove stop words, stem */
export function tokenize(text: string): string[] {
    const words = normalize(text).split(' ');
    return words
        .filter(w => w.length > 1 && !STOP_WORDS.has(w))
        .map(w => stem(w));
}

/** Expand tokens with synonyms — returns both original and canonical forms */
export function expandTokens(tokens: string[]): string[] {
    const expanded = new Set<string>();
    for (const token of tokens) {
        expanded.add(token);
        // Try to find canonical form
        const canonical = getCanonical(token);
        expanded.add(canonical);
        expanded.add(stem(canonical));
        // Also add all synonyms of the canonical
        const syns = getSynonyms(canonical);
        for (const syn of syns) {
            const normSyn = normalize(syn);
            expanded.add(normSyn);
            expanded.add(stem(normSyn));
        }
    }
    return Array.from(expanded);
}

/** Generate bigrams from tokens */
function bigrams(tokens: string[]): string[] {
    const result: string[] = [];
    for (let i = 0; i < tokens.length - 1; i++) {
        result.push(`${tokens[i]} ${tokens[i + 1]}`);
    }
    return result;
}

// ========================
// 📏 FUZZY MATCHING (Levenshtein)
// ========================

function levenshtein(a: string, b: string): number {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    const matrix: number[][] = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            const cost = b[i - 1] === a[j - 1] ? 0 : 1;
            matrix[i][j] = Math.min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost
            );
        }
    }
    return matrix[b.length][a.length];
}

/** Check if two words are "fuzzy equal" (Levenshtein distance ≤ threshold) */
function fuzzyMatch(a: string, b: string, maxDist = 2): boolean {
    if (Math.abs(a.length - b.length) > maxDist) return false;
    return levenshtein(a, b) <= maxDist;
}

// ========================
// 🔍 MULTI-STRATEGY KB SEARCH
// ========================

interface SearchResult {
    item: KBItem;
    score: number;
    source: 'exact' | 'fuzzy' | 'synonym' | 'ngram' | 'token-overlap';
}

const FLOW_NODE_IDS = new Set(Object.keys(customerFlow));

/** Resolve a KB response that might be a flow node ID to actual text */
function resolveKBResponse(item: KBItem): string {
    const response = Array.isArray(item.response) ? item.response[0] : item.response;
    if (!response) return '';
    if (FLOW_NODE_IDS.has(response)) {
        const node = customerFlow[response];
        return node?.text || response;
    }
    return response;
}

/**
 * Multi-strategy search over KB entries.
 * Returns the BEST match across all strategies, with a normalized score 0-1.
 */
export function multiSearch(query: string, isAdmin: boolean): SearchResult | null {
    const kb = isAdmin ? adminKB : customerKB;
    const normQuery = normalize(query);
    const queryTokens = tokenize(query);
    const queryExpanded = expandTokens(queryTokens);
    const queryBigrams = bigrams(normalize(query).split(' ').filter(w => w.length > 1));

    let bestResult: SearchResult | null = null;
    let bestScore = 0;

    for (const item of kb) {
        let score = 0;
        let source: SearchResult['source'] = 'token-overlap';

        for (const key of item.keys) {
            const normKey = normalize(key);
            const keyTokens = normKey.split(' ').filter(w => w.length > 1);

            // Strategy 1: EXACT SUBSTRING match (highest priority)
            if (normQuery.includes(normKey) || normKey.includes(normQuery)) {
                const matchRatio = normKey.length / Math.max(normQuery.length, 1);
                const exactScore = 0.85 + (matchRatio * 0.15); // 0.85 - 1.0
                if (exactScore > score) {
                    score = exactScore;
                    source = 'exact';
                }
            }

            // Strategy 2: FUZZY match on individual keywords
            for (const keyToken of keyTokens) {
                for (const queryToken of queryTokens) {
                    if (fuzzyMatch(queryToken, keyToken, 2)) {
                        const dist = levenshtein(queryToken, keyToken);
                        const fuzzyScore = 0.7 - (dist * 0.1); // 0.7 for dist=0, 0.5 for dist=2
                        if (fuzzyScore > score) {
                            score = fuzzyScore;
                            source = 'fuzzy';
                        }
                    }
                }
            }

            // Strategy 3: SYNONYM expansion match
            for (const expanded of queryExpanded) {
                if (normKey.includes(expanded) || expanded.includes(normKey)) {
                    const synScore = 0.75;
                    if (synScore > score) {
                        score = synScore;
                        source = 'synonym';
                    }
                }
                // Also fuzzy-match synonyms against key tokens
                for (const keyToken of keyTokens) {
                    if (fuzzyMatch(expanded, keyToken, 1)) {
                        const synFuzzyScore = 0.65;
                        if (synFuzzyScore > score) {
                            score = synFuzzyScore;
                            source = 'synonym';
                        }
                    }
                }
            }

            // Strategy 4: N-GRAM match (bigrams)
            for (const qBigram of queryBigrams) {
                if (normKey.includes(qBigram) || qBigram.includes(normKey)) {
                    const ngramScore = 0.8;
                    if (ngramScore > score) {
                        score = ngramScore;
                        source = 'ngram';
                    }
                }
            }

            // Strategy 5: TOKEN OVERLAP scoring
            if (keyTokens.length > 0) {
                const stemmedKeyTokens = keyTokens.map(stem);
                const overlap = stemmedKeyTokens.filter(kt =>
                    queryExpanded.some(qt => qt === kt || fuzzyMatch(qt, kt, 1))
                ).length;
                const overlapRatio = overlap / stemmedKeyTokens.length;
                if (overlapRatio >= 0.5) {
                    const overlapScore = 0.5 + (overlapRatio * 0.25); // 0.5 - 0.75
                    if (overlapScore > score) {
                        score = overlapScore;
                        source = 'token-overlap';
                    }
                }
            }
        }

        if (score > bestScore) {
            bestScore = score;
            bestResult = { item, score, source };
        }
    }

    // Minimum threshold
    if (bestResult && bestResult.score >= 0.45) {
        return bestResult;
    }
    return null;
}

// ========================
// 🎯 INTENT CLASSIFIER (Enhanced Naive Bayes)
// ========================

interface IntentDef {
    label: string;
    examples: string[];
    responseTemplate?: string;
}

// Hard-coded intents + golden dataset distillation
const INTENTS: IntentDef[] = [
    {
        label: 'greeting',
        examples: ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hi', 'que tal', 'alo', 'hey', 'oye', 'saludos'],
        responseTemplate: undefined, // Multiple responses handled by RESPONSE_BANK
    },
    {
        label: 'farewell',
        examples: ['chau', 'adios', 'hasta luego', 'nos vemos', 'bye', 'me voy', 'chaito', 'hasta pronto'],
    },
    {
        label: 'thanks',
        examples: ['gracias', 'muchas gracias', 'mil gracias', 'te agradezco', 'thanks', 'genial', 'perfecto', 'excelente'],
    },
    {
        label: 'how_are_you',
        examples: ['como estas', 'como te va', 'que tal estas', 'como andas', 'todo bien', 'que onda'],
    },
    {
        label: 'who_are_you',
        examples: ['quien eres', 'que eres', 'como te llamas', 'tu nombre', 'eres real', 'eres un bot', 'eres humano', 'eres robot'],
    },
    {
        label: 'check_price',
        examples: ['cuanto cuesta', 'precio', 'valor', 'a como esta', 'costo', 'cotizar', 'quiero saber el precio', 'cuanto sale', 'que precio'],
    },
    {
        label: 'check_stock',
        examples: ['hay stock', 'tienes', 'queda', 'disponible', 'todavia hay', 'hay disponibilidad', 'tienen de eso'],
    },
    {
        label: 'recommendation',
        examples: ['que me recomiendas', 'que es lo mejor', 'cual es el mas rico', 'best seller', 'mas vendido', 'popular', 'favorito', 'sugerencia'],
    },
    {
        label: 'complaint',
        examples: ['queja', 'reclamo', 'problema', 'mal servicio', 'decepcion', 'insatisfecho', 'llego mal', 'no me gusto'],
    },
    {
        label: 'joke',
        examples: ['cuentame un chiste', 'chiste', 'algo gracioso', 'hazme reir', 'broma'],
    },
    {
        label: 'frustration',
        examples: ['no entiendo', 'no funciona', 'ayuda', 'esta mal', 'no carga', 'horrible', 'aburrido', 'auxilio', 'que paso', 'no sale'],
    },
    // Distilled golden dataset intents
    ...goldenDataset.map(item => ({
        label: item.intent,
        examples: [item.user_input],
        responseTemplate: item.student_response,
    })),
];

// --- Train Naive Bayes at module load ---
interface BayesModel {
    wordCounts: Record<string, Record<string, number>>;
    classCounts: Record<string, number>;
    totalDocs: number;
    vocabulary: Set<string>;
}

const bayesModel: BayesModel = {
    wordCounts: {},
    classCounts: {},
    totalDocs: 0,
    vocabulary: new Set(),
};

// Train phase
for (const intent of INTENTS) {
    if (!bayesModel.classCounts[intent.label]) bayesModel.classCounts[intent.label] = 0;
    for (const example of intent.examples) {
        bayesModel.classCounts[intent.label]++;
        bayesModel.totalDocs++;
        const tokens = tokenize(example);
        for (const token of tokens) {
            bayesModel.vocabulary.add(token);
            if (!bayesModel.wordCounts[intent.label]) bayesModel.wordCounts[intent.label] = {};
            bayesModel.wordCounts[intent.label][token] = (bayesModel.wordCounts[intent.label][token] || 0) + 1;
        }
    }
}

/** Predict intent via Naive Bayes */
function predictIntent(text: string): { label: string; score: number } {
    const tokens = tokenize(text);
    const expanded = expandTokens(tokens); // Include synonym-expanded tokens
    let bestLabel = 'unknown';
    let maxScore = -Infinity;
    const vocabSize = bayesModel.vocabulary.size;

    for (const intent of INTENTS) {
        let score = Math.log((bayesModel.classCounts[intent.label] || 0.1) / bayesModel.totalDocs);
        let wordMatches = 0;

        for (const token of expanded) {
            const wordCount = bayesModel.wordCounts[intent.label]?.[token] || 0;
            const totalWords = Object.values(bayesModel.wordCounts[intent.label] || {}).reduce((a, b) => a + b, 0);

            if (bayesModel.vocabulary.has(token)) {
                score += Math.log((wordCount + 1) / (totalWords + vocabSize));
                if (wordCount > 0) wordMatches++;
            }
        }

        // Penalize if no word matches at all
        if (wordMatches === 0) score = -Infinity;

        if (score > maxScore) {
            maxScore = score;
            bestLabel = intent.label;
        }
    }

    return { label: bestLabel, score: maxScore };
}

// ========================
// 🏦 RESPONSE BANK (Multiple templates per intent)
// ========================

const RESPONSE_BANK: Record<string, string[]> = {
    greeting: [
        "¡Hola! 👋 Soy Antojín, tu asistente rápido. ¿En qué puedo calmar tu antojo hoy?",
        "¡Buenas! 🍍 Aquí Antojín a tu servicio. ¿Se te antoja algo rico hoy?",
        "¡Hey! 👋 Bienvenido a Antojitos Express. ¿Qué te provoca hoy? 🥤",
        "¡Hola, hola! 😋 ¿Listo para probar algo delicioso? Cuéntame, ¿qué necesitas?",
    ],
    farewell: [
        "¡Chau! 👋 Fue un gusto atenderte. ¡Que tengas un día excelente! ✨",
        "¡Nos vemos! 🍍 Aquí estaré cuando se te antoje algo rico.",
        "¡Hasta pronto! 💕 No olvides que siempre puedes volver por más.",
    ],
    thanks: [
        "¡De nada! 😊 Para eso estoy. ¿Algo más en que pueda ayudarte?",
        "¡Un placer! 🍍 Si necesitas algo más, aquí me tienes.",
        "¡Gracias a ti! 💕 Espero haberte sido de ayuda. ¡Vuelve pronto!",
    ],
    how_are_you: [
        "¡Muy bien, gracias! 😊 Siempre listo para ayudarte. ¿Qué se te ofrece hoy?",
        "¡De maravilla! 🍍 Aquí listo para armar tu pedido. ¿En qué te ayudo?",
        "¡Feliz y con energía! 🥤 Cuéntame, ¿qué necesitas?",
    ],
    who_are_you: [
        "¡Soy Antojín! 🍍 El asistente virtual de **Antojitos Express**. Te ayudo a explorar nuestros productos, hacer pedidos y resolver tus dudas. ¡Pregúntame lo que quieras!",
        "Me llamo **Antojín** 🤖🍍 — soy el cerebro de esta fuente de soda. Puedo mostrarte el menú, decirte precios, rastrear tu pedido y mucho más.",
    ],
    recommendation: [
        "🏆 ¡Nuestros best sellers son:\n1. 🥖 **Pan con Chicharrón** — El clásico peruano\n2. 🥤 **Jugo Surtido** — Fresco y natural\n3. 🥟 **Empanada de Carne** — Horneada al momento\n\n¿Cuál te tienta? 😋",
        "😋 Te recomiendo probar nuestro **Papapan con Chicharrón** — es el más pedido por algo. ¡Puro sabor! Si prefieres algo más ligero, el **Jugo Especial** es una delicia.",
    ],
    complaint: [
        "😔 Lamento mucho escuchar eso. Tu satisfacción es lo más importante para nosotros. Por favor escríbenos directamente al **WhatsApp** para resolver tu caso de inmediato. ¡Queremos hacerlo bien!",
        "¡Uy, lo siento! 😰 Eso no debería pasar. Cuéntame más o escríbenos al **WhatsApp** y lo solucionamos enseguida. Tu experiencia nos importa mucho.",
    ],
    joke: [
        "🤭 ¿Sabes qué le dijo un jugo a otro?\n— ¡Qué concentrado estás! 🥤",
        "😄 ¿Por qué el pan fue al doctor?\n— ¡Porque tenía migas! 🥖",
        "🤣 ¿Cuál es el colmo de un sánguche?\n— ¡Estar emparedado! 🥪",
    ],
    unknown: [
        "🤔 Hmm, no estoy seguro de entender. ¿Podrías reformular tu pregunta? También puedes escribir **\"menú\"** para ver nuestros productos o **\"ayuda\"** para ver qué puedo hacer.",
        "🧐 Esa es una buena pregunta pero no la tengo clara. Prueba preguntando por nuestros **productos**, **precios**, **delivery** o **horarios**.",
    ],
    frustration: [
        "😰 ¡Uy! Siento que te sientas así. No quiero que tengas una mala experiencia. ¿Quieres que te pase directamente con una **persona en WhatsApp**? Estaremos felices de ayudarte personalmente.",
        "😔 Perdona si no he sido de ayuda. Mi objetivo es calmar tus antojos, no complicarlos. Puedes escribir **\"menú\"** para empezar de cero o ir directo al **WhatsApp** para hablar con soporte.",
    ],
};

/** Pick a random response from the bank for the given intent */
function pickResponse(intentLabel: string): string | null {
    const templates = RESPONSE_BANK[intentLabel];
    if (!templates || templates.length === 0) return null;
    return templates[Math.floor(Math.random() * templates.length)];
}

// ========================
// 🔎 PRODUCT SEARCH
// ========================

/** Search for a specific product by fuzzy-matching name, category, or description */
export function searchProduct(query: string, products: Product[]): Product | null {
    const normQuery = normalize(query);
    const queryTokens = tokenize(query);
    const queryExpanded = expandTokens(queryTokens);

    let bestProduct: Product | null = null;
    let bestScore = 0;

    for (const product of products) {
        let score = 0;
        const normTitle = normalize(product.title);
        const normCategory = normalize(product.category);
        const normDesc = normalize(product.description || '');
        const titleTokens = normTitle.split(' ').filter(w => w.length > 1).map(stem);

        // Exact title substring
        if (normQuery.includes(normTitle) || normTitle.includes(normQuery)) {
            score = Math.max(score, 0.95);
        }

        // Category match
        if (normQuery.includes(normCategory)) {
            score = Math.max(score, 0.7);
        }

        // Token overlap with title
        for (const qt of queryExpanded) {
            for (const tt of titleTokens) {
                if (qt === tt) score = Math.max(score, 0.85);
                else if (fuzzyMatch(qt, tt, 1)) score = Math.max(score, 0.7);
            }
        }

        // Token in description
        for (const qt of queryExpanded) {
            if (normDesc.includes(qt) && qt.length > 3) {
                score = Math.max(score, 0.5);
            }
        }

        if (score > bestScore) {
            bestScore = score;
            bestProduct = product;
        }
    }

    return bestScore >= 0.5 ? bestProduct : null;
}

/** Format a product into a nice response */
function formatProductResponse(product: Product): string {
    const stockMsg = product.stock === 'low'
        ? '¡Quedan pocos! 🏃💨'
        : product.stock === 'available'
            ? 'Disponible ✅'
            : 'Agotado 😔';
    return `¡El **${product.title}** es buenísimo! 😋\n\n📝 ${product.description}\n💰 S/ ${product.price.toFixed(2)}\n📦 ${stockMsg}`;
}

// ========================
// 💬 FAQ SEARCH
// ========================

function searchFAQ(query: string): string | null {
    const queryTokens = tokenize(query);
    const queryExpanded = expandTokens(queryTokens);

    let bestMatch: typeof FAQ_DB[0] | null = null;
    let bestOverlap = 0;

    for (const faq of FAQ_DB) {
        const faqTokens = tokenize(faq.question);
        const overlap = faqTokens.filter(ft =>
            queryExpanded.some(qt => qt === ft || fuzzyMatch(qt, ft, 1))
        ).length;
        // Need at least 2 matching tokens, or 1 if the FAQ question is short
        const threshold = faqTokens.length <= 3 ? 1 : 2;
        if (overlap >= threshold && overlap > bestOverlap) {
            bestOverlap = overlap;
            bestMatch = faq;
        }
    }

    return bestMatch ? `💡 ${bestMatch.answer}` : null;
}

// ========================
// 🧵 CONTEXT TRACKING
// ========================

interface ConversationContext {
    lastProduct: Product | null;
    lastIntent: string;
    history: Array<{ role: 'user' | 'bot'; text: string }>;
}

const context: ConversationContext = {
    lastProduct: null,
    lastIntent: '',
    history: [],
};

/** Track a message in context */
export function trackMessage(text: string, role: 'user' | 'bot') {
    context.history.push({ role, text });
    // Keep only last 10 messages
    if (context.history.length > 10) {
        context.history = context.history.slice(-10);
    }
}

/** Check if query is a follow-up about the last product */
function isFollowUp(query: string): boolean {
    const followUpPatterns = [
        'cuanto cuesta', 'cuanto sale', 'precio', 'y ese', 'y eso',
        'me lo mandas', 'quiero ese', 'lo quiero', 'mandame',
        'tiene stock', 'hay disponible', 'el mas', 'la mas',
    ];
    const norm = normalize(query);
    return followUpPatterns.some(p => norm.includes(p)) && context.lastProduct !== null;
}

// ========================
// 🚀 MAIN PROCESSOR
// ========================

export interface NLPResult {
    response: string;
    action?: string;
    source: 'kb' | 'intent' | 'product' | 'faq' | 'context' | 'fallback';
}

/**
 * Process a query through PastelitoNLP. Returns the best response.
 * This is the single entry point that replaces semanticEngine + localBrain.
 */
export function processQuery(
    query: string,
    products: Product[],
    whatsappNumber: string = '51965968723',
    isAdmin: boolean = false
): NLPResult {

    // Track user message
    trackMessage(query, 'user');
    const normQuery = normalize(query);

    // --- Layer 0: Context follow-up ---
    if (isFollowUp(query) && context.lastProduct) {
        const product = context.lastProduct;
        const response = formatProductResponse(product);
        return { response, source: 'context' };
    }

    // --- Layer 1: KB Multi-Strategy Search ---
    const kbResult = multiSearch(query, isAdmin);
    if (kbResult && kbResult.score >= 0.5) {
        const item = kbResult.item;
        const resolvedResponse = resolveKBResponse(item);

        // Action-only entries
        if (item.action && !resolvedResponse) {
            return { response: '', action: item.action, source: 'kb' };
        }
        // Response + optional action
        if (resolvedResponse) {
            const finalResponse = Array.isArray(item.response)
                ? item.response[Math.floor(Math.random() * item.response.length)]
                : resolvedResponse;
            return { response: finalResponse, action: item.action, source: 'kb' };
        }
    }

    // --- Layer 2: Intent Classification ---
    const intentResult = predictIntent(query);
    if (intentResult.score > -20) {
        // Check if the golden dataset has a template
        const matchedIntent = INTENTS.find(i => i.label === intentResult.label);
        if (matchedIntent?.responseTemplate) {
            return { response: matchedIntent.responseTemplate, source: 'intent' };
        }
        // Check response bank
        const bankedResponse = pickResponse(intentResult.label);
        if (bankedResponse) {
            return { response: bankedResponse, source: 'intent' };
        }
    }

    // --- Layer 3: Product Search ---
    const product = searchProduct(query, products);
    if (product) {
        context.lastProduct = product;
        return { response: formatProductResponse(product), source: 'product' };
    }

    // --- Layer 4: FAQ Search ---
    const faqResponse = searchFAQ(query);
    if (faqResponse) {
        return { response: faqResponse, source: 'faq' };
    }

    // --- Layer 4.5: Loose Suggestion ---
    if (query.trim().length > 4) {
        let bestSuggestion: Product | null = null;
        let suggestionScore = 0;
        const qTokens = tokenize(query);
        for (const p of products) {
            const pTokens = tokenize(p.title);
            let matches = 0;
            for (const qt of qTokens) {
                for (const pt of pTokens) {
                    if (fuzzyMatch(qt, pt, 2)) matches++;
                }
            }
            if (matches > suggestionScore) {
                suggestionScore = matches;
                bestSuggestion = p;
            }
        }

        if (bestSuggestion && suggestionScore > 0) {
            const pureNumber = whatsappNumber.replace(/\D/g, '');
            return {
                response: `🤔 No encontré exactamente lo que buscas, ¿tal vez te refieres a nuestro **${bestSuggestion.title}**?\n\nSi necesitas algo más específico, escríbenos al [WhatsApp](https://wa.me/${pureNumber}).`,
                source: 'fallback'
            };
        }
    }

    // --- Layer 5: Smart Fallback ---
    // Try to give a helpful response even when nothing matches
    if (normQuery.length < 3) {
        return {
            response: "👋 ¡Hola! Escribe tu pregunta o consulta y te ayudo enseguida. Prueba con **\"menú\"**, **\"precios\"** o **\"delivery\"**.",
            source: 'fallback'
        };
    }

    // Final fallback with WhatsApp
    const pureNumber = whatsappNumber.replace(/\D/g, '');
    const fallbackResponse = pickResponse('unknown') ||
        `🤔 No encontré una respuesta exacta para eso. Para ayudarte mejor, escríbenos directamente al WhatsApp.\n\n👉 [Click para chatear](https://wa.me/${pureNumber}?text=Hola%20Antojín,%20tengo%20una%20consulta)`;

    return { response: fallbackResponse, source: 'fallback' };
}

/**
 * Check if PastelitoNLP is ready. Always returns true — no loading needed!
 */
export function isReady(): boolean {
    return true;
}
