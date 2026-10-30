const DEFAULT_API_URL = 'http://127.0.0.1:8000';

function allowedPathname(pathname: string): boolean {
  return pathname === '/health' || pathname.startsWith('/v1/');
}

function safeRequestedPath(path: string): boolean {
  // Queries are data; only the path can change the upstream routing boundary.
  // Inspect encoded forms too, rather than relying on a backend's decode rules.
  if (path.includes('#')) return false;
  let pathname = path.split('?', 1)[0];
  for (let depth = 0; depth < 5; depth += 1) {
    if (
      !allowedPathname(pathname) ||
      /[\\\u0000-\u001f\u007f]/.test(pathname) ||
      pathname.includes('//') ||
      pathname.split('/').some((segment) => segment === '.' || segment === '..')
    ) return false;
    try {
      const decoded = decodeURIComponent(pathname);
      if (decoded === pathname) return true;
      pathname = decoded;
    } catch {
      return false;
    }
  }
  return false;
}

async function proxy(request: Request) {
  const requestUrl = new URL(request.url);
  const paths = requestUrl.searchParams.getAll('path');
  const path = paths[0];
  if (paths.length !== 1 || !path || !safeRequestedPath(path)) {
    return Response.json(
      { detail: 'A valid Life OS API path is required.' },
      { status: 400 },
    );
  }

  try {
    const apiRoot = new URL(process.env.LIFE_OS_API_URL || DEFAULT_API_URL);
    if (
      !['http:', 'https:'].includes(apiRoot.protocol) ||
      apiRoot.username || apiRoot.password ||
      apiRoot.pathname !== '/' || apiRoot.search || apiRoot.hash
    ) throw new Error('Invalid upstream configuration');
    const upstreamUrl = new URL(path, apiRoot);
    // Recheck the actual normalized URL before attaching any credentials.
    if (upstreamUrl.origin !== apiRoot.origin || !allowedPathname(upstreamUrl.pathname)) {
      return Response.json({ detail: 'A valid Life OS API path is required.' }, { status: 400 });
    }
    requestUrl.searchParams.forEach((value, key) => {
      if (key !== 'path') upstreamUrl.searchParams.append(key, value);
    });
    const headers = new Headers();
    const contentType = request.headers.get('content-type');
    if (contentType) headers.set('content-type', contentType);
    const apiToken = process.env.LIFE_OS_API_TOKEN?.trim();
    const authorization = request.headers.get('authorization');
    if (apiToken) {
      headers.set('authorization', `Bearer ${apiToken}`);
    } else if (authorization) {
      headers.set('authorization', authorization);
    }

    const upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body:
        request.method === 'GET' || request.method === 'HEAD'
          ? undefined
          : await request.arrayBuffer(),
      cache: 'no-store',
      redirect: 'manual',
    });
    // An allowed endpoint must not redirect the credentialed proxy elsewhere.
    if (upstream.status >= 300 && upstream.status < 400) {
      return Response.json({ detail: 'Upstream redirects are not allowed.' }, { status: 502 });
    }
    return new Response(await upstream.arrayBuffer(), {
      status: upstream.status,
      headers: {
        'content-type': upstream.headers.get('content-type') || 'application/json',
      },
    });
  } catch {
    return Response.json(
      { detail: 'The private Life OS service is unavailable.' },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
