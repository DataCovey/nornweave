import type {
  IAuthenticateGeneric,
  ICredentialTestRequest,
  ICredentialType,
  INodeProperties,
} from 'n8n-workflow';

export class NornWeaveApi implements ICredentialType {
  name = 'nornWeaveApi';

  displayName = 'NornWeave API';

  documentationUrl = 'https://nornweave.io/docs/integrations/n8n';

  properties: INodeProperties[] = [
    {
      displayName: 'Base URL',
      name: 'baseUrl',
      type: 'string',
      default: 'http://localhost:8000',
      placeholder: 'https://your-nornweave-instance.com',
      description: 'The base URL of your NornWeave instance',
      required: true,
    },
    {
      displayName: 'API Key',
      name: 'apiKey',
      type: 'string',
      typeOptions: { password: true },
      default: '',
      description: 'Optional API key for authentication. Leave empty if your instance does not require authentication.',
      required: false,
    },
  ];

  authenticate: IAuthenticateGeneric = {
    type: 'generic',
    properties: {
      headers: {
        'X-API-Key': '={{$credentials?.apiKey}}',
      },
    },
  };

  test: ICredentialTestRequest = {
    request: {
      baseURL: '={{$credentials?.baseUrl}}',
      url: '/health',
      method: 'GET',
    },
  };
}
