import os
import re

file_path = r'c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\backend\router.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
in_commit_turn = False
in_try_block = False

for i, line in enumerate(lines):
    if line.startswith('async def commit_turn(session_id: str, body: CommitTurnRequest):'):
        in_commit_turn = True
        out_lines.append(line)
        continue
    
    if in_commit_turn:
        if line.strip() == 'await commit_lock.acquire()':
            out_lines.append(line)
            out_lines.append('    try:\n')
            in_try_block = True
            continue
            
        if line.strip() == 'commit_lock.release()':
            if in_try_block:
                # Replace with finally block
                out_lines.append('    finally:\n')
                out_lines.append('        commit_lock.release()\n')
                in_try_block = False
            continue
            
        if line.strip() == 'return CommitTurnResponse(':
            if in_try_block:
                out_lines.append('    finally:\n')
                out_lines.append('        commit_lock.release()\n')
                in_try_block = False
                
        if line.startswith('def '):
            in_commit_turn = False
            
        if in_try_block and line.strip() != '' and not line.startswith('#'):
            # This is too complex to indent properly with regex. Let's do it safely.
            pass

# Instead of indenting 600 lines, I'll just change `commit_lock.release()` to `finally:` using a safe AST or regex logic... wait, I can just do this manually for the few return points, but the function raises HTTPExceptions in multiple places. It's safer to just wrap it.
