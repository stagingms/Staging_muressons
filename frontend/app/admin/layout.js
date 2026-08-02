import '../globals.css';
import FetchInterceptor from '../components/FetchInterceptor';

export const metadata = {
    title: 'Facilitator Dashboard -Muressons Simulation',
    description:
        'Real-time cohort monitoring, manual overrides, and message injection for simulation facilitators.',
};

export default function AdminLayout({ children }) {
    return (
        <>
            <FetchInterceptor />
            {children}
        </>
    );
}
