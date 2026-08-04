/**
 * "Login succeeds, then you are immediately logged out" must name its cause (B4).
 *
 * A privacy extension, Safari ITP or a locked-down lab browser accepts the
 * login POST but never keeps what the session depends on. Today the facilitator
 * is bounced back to the gateway reading "Your session expired" — seconds after
 * a successful sign-in — and goes looking for a password fault that isn't there.
 *
 * The register's suggested fix was a blanket "enable cookies" banner on the
 * login page. That would be wrong on the PLAYER screen: a player session is
 * localStorage + an X-Player-Id header, with no cookie anywhere. So the two
 * screens probe the thing each actually depends on, and these tests pin that
 * distinction — a cookie warning on the player screen is a regression.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const read = (...p) => fs.readFileSync(path.join(APP, ...p), 'utf8');

const {
  cookiesWritable,
  localStorageWritable,
  COOKIE_BLOCKED_MESSAGE,
  STORAGE_BLOCKED_MESSAGE,
} = require('../app/utils/storageHealth');

describe('cookie probe', () => {
  const realCookie = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie');
  afterEach(() => {
    if (realCookie) Object.defineProperty(document, 'cookie', realCookie);
  });

  const stubCookie = ({ store = true, throws = false } = {}) => {
    let jar = '';
    Object.defineProperty(document, 'cookie', {
      configurable: true,
      get: () => jar,
      set: (v) => {
        if (throws) throw new Error('blocked by policy');
        if (store) jar = String(v).split(';')[0];
      },
    });
  };

  test('a browser that stores cookies passes', () => {
    stubCookie({ store: true });
    expect(cookiesWritable()).toBe(true);
  });

  test('a browser that silently drops cookies fails', () => {
    // The realistic case: the setter is a no-op, no exception thrown.
    stubCookie({ store: false });
    expect(cookiesWritable()).toBe(false);
  });

  test('a browser that throws on write fails rather than crashing the form', () => {
    stubCookie({ throws: true });
    expect(cookiesWritable()).toBe(false);
  });

  test('the probe cleans up after itself', () => {
    stubCookie({ store: true });
    cookiesWritable();
    expect(document.cookie).not.toContain('muressons_probe=1');
  });
});

describe('localStorage probe', () => {
  const real = window.localStorage;
  const install = (impl) => Object.defineProperty(window, 'localStorage', {
    configurable: true, value: impl,
  });
  afterEach(() => install(real));

  test('a working store passes', () => {
    expect(localStorageWritable()).toBe(true);
  });

  test('a store that throws on write fails', () => {
    // Safari private mode historically threw QuotaExceededError here.
    install({ setItem() { throw new Error('QuotaExceededError'); },
              getItem() { return null; }, removeItem() {} });
    expect(localStorageWritable()).toBe(false);
  });

  test('a store that silently discards fails', () => {
    install({ setItem() {}, getItem() { return null; }, removeItem() {} });
    expect(localStorageWritable()).toBe(false);
  });

  test('the probe key is removed again', () => {
    localStorageWritable();
    expect(window.localStorage.getItem('__muressons_probe__')).toBeNull();
  });
});

describe('each screen warns about the thing IT depends on', () => {
  const adminLogin = read('components', 'AdminLogin.js');
  const joinModal = read('components', 'JoinCohortModal.js');

  test('the facilitator form probes cookies — its session is an HttpOnly cookie', () => {
    expect(adminLogin).toMatch(/cookiesWritable/);
    expect(adminLogin).toMatch(/COOKIE_BLOCKED_MESSAGE/);
    expect(adminLogin).toMatch(/credentials: 'include'/);   // why it needs one
  });

  test('the player form probes localStorage — it has no cookie at all', () => {
    expect(joinModal).toMatch(/localStorageWritable/);
    expect(joinModal).toMatch(/STORAGE_BLOCKED_MESSAGE/);
  });

  test('the player form does NOT show a cookie warning', () => {
    // The wrong diagnosis is worse than none: it would send a student to
    // change a setting that has no bearing on their session.
    expect(joinModal).not.toMatch(/cookiesWritable|COOKIE_BLOCKED_MESSAGE/);
  });

  test('neither warning is rendered unconditionally', () => {
    // A permanent banner on a screen that works for 99% of people is noise,
    // and noise gets ignored exactly when it finally matters.
    expect(adminLogin).toMatch(/\{cookiesBlocked && \(/);
    expect(joinModal).toMatch(/\{storageBlocked && \(/);
  });

  test('both probes run client-side only, after mount', () => {
    // Running at module scope would execute during SSR, where document and
    // window do not exist.
    expect(adminLogin).toMatch(/useEffect\(\(\) => \{ setCookiesBlocked\(!cookiesWritable\(\)\); \}, \[\]\)/);
    expect(joinModal).toMatch(/useEffect\(\(\) => \{ setStorageBlocked\(!localStorageWritable\(\)\); \}, \[\]\)/);
  });

  test('the alerts are announced to assistive tech', () => {
    expect(adminLogin).toMatch(/role="alert"[\s\S]{0,400}COOKIE_BLOCKED_MESSAGE/);
    expect(joinModal).toMatch(/role="alert"[\s\S]{0,400}STORAGE_BLOCKED_MESSAGE/);
  });
});

describe('the messages say what to do', () => {
  test.each([
    ['cookie', COOKIE_BLOCKED_MESSAGE],
    ['storage', STORAGE_BLOCKED_MESSAGE],
  ])('the %s message names both the symptom and a remedy', (_label, msg) => {
    expect(msg.toLowerCase()).toMatch(/blocking/);
    expect(msg.length).toBeGreaterThan(60);
    // No jargon a participant cannot act on.
    expect(msg).not.toMatch(/HttpOnly|JWT|localStorage|ITP/);
  });
});
