import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Rastrea tu Pedido | Dulces Momentos',
    description: 'Sigue el estado de tu pedido en tiempo real. Desde el horno hasta tu puerta.',
};

export default function TrackerLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
