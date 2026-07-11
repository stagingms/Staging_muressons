import os

file_path = r"C:\Users\Home\.gemini\antigravity\brain\f71caabe-fe9d-4a51-a28c-81a4c4e3bf5f\full_facilitator_manual.md"
base = "C:/Users/Home/.gemini/antigravity/brain/f71caabe-fe9d-4a51-a28c-81a4c4e3bf5f"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    # 1. After '### 2.2 Accessing the Facilitator Dashboard'
    (
        "### 2.2 Accessing the Facilitator Dashboard\r\n\r\nNavigate to:",
        f"### 2.2 Accessing the Facilitator Dashboard\r\n\r\n![Admin Gateway — choose between God Mode and Facilitator access]({base}/admin_gateway_1781970681072.png)\r\n\r\nNavigate to:"
    ),
    # 2. After '### 2.3 Creating a New Session'
    (
        "### 2.3 Creating a New Session\r\n\r\n**Steps:**",
        f"### 2.3 Creating a New Session\r\n\r\n![Create Cohort modal — configure paradigm, difficulty, pathway, and side tracks]({base}/session_creation_1781970599733.png)\r\n\r\n**Steps:**"
    ),
    # 8. After '### 2.8 Registering Players'
    (
        "### 2.8 Registering Players and Distributing Player IDs\r\n\r\nEach team in the simulation",
        f"### 2.8 Registering Players and Distributing Player IDs\r\n\r\n![Player Registry — manage enrolled players, team assignments, and credentials]({base}/s13_player_registry.png)\r\n\r\nEach team in the simulation"
    ),
    # 3. After '## 3. The 29-Tab Facilitator Dashboard'
    (
        "## 3. The 29-Tab Facilitator Dashboard\r\n\r\nThe Facilitator Dashboard",
        f"## 3. The 29-Tab Facilitator Dashboard\r\n\r\n![Facilitator Dashboard home — at-a-glance overview of active cohorts and KPI health]({base}/s07_dashboard_home.png)\r\n\r\nThe Facilitator Dashboard"
    ),
    # 4. After '### Group 1: Session Control'
    (
        "### Group 1: Session Control\r\n\r\n#### Tab 1",
        f"### Group 1: Session Control\r\n\r\n![The Teleprompter — round facilitation script with talking points and engine flags]({base}/s11_teleprompter.png)\r\n\r\n#### Tab 1"
    ),
    # 15. After '#### Tab 2 — Session Settings' (configuration sidebar)
    (
        "#### Tab 2 \u2014 Session Settings\r\nEdit session metadata: name, decision paradigm (read-only after round 1 decisions are submitted), difficulty tier, and side track assignments. You can adjust difficulty tier at any time between rounds.\r\n\r\n#### Tab 3",
        f"#### Tab 2 \u2014 Session Settings\r\nEdit session metadata: name, decision paradigm (read-only after round 1 decisions are submitted), difficulty tier, and side track assignments. You can adjust difficulty tier at any time between rounds.\r\n\r\n![Configuration sidebar — auto-pause, undo round, regulatory sandbox, and more]({base}/s09_sidebar_config.png)\r\n\r\n#### Tab 3"
    ),
    # 5. After '### Group 2: Live Monitoring'
    (
        "### Group 2: Live Monitoring\r\n\r\n#### Tab 5",
        f"### Group 2: Live Monitoring\r\n\r\n![Cohort Pulse Heatmap — colour-coded KPI health across all teams]({base}/cohort_pulse_1781970572017.png)\r\n\r\n#### Tab 5"
    ),
    # 6. After 'Decision Replay' in Group 3
    (
        "### Group 3: Decision Intelligence\r\n\r\n#### Tab 9 \u2014 Decision Replay\r\nReview any team\u2019s complete decision history",
        f"### Group 3: Decision Intelligence\r\n\r\n#### Tab 9 \u2014 Decision Replay\r\n\r\n![Decision Timeline — chronological audit of team choices across rounds]({base}/s16_decision_history.png)\r\n\r\nReview any team\u2019s complete decision history"
    ),
    # 13. After '#### Tab 11 — Annotation Layer' (teaching journal)
    (
        "#### Tab 11 \u2014 Annotation Layer\r\nAdd facilitator notes directly to the simulation state.",
        f"#### Tab 11 \u2014 Annotation Layer\r\n\r\n![Teaching Journal — private facilitator notes and timestamped annotations]({base}/s17_teaching_journal.png)\r\n\r\nAdd facilitator notes directly to the simulation state."
    ),
    # 7. After '### Group 5: Output & Assessment'
    (
        "### Group 5: Output & Assessment\r\n\r\n#### Tab 15",
        f"### Group 5: Output & Assessment\r\n\r\n![Leaderboard Matrix — cross-pathway normalised team rankings]({base}/s12_leaderboard.png)\r\n\r\n#### Tab 15"
    ),
    # 9. After '### Round 1 — ESG Baseline Assessment'
    (
        "### Round 1 \u2014 ESG Baseline Assessment\r\n\r\n**Simulation Date**: Year 0 \u2014 Board Mandate",
        f"### Round 1 \u2014 ESG Baseline Assessment\r\n\r\n![Round 1 briefing as seen by players — the ESG Materiality audit narrative]({base}/s02_round_briefing.png)\r\n\r\n**Simulation Date**: Year 0 \u2014 Board Mandate"
    ),
    # 14. After '### 5.1 Overview'
    (
        "### 5.1 Overview and Control Hierarchy\r\n\r\nSide tracks are self-contained parallel mini-simulations",
        f"### 5.1 Overview and Control Hierarchy\r\n\r\n![Facilitator sidebar showing Analytics & Assessment tools]({base}/s08_sidebar_analytics.png)\r\n\r\nSide tracks are self-contained parallel mini-simulations"
    ),
    # 10. After '### 7.1 CEO Interview'
    (
        "### 7.1 CEO Interview (If Enabled)\r\n\r\nThe CEO Interview module provides a post-game competency assessment.",
        f"### 7.1 CEO Interview (If Enabled)\r\n\r\n![CEO Interview assessment — competency spider diagram with 6 dimensions]({base}/ceo_interview_1781970547757.png)\r\n\r\nThe CEO Interview module provides a post-game competency assessment."
    ),
    # 11. After '### 8.2 Decision Overrides'
    (
        "### 8.2 Decision Overrides\r\n\r\n`backend/decision_overrides.json`",
        f"### 8.2 Decision Overrides\r\n\r\n![Team Impersonation — view any team's cockpit exactly as the player sees it]({base}/s14_impersonation.png)\r\n\r\n`backend/decision_overrides.json`"
    ),
    # 12. After '### 10.2 Debrief Structure'
    (
        "### 10.2 Debrief Structure\r\n\r\n#### Phase 1: Terminal Valuation Reveal",
        f"### 10.2 Debrief Structure\r\n\r\n![Cohort Analytics — session performance data for post-session debrief]({base}/s15_cohort_analytics.png)\r\n\r\n#### Phase 1: Terminal Valuation Reveal"
    ),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        count += 1
    else:
        print(f"WARNING: Could not find target text for replacement #{replacements.index((old, new)) + 1}")
        # Try with \n instead of \r\n
        old_lf = old.replace("\r\n", "\n")
        new_lf = new.replace("\r\n", "\n")
        if old_lf in content:
            content = content.replace(old_lf, new_lf, 1)
            count += 1
            print(f"  -> Found with LF line endings instead, applied successfully")
        else:
            print(f"  -> Also not found with LF endings. First 80 chars: {repr(old[:80])}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nDone! Applied {count}/{len(replacements)} replacements.")
