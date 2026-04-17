export interface Product {
    id: string;
    title: string;
    category: string;
    price: number;
    originalPrice?: number;
    description: string;
    image: string;
    imagePosition?: string;
    stock: 'available' | 'low' | 'out_of_stock';
    featured: boolean;
    savings?: number;
    preparationTime?: number;
    tags?: string[];
}

export const products: Product[] = [
    // EJEMPLO DE PRODUCTO
    {
        id: 'producto-demo-1',
        title: "Producto Demo 1",
        category: "categoria-1",
        price: 99.99,
        description: "Reemplace este archivo con los productos o servicios reales del nuevo negocio.",
        image: "/img/placeholder.jpg",
        imagePosition: "center center",
        stock: "available",
        featured: true,
        preparationTime: 0,
        tags: ["demo"]
    }
];
