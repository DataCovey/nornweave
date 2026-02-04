import { NornWeaveTrigger } from '../nodes/NornWeaveTrigger/NornWeaveTrigger.node';

describe('NornWeaveTrigger Node', () => {
  let node: NornWeaveTrigger;

  beforeEach(() => {
    node = new NornWeaveTrigger();
  });

  describe('description', () => {
    it('should have correct name', () => {
      expect(node.description.name).toBe('nornWeaveTrigger');
    });

    it('should have correct display name', () => {
      expect(node.description.displayName).toBe('NornWeave Trigger');
    });

    it('should be version 1', () => {
      expect(node.description.version).toBe(1);
    });

    it('should be in trigger group', () => {
      expect(node.description.group).toContain('trigger');
    });

    it('should have no inputs (trigger node)', () => {
      expect(node.description.inputs).toHaveLength(0);
    });
  });

  describe('events parameter', () => {
    it('should have events multiOptions parameter', () => {
      const eventsProp = node.description.properties.find((p) => p.name === 'events');
      expect(eventsProp).toBeDefined();
      expect(eventsProp?.type).toBe('multiOptions');
      expect(eventsProp?.required).toBe(true);
    });

    it('should default to email.received', () => {
      const eventsProp = node.description.properties.find((p) => p.name === 'events');
      expect(eventsProp?.default).toContain('email.received');
    });

    it('should have all expected event types', () => {
      const eventsProp = node.description.properties.find((p) => p.name === 'events');
      const eventValues = (eventsProp?.options as Array<{ value: string }>)?.map((o) => o.value);

      expect(eventValues).toContain('email.received');
      expect(eventValues).toContain('email.sent');
      expect(eventValues).toContain('email.delivered');
      expect(eventValues).toContain('email.bounced');
      expect(eventValues).toContain('email.opened');
      expect(eventValues).toContain('email.clicked');
    });
  });

  describe('webhook configuration', () => {
    it('should have webhook defined', () => {
      expect(node.description.webhooks).toBeDefined();
      expect(node.description.webhooks).toHaveLength(1);
    });

    it('should use POST method', () => {
      expect(node.description.webhooks?.[0].httpMethod).toBe('POST');
    });

    it('should respond on received', () => {
      expect(node.description.webhooks?.[0].responseMode).toBe('onReceived');
    });
  });

  describe('webhook methods', () => {
    it('should have checkExists method', () => {
      expect(node.webhookMethods.default.checkExists).toBeDefined();
    });

    it('should have create method', () => {
      expect(node.webhookMethods.default.create).toBeDefined();
    });

    it('should have delete method', () => {
      expect(node.webhookMethods.default.delete).toBeDefined();
    });
  });
});
