import os

directories = [
    r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\frontend\app",
    r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\backend",
    r"C:\Users\Home\.gemini\antigravity\brain\5b7040a3-9aff-45ab-afd3-57679327bdc9"
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    orig_content = content
    # Replace variable names first
    content = content.replace("ebitda_2050", "terminal_ebitda")
    content = content.replace("EBITDA_2050", "Terminal_EBITDA")
    content = content.replace("EBITDA 2050", "Terminal EBITDA")
    content = content.replace("EBITDA₂₀₅₀", "Terminal EBITDA")
    
    # Textual references
    content = content.replace("the 2050 ledger", "the Year 3 ledger")
    content = content.replace("the 2050 exit multiple", "the Year 3 exit multiple")
    content = content.replace("in 2050", "in Year 3")
    content = content.replace("Meeting, 2050", "Meeting, Year 3")
    content = content.replace("EBITDA 2050", "Terminal EBITDA")
    content = content.replace("(2050)", "(Year 3)")
    content = content.replace("2050 outcome profiles", "Year 3 outcome profiles")
    content = content.replace("2050 Annual Report", "Year 3 Annual Report")
    content = content.replace("2050 ANNUAL REPORT", "YEAR 3 ANNUAL REPORT")
    content = content.replace("2050 carbon tax", "Year 3 carbon tax")
    content = content.replace("2050 border adjustments", "Year 3 border adjustments")
    content = content.replace("Report 2050", "Report (Year 3)")
    content = content.replace("SCORECARD 2050", "SCORECARD (YEAR 3)")
    content = content.replace("Terminal Valuation 2050", "Terminal Valuation")
    content = content.replace("2050 Terminal Valuation", "Year 3 Terminal Valuation")
    content = content.replace("2050 Regenerative Multiple", "Year 3 Regenerative Multiple")
    content = content.replace("2050 Activist Ultimatum", "Year 3 Activist Ultimatum")
    content = content.replace("The year is 2050.", "Three years have passed.")
    content = content.replace("The year is <strong>2050</strong>.", "<strong>Three years</strong> have passed.")
    content = content.replace("2050 Board of Directors", "Year 3 Board of Directors")
    content = content.replace("© 2050", "© Year 3")
    content = content.replace("projected 2050", "projected Year 3")
    content = content.replace("gold standard of 2050", "gold standard of Year 3")
    content = content.replace("The 2050 market", "The Year 3 market")
    content = content.replace("2050 Profile Archetype", "Year 3 Profile Archetype")
    content = content.replace("2050 valuation", "Year 3 valuation")
    
    # Catch-all
    content = content.replace("2050", "Year 3")

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated: {filepath}")

for d in directories:
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith(('.js', '.jsx', '.py', '.md')):
                filepath = os.path.join(root, f)
                process_file(filepath)
