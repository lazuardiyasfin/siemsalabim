import { describe, test, expect } from 'vitest';
import { getColor } from '../utils/map-helpers.js';

describe('getColor', () => {
    test.each([
        { value: 150, expected: '#800026' },
        { value: 110, expected: '#800026' },
        { value: 109, expected: '#BD0026' },
        { value: 85,  expected: '#BD0026' },
        { value: 74,  expected: '#BD0026' },
        { value: 73,  expected: '#E31A1C' },
        { value: 50,  expected: '#E31A1C' },
        { value: 38,  expected: '#E31A1C' },
        { value: 37,  expected: '#FC4E2A' },
        { value: 15,  expected: '#FC4E2A' },
        { value: 1,   expected: '#FC4E2A' },
        { value: 0,   expected: '#FD8D3C' },
        { value: -5,  expected: '#FD8D3C' },
    ])('should return $expected when value is $value', ({ value, expected }) => {
        expect(getColor(value)).toBe(expected);
    });

    test('should handle invalid inputs gracefully', () => {
        expect(getColor(undefined)).toBe('#FD8D3C');
        expect(getColor(null)).toBe('#FD8D3C');
        expect(getColor('string')).toBe('#FD8D3C');
    });
});