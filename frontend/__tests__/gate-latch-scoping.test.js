/**
 * A completion latch must not outlive the session that earned it.
 *
 * THE BUG: `csrdDone` in page.js was a plain `useState(false)`, so it survived a
 * change of session in the same tab. A facilitator or tester who submitted the
 * R2 CSRD assessment in one cohort saw the NEXT player open Round 2 with
 * "✅ CSRD Assessment Submitted" already ticked, having entered nothing — and
 * because `isCommitBlocked` reads the same flag, that player could commit Round 2
 * without ever opening the assessment.
 *
 * The reason it happened is worth pinning as hard as the behaviour: page.js had a
 * reset effect keyed on `sim.sessionId` that cleared these flags by hand.
 * `csrdDone` was declared 87 lines below it and never joined the list;
 * `boardroomDone` had drifted the same way. A hand-maintained reset list works
 * only while everyone remembers it, and two of three latches did not. So the
 * scoping is now structural (hooks/useSessionLatch.js) and the tripwire below
 * fails if any future latch reverts to bare page state.
 */
import { renderHook, act } from '@testing-library/react';
import fs from 'fs';
import path from 'path';
import useSessionLatch from '../app/hooks/useSessionLatch';

describe('useSessionLatch', () => {
  it('starts unlatched', () => {
    const { result } = renderHook(() => useSessionLatch('sid-1'));
    expect(result.current[0]).toBe(false);
  });

  it('latches for the session that set it', () => {
    const { result } = renderHook(() => useSessionLatch('sid-1'));
    act(() => result.current[1]());
    expect(result.current[0]).toBe(true);
  });

  it('DROPS when the session changes — the reported bug', () => {
    const { result, rerender } = renderHook(({ sid }) => useSessionLatch(sid), {
      initialProps: { sid: 'player-A' },
    });
    act(() => result.current[1]());
    expect(result.current[0]).toBe(true);

    // Same tab, a different player joins.
    rerender({ sid: 'player-B' });
    expect(result.current[0]).toBe(false);
  });

  it('survives a momentarily unknown session id', () => {
    // The latch must NOT drop mid-refresh: dropping it is what sent players back
    // through a mini-game they had already completed.
    const { result, rerender } = renderHook(({ sid }) => useSessionLatch(sid), {
      initialProps: { sid: 'sid-1' },
    });
    act(() => result.current[1]());
    rerender({ sid: undefined });
    expect(result.current[0]).toBe(true);
    rerender({ sid: 'sid-1' });
    expect(result.current[0]).toBe(true);
  });

  it('re-latches for the new session independently', () => {
    const { result, rerender } = renderHook(({ sid }) => useSessionLatch(sid), {
      initialProps: { sid: 'player-A' },
    });
    act(() => result.current[1]());
    rerender({ sid: 'player-B' });
    act(() => result.current[1]());
    expect(result.current[0]).toBe(true);
    rerender({ sid: 'player-A' });
    expect(result.current[0]).toBe(false);
  });
});

describe('page.js completion latches', () => {
  const SRC = fs.readFileSync(path.join(__dirname, '..', 'app', 'page.js'), 'utf8');

  // Every gate whose local flag, if leaked, lets a player skip required work.
  const LATCHES = ['stakeholderDone', 'csrdDone', 'boardroomDone'];

  it.each(LATCHES)('%s is session-scoped, not bare page state', (name) => {
    expect(SRC).toMatch(
      new RegExp(`const \\[${name},\\s*\\w+\\]\\s*=\\s*useSessionLatch\\(`),
    );
    // A bare useState would silently restore the leak.
    expect(SRC).not.toMatch(new RegExp(`const \\[${name},[^\\]]*\\]\\s*=\\s*useState`));
  });

  it('still gates the R2 commit on the CSRD assessment', () => {
    // The leak was only harmful because this gate trusts the local flag. If the
    // gate stops reading it the latch work is pointless; if the gate stops
    // existing, the assessment stops being mandatory.
    expect(SRC).toMatch(/hasSubmittedMatrix\s*=\s*csrdDone\s*\|\|/);
    expect(SRC).toMatch(/roundNumber === 2 && !hasSubmittedMatrix/);
  });

  it('does not clear the latches by hand any more', () => {
    // The reset effect is the pattern that failed. Re-adding a latch to it would
    // reintroduce the "remember to join the list" trap.
    const effect = SRC.slice(
      SRC.indexOf('Reset transient minigame UI'),
      SRC.indexOf('}, [sim.sessionId]);', SRC.indexOf('Reset transient minigame UI')),
    );
    expect(effect).not.toMatch(/setStakeholderDone|setCsrdDone|setBoardroomDone/);
  });
});
