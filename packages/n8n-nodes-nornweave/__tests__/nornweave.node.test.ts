import { NornWeave } from '../nodes/NornWeave/NornWeave.node';

describe('NornWeave Node', () => {
  let node: NornWeave;

  beforeEach(() => {
    node = new NornWeave();
  });

  describe('description', () => {
    it('should have correct name', () => {
      expect(node.description.name).toBe('nornWeave');
    });

    it('should have correct display name', () => {
      expect(node.description.displayName).toBe('NornWeave');
    });

    it('should be version 1', () => {
      expect(node.description.version).toBe(1);
    });

    it('should be usable as a tool', () => {
      expect(node.description.usableAsTool).toBe(true);
    });

    it('should require nornWeaveApi credentials', () => {
      const cred = node.description.credentials?.find((c) => c.name === 'nornWeaveApi');
      expect(cred).toBeDefined();
      expect(cred?.required).toBe(true);
    });
  });

  describe('resources', () => {
    it('should have 4 resources', () => {
      const resourceProp = node.description.properties.find((p) => p.name === 'resource');
      expect(resourceProp?.type).toBe('options');
      expect(resourceProp?.options).toHaveLength(4);
    });

    it('should have Inbox resource', () => {
      const resourceProp = node.description.properties.find((p) => p.name === 'resource');
      const inboxOption = (resourceProp?.options as Array<{ value: string }>)?.find(
        (o) => o.value === 'inbox',
      );
      expect(inboxOption).toBeDefined();
    });

    it('should have Message resource', () => {
      const resourceProp = node.description.properties.find((p) => p.name === 'resource');
      const messageOption = (resourceProp?.options as Array<{ value: string }>)?.find(
        (o) => o.value === 'message',
      );
      expect(messageOption).toBeDefined();
    });

    it('should have Thread resource', () => {
      const resourceProp = node.description.properties.find((p) => p.name === 'resource');
      const threadOption = (resourceProp?.options as Array<{ value: string }>)?.find(
        (o) => o.value === 'thread',
      );
      expect(threadOption).toBeDefined();
    });

    it('should have Search resource', () => {
      const resourceProp = node.description.properties.find((p) => p.name === 'resource');
      const searchOption = (resourceProp?.options as Array<{ value: string }>)?.find(
        (o) => o.value === 'search',
      );
      expect(searchOption).toBeDefined();
    });
  });

  describe('inbox operations', () => {
    it('should have Create, Delete, Get, Get Many operations', () => {
      const operationProp = node.description.properties.find(
        (p) =>
          p.name === 'operation' &&
          p.displayOptions?.show?.resource?.includes('inbox'),
      );
      const operations = (operationProp?.options as Array<{ value: string }>)?.map((o) => o.value);
      expect(operations).toContain('create');
      expect(operations).toContain('delete');
      expect(operations).toContain('get');
      expect(operations).toContain('getMany');
    });
  });

  describe('message operations', () => {
    it('should have Get, Get Many, Send operations', () => {
      const operationProp = node.description.properties.find(
        (p) =>
          p.name === 'operation' &&
          p.displayOptions?.show?.resource?.includes('message'),
      );
      const operations = (operationProp?.options as Array<{ value: string }>)?.map((o) => o.value);
      expect(operations).toContain('get');
      expect(operations).toContain('getMany');
      expect(operations).toContain('send');
    });
  });

  describe('thread operations', () => {
    it('should have Get, Get Many operations', () => {
      const operationProp = node.description.properties.find(
        (p) =>
          p.name === 'operation' &&
          p.displayOptions?.show?.resource?.includes('thread'),
      );
      const operations = (operationProp?.options as Array<{ value: string }>)?.map((o) => o.value);
      expect(operations).toContain('get');
      expect(operations).toContain('getMany');
    });
  });

  describe('search operations', () => {
    it('should have Query operation', () => {
      const operationProp = node.description.properties.find(
        (p) =>
          p.name === 'operation' &&
          p.displayOptions?.show?.resource?.includes('search'),
      );
      const operations = (operationProp?.options as Array<{ value: string }>)?.map((o) => o.value);
      expect(operations).toContain('query');
    });
  });
});
