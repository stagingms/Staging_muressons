import os
content = open('router.py', encoding='utf-8').read()

old = '''            for sid, sess in db._sessions.items():
                for p_rec in sess.get("registered_players", []):
                    if p_rec.get("player_id") == req.user_id:
                        player = p_rec
                        target_session_id = sid
                        break
                if target_session_id: break'''

new = '''            for sid, sess in db._sessions.items():
                if sess.get("player_id") == req.user_id:
                    player = {"player_id": req.user_id, "session_id": sess.get("parent_cohort_id")}
                    target_session_id = sid
                    break'''

if old in content:
    content = content.replace(old, new)
    open('router.py', 'w', encoding='utf-8').write(content)
    print("Replaced successfully")
else:
    print("String not found")
