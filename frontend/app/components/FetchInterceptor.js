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
                        const authData = JSON.parse(
                            localStorage.getItem('godmode_auth')
                            || localStorage.getItem('facilitator_auth')
                            || '{}'
                        );
                        const facId = authData.facilitator_id;
                        config = config || {};
                        // Always include credentials so the HttpOnly JWT cookie is sent
                        config.credentials = config.credentials || 'include';
                        if (facId) {
                            config.headers = {
                                ...config.headers,
                                'x-facilitator-id': facId
                            };
                        }
                        args[1] = config;
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
