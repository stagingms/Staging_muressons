import database as db
import asyncio

db._load_from_disk()

req_user_id = 'MUR-WOV'
req_session_id = 'f8ecc7e1-05b9-4861-ad1c-c2778889fc51'

for u_id in [req_user_id, req_session_id]:
    player = None
    sess = db._sessions.get(u_id)
    if sess and sess.get("player_id"):
        player = {"player_id": sess["player_id"], "session_id": u_id}
        target_session_id = u_id

    if not player:
        for sid, s in db._sessions.items():
            if s.get("player_id") == u_id:
                player = {"player_id": u_id, "session_id": s.get("parent_cohort_id")}
                target_session_id = sid
                break

    print(f"For {u_id}, player found: {player}")
