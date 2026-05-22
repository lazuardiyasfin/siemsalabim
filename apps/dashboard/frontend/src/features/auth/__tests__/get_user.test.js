import { describe, it, expect, beforeEach } from 'vitest';
import { checkAuthStatus, setTokenStatus } from '../api/get_user';

describe('checkAuthStatus()', () => {
    beforeEach(() => {
        setTokenStatus(false);
    });

    it('Should return false if user isn\'t authenticated', async () => {
        const status = await checkAuthStatus();
        
        expect(status).toBe(false);
    });

    it('Should return true if user is authenticated', async () => {
        setTokenStatus(true);
        
        const status = await checkAuthStatus();
        
        expect(status).toBe(true);
    });
});