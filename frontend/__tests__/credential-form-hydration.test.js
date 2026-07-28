/**
 * Credential forms must tolerate password-manager DOM injection.
 *
 * Password managers and security extensions (NortonLifeLock stamps
 * data-nlok-ref-guid; 1Password, LastPass, Bitwarden do equivalents) decorate
 * login forms BEFORE React hydrates. The server HTML and the client tree then
 * differ and Next.js reports:
 *
 *   "A tree hydrated but some attributes of the server rendered HTML didn't
 *    match the client properties."
 *
 * Nothing in our markup is wrong and we cannot stop a third-party extension,
 * so every element an extension decorates carries suppressHydrationWarning.
 *
 * This shipped twice: first on the credential INPUTS, then again on the submit
 * BUTTON, because suppressHydrationWarning is one level deep — putting it on
 * the form does not cover the button. This test pins every credential-form
 * submit button so the third occurrence fails CI instead of a user's console.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const read = (p) => fs.readFileSync(path.join(APP, p), 'utf8');

// Files that render a credential form, and how many submit buttons each has.
const CREDENTIAL_FORMS = [
  ['components/AdminLogin.js', 1],
  ['components/JoinCohortModal.js', 1],
  ['components/ChangePasswordModal.js', 1],
  ['admin/facilitator/page.js', 2], // login gateway + change-password modal
];

/** Extract each `<button ... type="submit" ...>` opening tag. */
function submitButtonTags(src) {
  const tags = [];
  const re = /<button\b[^>]*>/gs;
  let m;
  while ((m = re.exec(src)) !== null) {
    if (m[0].includes('type="submit"')) tags.push(m[0]);
  }
  return tags;
}

describe('credential-form hydration safety', () => {
  test.each(CREDENTIAL_FORMS)('%s: every submit button suppresses hydration warnings', (file, expected) => {
    const tags = submitButtonTags(read(file));
    expect(tags).toHaveLength(expected);
    tags.forEach((tag) => {
      expect(tag).toContain('suppressHydrationWarning');
    });
  });

  test('AdminLogin also guards the facilitator-ID input', () => {
    // The username field is half of a saved credential and gets tagged too.
    const src = read('components/AdminLogin.js');
    const input = src.slice(src.indexOf('<input'), src.indexOf('</div>', src.indexOf('<input')));
    expect(input).toContain('suppressHydrationWarning');
  });

  test('PasswordInput guards the password field itself', () => {
    expect(read('components/PasswordInput.js')).toContain('suppressHydrationWarning');
  });
});
