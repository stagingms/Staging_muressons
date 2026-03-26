import os

path = 'router.py'
content = open(path, encoding='utf-8').read()

old1 = '''    if req.role == "player":
        from admin_router import _player_registry
        import database as db
        player = next((p for p in _player_registry if p["player_id"] == req.user_id), None)
        
        target_session_id = None
        if not player:
            for sid, sess in db._sessions.items():
                for p_rec in sess.get("registered_players", []):
                    if p_rec.get("player_id") == req.user_id:
                        player = p_rec
                        target_session_id = sid
                        break
                if target_session_id: break
                
        if not player:
            raise HTTPException(status_code=404, detail="Player not found.")
        player["username"] = req.username.strip()
        
        session_id = player.get("session_id") or target_session_id'''

new1 = '''    if req.role == "player":
        from admin_router import _player_registry
        import database as db
        player = next((p for p in _player_registry if p["player_id"] == req.user_id), None)
        
        target_session_id = None
        if not player:
            # Look through all active independent sessions
            for sid, sess in db._sessions.items():
                if sess.get("player_id") == req.user_id:
                    player = {"player_id": req.user_id, "session_id": sess.get("parent_cohort_id")}
                    target_session_id = sid
                    break
                    
        if not player:
            raise HTTPException(status_code=404, detail="Player not found.")
            
        player["username"] = req.username.strip()
        
        session_id = player.get("session_id") or target_session_id'''

if old1 in content:
    content = content.replace(old1, new1)
    print('Patch 1 successful!')
else:
    print('Patch 1 failed to match.')

old2 = '''    if not player_record:
        import database as db
        for sid, sess in db._sessions.items():
            for p in sess.get("registered_players", []):
                if p.get("player_id") == req.player_id:
                    player_record = p
                    player_record["session_id"] = sid
                    break
            if player_record: break

    if not player_record:'''

new2 = '''    if not player_record:
        import database as db
        for sid, sess in db._sessions.items():
            if sess.get("player_id") == req.player_id:
                player_record = {"player_id": req.player_id, "session_id": sess.get("parent_cohort_id")}
                break

    if not player_record:'''

if old2 in content:
    content = content.replace(old2, new2)
    print('Patch 2 successful!')
else:
    print('Patch 2 failed to match.')

open(path, 'w', encoding='utf-8').write(content)
