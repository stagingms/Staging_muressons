'use client';
import { useEffect } from 'react';

export default function FetchInterceptor() {
    useEffect(() => {
        if (typeof window !== 'undefined' && !window._fetchPatched) {
            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                let [resource, config] = args;
                if (typeof resource === 'string' && resource.includes('/api/admin/')) {
                    try {
                        const authData = JSON.parse(localStorage.getItem('facilitator_auth') || '{}');
                        const facId = authData.facilitator_id;
                        if (facId) {
                            config = config || {};
                            config.headers = {
                                ...config.headers,
                                'x-facilitator-id': facId
                            };
                            args[1] = config;
                        }
                    } catch (e) {
                        // ignore parsing error
                    }
                }
                return originalFetch(...args);
            };
            window._fetchPatched = true;
        }
    }, []);
    return null;
}
