import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Nuestra Carta | Dulces Momentos',
    description: 'Explora nuestros deliciosos postres, tortas y bocaditos.',
};

export default function MenuLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
