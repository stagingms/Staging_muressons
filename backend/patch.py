import os

path = 'router.py'
content = open(path, encoding='utf-8').read()

old1 = '''    if req.role == "player":
        from admin_router import _player_registry
        player = next((p for p in _player_registry if p["player_id"] == req.user_id), None)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found.")
        player["username"] = req.username.strip()
        
        session_id = player.get("session_id")'''

new1 = '''    if req.role == "player":
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

content = content.replace(old1, new1)
if old1 not in content and 'target_session_id' in content:
    print('Patch 1 successful!')

old2 = '''    # Find the player in the registry
    player_record = next(
        (p for p in _player_registry if p["player_id"] == req.player_id),
        None
    )
    if not player_record:'''

new2 = '''    # Find the player in the registry
    player_record = next(
        (p for p in _player_registry if p["player_id"] == req.player_id),
        None
    )
    
    if not player_record:
        import database as db
        for sid, sess in db._sessions.items():
            for p in sess.get("registered_players", []):
                if p.get("player_id") == req.player_id:
                    player_record = p
                    player_record["session_id"] = sid
                    break
            if player_record: break

    if not player_record:'''

content = content.replace(old2, new2)
if old2 not in content and 'for p in sess.get("registered_players", [])' in content:
    print('Patch 2 successful!')

open(path, 'w', encoding='utf-8').write(content)
