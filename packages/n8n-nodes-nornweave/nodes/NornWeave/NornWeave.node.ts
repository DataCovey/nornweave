import {
  NodeConnectionTypes,
  type INodeType,
  type INodeTypeDescription,
} from 'n8n-workflow';

export class NornWeave implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'NornWeave',
    name: 'nornWeave',
    icon: 'file:../../icons/nornweave.svg',
    group: ['transform'],
    version: 1,
    subtitle: '={{$parameter["operation"] + ": " + $parameter["resource"]}}',
    description: 'Interact with NornWeave - Inbox-as-a-Service for AI Agents',
    defaults: {
      name: 'NornWeave',
    },
    usableAsTool: true,
    inputs: [NodeConnectionTypes.Main],
    outputs: [NodeConnectionTypes.Main],
    credentials: [
      {
        name: 'nornWeaveApi',
        required: true,
      },
    ],
    requestDefaults: {
      baseURL: '={{$credentials?.baseUrl}}',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    },
    properties: [
      // Resource selector
      {
        displayName: 'Resource',
        name: 'resource',
        type: 'options',
        noDataExpression: true,
        options: [
          {
            name: 'Inbox',
            value: 'inbox',
            description: 'Manage email inboxes',
          },
          {
            name: 'Message',
            value: 'message',
            description: 'Send and retrieve email messages',
          },
          {
            name: 'Thread',
            value: 'thread',
            description: 'Access email conversation threads',
          },
          {
            name: 'Search',
            value: 'search',
            description: 'Search messages by content',
          },
        ],
        default: 'inbox',
      },

      // ==================== INBOX OPERATIONS ====================
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['inbox'],
          },
        },
        options: [
          {
            name: 'Create',
            value: 'create',
            description: 'Create a new inbox',
            action: 'Create an inbox',
            routing: {
              request: {
                method: 'POST',
                url: '/v1/inboxes',
              },
            },
          },
          {
            name: 'Delete',
            value: 'delete',
            description: 'Delete an inbox',
            action: 'Delete an inbox',
            routing: {
              request: {
                method: 'DELETE',
                url: '=/v1/inboxes/{{$parameter["inboxId"]}}',
              },
              output: {
                postReceive: [
                  {
                    type: 'set',
                    properties: {
                      value: '={{ { "success": true } }}',
                    },
                  },
                ],
              },
            },
          },
          {
            name: 'Get',
            value: 'get',
            description: 'Get an inbox by ID',
            action: 'Get an inbox',
            routing: {
              request: {
                method: 'GET',
                url: '=/v1/inboxes/{{$parameter["inboxId"]}}',
              },
            },
          },
          {
            name: 'Get Many',
            value: 'getMany',
            description: 'Get many inboxes',
            action: 'Get many inboxes',
            routing: {
              request: {
                method: 'GET',
                url: '/v1/inboxes',
              },
              output: {
                postReceive: [
                  {
                    type: 'rootProperty',
                    properties: {
                      property: 'items',
                    },
                  },
                ],
              },
            },
          },
        ],
        default: 'getMany',
      },

      // Inbox Create parameters
      {
        displayName: 'Name',
        name: 'name',
        type: 'string',
        required: true,
        default: '',
        placeholder: 'Support Inbox',
        description: 'A friendly name for the inbox',
        displayOptions: {
          show: {
            resource: ['inbox'],
            operation: ['create'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'name',
          },
        },
      },
      {
        displayName: 'Email Username',
        name: 'emailUsername',
        type: 'string',
        required: true,
        default: '',
        placeholder: 'support',
        description: 'The username part of the email address (e.g., "support" for support@yourdomain.com)',
        displayOptions: {
          show: {
            resource: ['inbox'],
            operation: ['create'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'email_username',
          },
        },
      },

      // Inbox ID parameter (shared across get, delete)
      {
        displayName: 'Inbox ID',
        name: 'inboxId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the inbox',
        displayOptions: {
          show: {
            resource: ['inbox'],
            operation: ['get', 'delete'],
          },
        },
      },

      // Inbox Get Many pagination
      {
        displayName: 'Return All',
        name: 'returnAll',
        type: 'boolean',
        default: false,
        description: 'Whether to return all results or only up to a given limit',
        displayOptions: {
          show: {
            resource: ['inbox'],
            operation: ['getMany'],
          },
        },
      },
      {
        displayName: 'Limit',
        name: 'limit',
        type: 'number',
        typeOptions: {
          minValue: 1,
          maxValue: 100,
        },
        default: 50,
        description: 'Max number of results to return',
        displayOptions: {
          show: {
            resource: ['inbox'],
            operation: ['getMany'],
            returnAll: [false],
          },
        },
        routing: {
          send: {
            type: 'query',
            property: 'limit',
          },
        },
      },

      // ==================== MESSAGE OPERATIONS ====================
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['message'],
          },
        },
        options: [
          {
            name: 'Get',
            value: 'get',
            description: 'Get a message by ID',
            action: 'Get a message',
            routing: {
              request: {
                method: 'GET',
                url: '=/v1/messages/{{$parameter["messageId"]}}',
              },
            },
          },
          {
            name: 'Get Many',
            value: 'getMany',
            description: 'Get many messages from an inbox',
            action: 'Get many messages',
            routing: {
              request: {
                method: 'GET',
                url: '/v1/messages',
              },
              output: {
                postReceive: [
                  {
                    type: 'rootProperty',
                    properties: {
                      property: 'items',
                    },
                  },
                ],
              },
            },
          },
          {
            name: 'Send',
            value: 'send',
            description: 'Send an outbound email message',
            action: 'Send a message',
            routing: {
              request: {
                method: 'POST',
                url: '/v1/messages',
              },
            },
          },
        ],
        default: 'getMany',
      },

      // Message Get parameter
      {
        displayName: 'Message ID',
        name: 'messageId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the message',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['get'],
          },
        },
      },

      // Message Get Many parameters
      {
        displayName: 'Inbox ID',
        name: 'inboxId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the inbox to get messages from',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['getMany'],
          },
        },
        routing: {
          send: {
            type: 'query',
            property: 'inbox_id',
          },
        },
      },
      {
        displayName: 'Return All',
        name: 'returnAll',
        type: 'boolean',
        default: false,
        description: 'Whether to return all results or only up to a given limit',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['getMany'],
          },
        },
      },
      {
        displayName: 'Limit',
        name: 'limit',
        type: 'number',
        typeOptions: {
          minValue: 1,
          maxValue: 100,
        },
        default: 50,
        description: 'Max number of results to return',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['getMany'],
            returnAll: [false],
          },
        },
        routing: {
          send: {
            type: 'query',
            property: 'limit',
          },
        },
      },

      // Message Send parameters
      {
        displayName: 'Inbox ID',
        name: 'inboxId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the inbox to send from',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['send'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'inbox_id',
          },
        },
      },
      {
        displayName: 'To',
        name: 'to',
        type: 'string',
        required: true,
        default: '',
        placeholder: 'recipient@example.com',
        description: 'Recipient email addresses (comma-separated for multiple)',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['send'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'to',
            value: '={{ $value.split(",").map(e => e.trim()) }}',
          },
        },
      },
      {
        displayName: 'Subject',
        name: 'subject',
        type: 'string',
        required: true,
        default: '',
        placeholder: 'Hello from NornWeave',
        description: 'The email subject line',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['send'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'subject',
          },
        },
      },
      {
        displayName: 'Body',
        name: 'body',
        type: 'string',
        typeOptions: {
          rows: 5,
        },
        required: true,
        default: '',
        placeholder: 'Your message content in **Markdown** format',
        description: 'The email body content (Markdown supported)',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['send'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'body',
          },
        },
      },
      {
        displayName: 'Reply to Thread ID',
        name: 'replyToThreadId',
        type: 'string',
        default: '',
        description: 'Optional thread ID to reply to (creates a new thread if empty)',
        displayOptions: {
          show: {
            resource: ['message'],
            operation: ['send'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'reply_to_thread_id',
            value: '={{ $value || undefined }}',
          },
        },
      },

      // ==================== THREAD OPERATIONS ====================
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['thread'],
          },
        },
        options: [
          {
            name: 'Get',
            value: 'get',
            description: 'Get a thread with all messages',
            action: 'Get a thread',
            routing: {
              request: {
                method: 'GET',
                url: '=/v1/threads/{{$parameter["threadId"]}}',
              },
            },
          },
          {
            name: 'Get Many',
            value: 'getMany',
            description: 'Get many threads from an inbox',
            action: 'Get many threads',
            routing: {
              request: {
                method: 'GET',
                url: '/v1/threads',
              },
              output: {
                postReceive: [
                  {
                    type: 'rootProperty',
                    properties: {
                      property: 'items',
                    },
                  },
                ],
              },
            },
          },
        ],
        default: 'getMany',
      },

      // Thread Get parameter
      {
        displayName: 'Thread ID',
        name: 'threadId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the thread',
        displayOptions: {
          show: {
            resource: ['thread'],
            operation: ['get'],
          },
        },
      },

      // Thread Get Many parameters
      {
        displayName: 'Inbox ID',
        name: 'inboxId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the inbox to get threads from',
        displayOptions: {
          show: {
            resource: ['thread'],
            operation: ['getMany'],
          },
        },
        routing: {
          send: {
            type: 'query',
            property: 'inbox_id',
          },
        },
      },
      {
        displayName: 'Return All',
        name: 'returnAll',
        type: 'boolean',
        default: false,
        description: 'Whether to return all results or only up to a given limit',
        displayOptions: {
          show: {
            resource: ['thread'],
            operation: ['getMany'],
          },
        },
      },
      {
        displayName: 'Limit',
        name: 'limit',
        type: 'number',
        typeOptions: {
          minValue: 1,
          maxValue: 100,
        },
        default: 50,
        description: 'Max number of results to return',
        displayOptions: {
          show: {
            resource: ['thread'],
            operation: ['getMany'],
            returnAll: [false],
          },
        },
        routing: {
          send: {
            type: 'query',
            property: 'limit',
          },
        },
      },

      // ==================== SEARCH OPERATIONS ====================
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['search'],
          },
        },
        options: [
          {
            name: 'Query',
            value: 'query',
            description: 'Search messages by content',
            action: 'Search messages',
            routing: {
              request: {
                method: 'POST',
                url: '/v1/search',
              },
              output: {
                postReceive: [
                  {
                    type: 'rootProperty',
                    properties: {
                      property: 'items',
                    },
                  },
                ],
              },
            },
          },
        ],
        default: 'query',
      },

      // Search parameters
      {
        displayName: 'Query',
        name: 'query',
        type: 'string',
        required: true,
        default: '',
        placeholder: 'invoice from October',
        description: 'The search query to find messages',
        displayOptions: {
          show: {
            resource: ['search'],
            operation: ['query'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'query',
          },
        },
      },
      {
        displayName: 'Inbox ID',
        name: 'inboxId',
        type: 'string',
        required: true,
        default: '',
        description: 'The ID of the inbox to search in',
        displayOptions: {
          show: {
            resource: ['search'],
            operation: ['query'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'inbox_id',
          },
        },
      },
      {
        displayName: 'Limit',
        name: 'limit',
        type: 'number',
        typeOptions: {
          minValue: 1,
          maxValue: 100,
        },
        default: 50,
        description: 'Max number of results to return',
        displayOptions: {
          show: {
            resource: ['search'],
            operation: ['query'],
          },
        },
        routing: {
          send: {
            type: 'body',
            property: 'limit',
          },
        },
      },
    ],
  };
}
