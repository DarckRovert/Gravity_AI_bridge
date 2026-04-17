import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Panel Admin | Antojitos Express',
    description: 'Acceso restringido para administración.',
    robots: {
        index: false,
        follow: false,
    },
};

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
