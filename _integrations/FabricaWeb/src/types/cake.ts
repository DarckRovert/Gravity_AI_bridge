export interface CakeSelections {
    base: string;
    relleno: string;
    cobertura: string;
    tamano: string;
}

export interface CakeOption {
    label: string;
    price: number;
    icon: string;
    desc: string;
}

export interface BuilderOptions {
    base: CakeOption[];
    relleno: CakeOption[];
    cobertura: CakeOption[];
    tamano: CakeOption[];
}
