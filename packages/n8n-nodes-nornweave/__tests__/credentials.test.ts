import { NornWeaveApi } from '../credentials/NornWeaveApi.credentials';

describe('NornWeaveApi Credentials', () => {
  let credentials: NornWeaveApi;

  beforeEach(() => {
    credentials = new NornWeaveApi();
  });

  describe('properties', () => {
    it('should have correct name', () => {
      expect(credentials.name).toBe('nornWeaveApi');
    });

    it('should have correct display name', () => {
      expect(credentials.displayName).toBe('NornWeave API');
    });

    it('should have baseUrl property', () => {
      const baseUrlProp = credentials.properties.find((p) => p.name === 'baseUrl');
      expect(baseUrlProp).toBeDefined();
      expect(baseUrlProp?.required).toBe(true);
      expect(baseUrlProp?.type).toBe('string');
      expect(baseUrlProp?.default).toBe('http://localhost:8000');
    });

    it('should have apiKey property as optional', () => {
      const apiKeyProp = credentials.properties.find((p) => p.name === 'apiKey');
      expect(apiKeyProp).toBeDefined();
      expect(apiKeyProp?.required).toBe(false);
      expect(apiKeyProp?.type).toBe('string');
      expect(apiKeyProp?.typeOptions?.password).toBe(true);
    });
  });

  describe('authentication', () => {
    it('should configure X-API-Key header', () => {
      expect(credentials.authenticate.type).toBe('generic');
      expect(credentials.authenticate.properties.headers).toHaveProperty('X-API-Key');
    });
  });

  describe('test request', () => {
    it('should test against /health endpoint', () => {
      expect(credentials.test.request.url).toBe('/health');
      expect(credentials.test.request.method).toBe('GET');
    });
  });
});
