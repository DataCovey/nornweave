import type {
  IHookFunctions,
  IWebhookFunctions,
  INodeType,
  INodeTypeDescription,
  IWebhookResponseData,
} from 'n8n-workflow';
import { NodeConnectionTypes } from 'n8n-workflow';

export class NornWeaveTrigger implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'NornWeave Trigger',
    name: 'nornWeaveTrigger',
    icon: 'file:../../icons/nornweave.svg',
    group: ['trigger'],
    version: 1,
    subtitle: '={{$parameter["events"].join(", ")}}',
    description: 'Triggers when NornWeave receives an email or delivery event',
    defaults: {
      name: 'NornWeave Trigger',
    },
    inputs: [],
    outputs: [NodeConnectionTypes.Main],
    credentials: [
      {
        name: 'nornWeaveApi',
        required: false,
      },
    ],
    webhooks: [
      {
        name: 'default',
        httpMethod: 'POST',
        responseMode: 'onReceived',
        path: 'webhook',
      },
    ],
    properties: [
      {
        displayName: 'Events',
        name: 'events',
        type: 'multiOptions',
        required: true,
        default: ['email.received'],
        description: 'The events to listen for',
        options: [
          {
            name: 'Email Bounced',
            value: 'email.bounced',
            description: 'Triggered when an email bounces (permanent failure)',
          },
          {
            name: 'Email Clicked',
            value: 'email.clicked',
            description: 'Triggered when a recipient clicks a link in the email',
          },
          {
            name: 'Email Delivered',
            value: 'email.delivered',
            description: 'Triggered when an email is successfully delivered',
          },
          {
            name: 'Email Opened',
            value: 'email.opened',
            description: 'Triggered when a recipient opens the email',
          },
          {
            name: 'Email Received',
            value: 'email.received',
            description: 'Triggered when a new inbound email arrives',
          },
          {
            name: 'Email Sent',
            value: 'email.sent',
            description: 'Triggered when an outbound email is accepted for delivery',
          },
        ],
      },
      {
        displayName:
          'Note: You need to configure your email provider to send webhooks to the URL shown above. See the <a href="https://https://nornweave.datacovey.com/docs/integrations/n8n" target="_blank">documentation</a> for setup instructions.',
        name: 'notice',
        type: 'notice',
        default: '',
      },
    ],
		usableAsTool: true,
  };

  webhookMethods = {
    default: {
      async checkExists(this: IHookFunctions): Promise<boolean> {
        // For now, webhooks are configured manually in the email provider
        // In Phase 2, we could auto-register webhooks via NornWeave API
        return true;
      },
      async create(this: IHookFunctions): Promise<boolean> {
        // Manual webhook setup - no auto-registration yet
        return true;
      },
      async delete(this: IHookFunctions): Promise<boolean> {
        // Manual webhook setup - no auto-deregistration yet
        return true;
      },
    },
  };

  async webhook(this: IWebhookFunctions): Promise<IWebhookResponseData> {
    const req = this.getRequestObject();
    const body = this.getBodyData() as {
      type?: string;
      event_type?: string;
      [key: string]: unknown;
    };

    // Get configured events to filter
    const events = this.getNodeParameter('events', []) as string[];

    // Determine the event type from the payload
    // NornWeave sends event_type in the payload
    const eventType = body.type || body.event_type || 'email.received';

    // Check if this event should trigger the workflow
    if (events.length > 0 && !events.includes(eventType)) {
      // Event doesn't match filter - acknowledge but don't trigger
      return {
        webhookResponse: {
          status: 'acknowledged',
          message: `Event ${eventType} not in filter list`,
        },
      };
    }

    // Transform the payload to n8n execution data
    const returnData = {
      headers: req.headers,
      params: req.params,
      query: req.query,
      body: body,
      webhookUrl: this.getNodeWebhookUrl('default'),
      eventType: eventType,
    };

    return {
      workflowData: [[{ json: returnData }]],
    };
  }
}
