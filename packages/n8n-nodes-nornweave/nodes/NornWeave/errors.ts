import { NodeApiError, type INode } from 'n8n-workflow';

interface ApiErrorResponse {
  detail?: string | { msg: string; loc?: string[] }[];
  message?: string;
  error?: string;
}

/**
 * Transform NornWeave API errors into user-friendly n8n error messages
 */
export function handleApiError(
  node: INode,
  error: Error & { response?: { status?: number; data?: ApiErrorResponse } },
  resource?: string,
  resourceId?: string,
): never {
  const status = error.response?.status;
  const data = error.response?.data;

  // HTTP 404 - Not Found
  if (status === 404) {
    const resourceName = resource || 'Resource';
    const idInfo = resourceId ? ` with ID "${resourceId}"` : '';
    throw new NodeApiError(node, error, {
      message: `${resourceName} not found`,
      description: `The ${resourceName.toLowerCase()}${idInfo} was not found. Please check that the ID is correct and the resource exists.`,
      httpCode: '404',
    });
  }

  // HTTP 409 - Conflict (e.g., duplicate inbox)
  if (status === 409) {
    throw new NodeApiError(node, error, {
      message: 'Resource conflict',
      description:
        data?.detail?.toString() ||
        'A resource with this identifier already exists. Please use a different value.',
      httpCode: '409',
    });
  }

  // HTTP 422 - Validation Error
  if (status === 422) {
    let validationMessage = 'Validation failed';

    if (Array.isArray(data?.detail)) {
      const fields = data.detail
        .map((d) => {
          const loc = d.loc?.join('.') || 'unknown';
          return `${loc}: ${d.msg}`;
        })
        .join('; ');
      validationMessage = `Validation failed: ${fields}`;
    } else if (typeof data?.detail === 'string') {
      validationMessage = data.detail;
    }

    throw new NodeApiError(node, error, {
      message: 'Validation error',
      description: validationMessage,
      httpCode: '422',
    });
  }

  // HTTP 401/403 - Authentication errors
  if (status === 401 || status === 403) {
    throw new NodeApiError(node, error, {
      message: 'Authentication failed',
      description:
        'Unable to authenticate with NornWeave. Please check your API key in the credentials.',
      httpCode: status.toString(),
    });
  }

  // HTTP 500+ - Server errors
  if (status && status >= 500) {
    throw new NodeApiError(node, error, {
      message: 'NornWeave server error',
      description:
        'The NornWeave server encountered an error. Please try again later or check the server logs.',
      httpCode: status.toString(),
    });
  }

  // Network errors (no response)
  if (!error.response) {
    throw new NodeApiError(node, error, {
      message: 'Connection failed',
      description:
        'Unable to connect to NornWeave. Please check that:\n' +
        '1. The Base URL in your credentials is correct\n' +
        '2. The NornWeave server is running and accessible\n' +
        '3. There are no network/firewall issues',
    });
  }

  // Default error handling
  throw new NodeApiError(node, error, {
    message: data?.message || data?.error || 'Request failed',
    description: data?.detail?.toString() || error.message,
    httpCode: status?.toString(),
  });
}
