/**
 * The error normaliser. Every case here is a shape that produced the literal
 * text "[object Object]" in a form the operator had to act on.
 */
import { toErrorText, describeHttpFailure } from '../app/lib/apiError';

const FALLBACK = 'Something went wrong. See the browser console for details.';

describe('toErrorText', () => {
    it('passes a plain string through', () => {
        expect(toErrorText('Facilitator quota reached.')).toBe('Facilitator quota reached.');
    });

    it('renders a FastAPI 422 array as field: message, dropping the body prefix', () => {
        expect(toErrorText([
            { loc: ['body', 'region_id'], msg: 'Input should be a valid string', type: 'string_type' },
            { loc: ['body', 'cohort_name'], msg: 'String should have at least 1 character' },
        ])).toBe('region_id: Input should be a valid string; cohort_name: String should have at least 1 character');
    });

    it('renders a structured dict detail', () => {
        expect(toErrorText({ code: 'quota', message: 'Cohort limit reached.' })).toBe('Cohort limit reached.');
    });

    it('unwraps a nested detail', () => {
        expect(toErrorText({ detail: { message: 'Inner reason.' } })).toBe('Inner reason.');
        expect(toErrorText({ detail: 'Plain inner.' })).toBe('Plain inner.');
    });

    it('uses an Error message', () => {
        expect(toErrorText(new Error('Network request failed'))).toBe('Network request failed');
    });

    it('refuses to surface an already-poisoned Error', () => {
        // new Error({}) — the very coercion this module exists to prevent.
        expect(toErrorText(new Error({}))).toBe(FALLBACK);
    });

    it('never returns the literal [object Object] for any shape', () => {
        const shapes = [
            {}, [], [{}], { detail: {} }, { detail: [] }, new Error(''),
            { a: 1 }, [{ loc: ['body'], msg: '' }], 0, false, '   ',
        ];
        for (const s of shapes) {
            const out = toErrorText(s);
            expect(out).not.toBe('[object Object]');
            expect(typeof out === 'string' && out.length > 0).toBe(true);
        }
    });

    it('returns null for null/undefined so a caller can clear the banner', () => {
        expect(toErrorText(null)).toBeNull();
        expect(toErrorText(undefined)).toBeNull();
    });

    it('survives a circular object rather than throwing', () => {
        const a = { name: 'x' }; a.self = a;
        expect(() => toErrorText(a)).not.toThrow();
        expect(toErrorText(a)).toBe(FALLBACK);
    });
});

describe('describeHttpFailure', () => {
    it('names what failed, the status, and what the server said', () => {
        expect(describeHttpFailure('Pedagogical Settings', 500, { detail: 'boom' }))
            .toBe('Pedagogical Settings failed (500): boom');
    });

    it('names the field on a 422', () => {
        expect(describeHttpFailure('Create cohort', 422, {
            detail: [{ loc: ['body', 'region_id'], msg: 'Input should be a valid string' }],
        })).toBe('Create cohort failed (422): region_id: Input should be a valid string');
    });

    it('still identifies the call when the body is empty or unparseable', () => {
        expect(describeHttpFailure('Create cohort', 502, {})).toBe('Create cohort failed (HTTP 502).');
        expect(describeHttpFailure('Create cohort', 502, null)).toBe('Create cohort failed (HTTP 502).');
    });
});
