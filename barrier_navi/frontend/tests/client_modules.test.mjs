import assert from 'node:assert/strict';
import test from 'node:test';

import { apiUrl, getApi, patchApi, postApi } from '../dist/api.js';
import {
  clearClientAuthState,
  getClientAuthState,
  isClientAuthenticated,
  setAuthenticatedUser,
  startGuestSession,
} from '../dist/auth.js';

class MemoryStorage {
  #values = new Map();

  getItem(key) {
    return this.#values.has(key) ? this.#values.get(key) : null;
  }

  setItem(key, value) {
    this.#values.set(key, String(value));
  }

  removeItem(key) {
    this.#values.delete(key);
  }
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

test('apiUrl normalizes API paths', () => {
  assert.equal(apiUrl('/auth/profile'), '/api/auth/profile');
  assert.equal(apiUrl('stations/search'), '/api/stations/search');
});

test('postApi sends same-origin JSON and preserves successful API payloads', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => {
    globalThis.fetch = originalFetch;
  });

  let requestUrl;
  let requestInit;
  globalThis.fetch = async (url, init) => {
    requestUrl = url;
    requestInit = init;
    return jsonResponse({ success: true, data: { id: 7 } }, 201);
  };

  const result = await postApi('/auth/login', { username: 'user', password: 'secret' });

  assert.equal(requestUrl, '/api/auth/login');
  assert.equal(requestInit.method, 'POST');
  assert.equal(requestInit.credentials, 'same-origin');
  assert.equal(requestInit.headers.get('Content-Type'), 'application/json');
  assert.deepEqual(JSON.parse(requestInit.body), { username: 'user', password: 'secret' });
  assert.equal(result.status, 201);
  assert.deepEqual(result.body, { success: true, data: { id: 7 } });
});

test('common API client preserves API failures and normalizes malformed and network responses', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => {
    globalThis.fetch = originalFetch;
  });

  globalThis.fetch = async () => jsonResponse({ success: false, error: '認証が必要です' }, 401);
  const unauthorized = await getApi('/auth/profile');
  assert.equal(unauthorized.status, 401);
  assert.equal(unauthorized.body.error, '認証が必要です');

  globalThis.fetch = async () => new Response('<html>error</html>', { status: 502 });
  const malformed = await patchApi('/auth/profile', { username: 'user' });
  assert.equal(malformed.status, 502);
  assert.equal(malformed.body.success, false);
  assert.match(malformed.body.error, /JSON/);

  globalThis.fetch = async () => {
    throw new Error('offline');
  };
  const networkFailure = await getApi('/stations/count');
  assert.equal(networkFailure.status, 0);
  assert.equal(networkFailure.body.success, false);
  assert.match(networkFailure.body.error, /通信に失敗/);
});

test('client authentication helpers only manage UI storage state', (t) => {
  const originalStorage = globalThis.localStorage;
  const storage = new MemoryStorage();
  globalThis.localStorage = storage;
  t.after(() => {
    globalThis.localStorage = originalStorage;
  });

  setAuthenticatedUser({ id: 8, username: '利用者', email: 'user@example.test' }, 'fallback');
  assert.deepEqual(getClientAuthState(), {
    isLoggedIn: true,
    isGuest: false,
    username: '利用者',
    userId: 8,
    userEmail: 'user@example.test',
  });
  assert.equal(isClientAuthenticated(), true);

  startGuestSession();
  assert.deepEqual(getClientAuthState(), {
    isLoggedIn: false,
    isGuest: true,
    username: 'ゲスト',
    userId: null,
    userEmail: null,
  });

  storage.setItem('rememberMe', 'true');
  clearClientAuthState();
  assert.deepEqual(getClientAuthState(), {
    isLoggedIn: false,
    isGuest: false,
    username: null,
    userId: null,
    userEmail: null,
  });
  assert.equal(storage.getItem('rememberMe'), null);
});
