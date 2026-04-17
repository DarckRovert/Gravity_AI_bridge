import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Crea tu Torta | Dulces Momentos',
    description: 'Diseña la torta perfecta para tu ocasión especial. Elige sabor, relleno y decoración.',
};

export default function BuilderLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
