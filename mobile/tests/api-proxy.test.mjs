import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

// Exercise the actual route handlers, including credential handling and fetch.
const source = readFileSync(new URL('../app/api/life-os/route.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
function setup({ env = { LIFE_OS_API_TOKEN: 'test-proxy-token' }, status = 200, fail = false } = {}) {
  const calls = [];
  const exports = {};
  vm.runInNewContext(compiled, { exports, URL, Headers, Request, Response, process: { env }, fetch: async (url, options) => {
    calls.push({ url: new URL(url), options });
    if (fail) throw new Error('synthetic network failure');
    return new Response(JSON.stringify({ ok: true }), { status, headers: { 'content-type': 'application/json', ...(status === 302 ? { location: 'https://example.com/' } : {}) } });
  } });
  return { handlers: exports, calls };
}
function request(path, method = 'GET', extra = []) {
  const url = new URL('http://localhost/api/life-os');
  if (path !== null) url.searchParams.set('path', path);
  for (const [key, value] of extra) url.searchParams.append(key, value);
  return new Request(url, { method, headers: { 'content-type': 'application/json', authorization: 'Bearer caller-token' }, ...(method !== 'GET' ? { body: '{"example":true}' } : {}) });
}
const rejected = [null, '', '/docs', '/health/extra', '/v10/goals', '/v1/../docs', '/v1/./goals', '/v1/a/../../docs', '/v1/%2e%2e/docs', '/v1/.%2e/docs', '/v1/%252e%252e/docs', '/v1/%2e%2e%2fdocs', '/v1/a%2f..%2f..%2fdocs', '/v1/..\\docs', '/v1/%5c..%5cdocs', '/v1/%255c..%255cdocs', '/v1//docs', '//example.com/v1/goals', 'https://example.com/v1/goals', '/v1/goals#fragment', '/v1/\n../docs', '/v1/%00goals', '/v1/%ZZ'];
for (const method of ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']) {
  for (const path of rejected) test(`${method} rejects ${JSON.stringify(path)} before fetch`, async () => {
    const { handlers, calls } = setup();
    const response = await handlers[method](request(path, method));
    assert.equal(response.status, 400);
    assert.equal(calls.length, 0);
  });
}
test('rejects duplicate path parameters', async () => {
  const { handlers, calls } = setup();
  assert.equal((await handlers.GET(request('/v1/goals', 'GET', [['path', '/health']]))).status, 400);
  assert.equal(calls.length, 0);
});
for (const path of ['/v1/goals?tenant_id=me', '/health', '/v1/knowledge-records?query=../notes', '/v1/goals/example%20id']) test(`allows ${path}`, async () => {
  const { handlers, calls } = setup();
  const response = await handlers.GET(request(path, 'GET', [['limit', '10']]));
  assert.equal(response.status, 200);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url.origin, 'http://127.0.0.1:8000');
  assert.equal(calls[0].url.searchParams.get('limit'), '10');
  assert.equal(calls[0].options.headers.get('authorization'), 'Bearer test-proxy-token');
  assert.equal(calls[0].options.redirect, 'manual');
});
test('preserves write payload and caller authorization without configured token', async () => {
  const { handlers, calls } = setup({ env: {} });
  assert.equal((await handlers.POST(request('/v1/goals', 'POST'))).status, 200);
  assert.equal(new TextDecoder().decode(calls[0].options.body), '{"example":true}');
  assert.equal(calls[0].options.headers.get('authorization'), 'Bearer caller-token');
});
test('never follows or exposes upstream redirects', async () => {
  const { handlers, calls } = setup({ status: 302 });
  const response = await handlers.GET(request('/v1/goals'));
  assert.equal(response.status, 502);
  assert.equal(response.headers.get('location'), null);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.redirect, 'manual');
});
test('handles network failure without leaking a token', async () => {
  const { handlers } = setup({ fail: true });
  const response = await handlers.GET(request('/v1/goals'));
  assert.equal(response.status, 503);
  assert.ok(!(await response.text()).includes('test-proxy-token'));
});
for (const root of ['file:///etc/passwd', 'http://user:password@localhost', 'http://localhost/other', 'http://localhost/?token=value']) test(`rejects invalid upstream configuration ${root}`, async () => {
  const { handlers, calls } = setup({ env: { LIFE_OS_API_URL: root, LIFE_OS_API_TOKEN: 'test-proxy-token' } });
  assert.equal((await handlers.GET(request('/v1/goals'))).status, 503);
  assert.equal(calls.length, 0);
});
