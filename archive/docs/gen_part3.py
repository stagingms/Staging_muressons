"""Part 3: §5-§10C — Shadow Board, Endings, Terminal Val, Side Tracks, Agents, God Mode, Verticals."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_styles import *

def build_section5(doc):
    add_page_break(doc)
    doc.add_heading('PART 3 — ADVANCED SYSTEMS', level=1)
    doc.add_heading('§5. The Shadow Board Audit — Deep Dive', level=1)
    
    doc.add_heading('5.1 Overview', level=2)
    doc.add_paragraph('The Shadow Board Audit is a mandatory interception at Round 5. Three independent personas evaluate the player\'s strategy and offer recommendations. Players may accept or reject each persona\'s advice. Rejections set hidden flags that cascade to R10 ending pathways.')
    add_screenshot_placeholder(doc, 'Shadow Board Audit modal with 3 persona cards')
    
    doc.add_heading('5.2 Persona Profiles', level=2)
    add_styled_table(doc, ['Persona', 'Name', 'Title', 'Monitored Metric', 'Rejection Flag'],
        [['Shareholder', 'Victoria Chen', 'Independent NED, Corporate Governance Institute', 'Governance Risk', 'shareholder_alienated'],
         ['Community Leader', 'Amara Okafor', 'Director, Global Justice Alliance', 'Social License', 'community_distrust'],
         ['Environmental Scientist', 'Dr. Kenji Tanaka', 'Lead Author, IPCC AR7 Working Group', 'Carbon Intensity', 'scientist_dismissed']])
    
    doc.add_heading('5.3 Rejection Mechanics', level=2)
    doc.add_paragraph('Each rejection sets a hidden flag with cascading consequences:')
    add_bullet_list(doc, [
        'shareholder_alienated → Activates Activist Ultimatum ending pathway; -10 tolerance on Activist Investor agent; Governance Risk penalty at R10.',
        'community_distrust → Activates Community Uprising pathway variant; Community Leader agent enters hostile state; Social License floor drops by 10.',
        'scientist_dismissed → Activates Climate Black Swan pathway; Carbon tax increase at R10; Scientist agent triggers environmental exposé.',
    ], bold_prefix=True)
    add_callout(doc, 'Shadow Board rejections are IRREVERSIBLE. The flags persist through R10 and directly determine which ending pathway activates.', 'warning')
    
    doc.add_heading('5.4 Facilitation Script', level=2)
    doc.add_paragraph('BEFORE the audit: "You are about to receive feedback from three independent board advisors. Each will evaluate your strategy from their expertise. You may accept or reject their advice — but your response will have consequences."')
    doc.add_paragraph('AFTER the audit (debrief): "The Shadow Board represented three dimensions of stakeholder governance. Rejection of expertise signals a governance failure — a pattern we see in real-world corporate crises from Boeing to Volkswagen."')

def build_section6(doc):
    add_page_break(doc)
    doc.add_heading('§6. Ending Pathways', level=1)
    
    doc.add_heading('6.1 Pathway Overview', level=2)
    add_styled_table(doc, ['ID', 'Pathway', 'Trigger Condition', 'R10 Crisis Theme'],
        [['default', 'Activist Ultimatum', 'Default (or shareholder_alienated)', 'Activist investor blocking stake'],
         ['climate_black_swan', 'Climate Black Swan', 'scientist_dismissed flag', 'IPCC special report triggers carbon price shock'],
         ['regulatory_shutdown', 'Regulatory Shutdown', 'governance_risk > 60 at R8', 'EU regulatory enforcement action'],
         ['community_uprising', 'Community Uprising', 'community_distrust + SLO < 40', 'Multi-city protests and supply chain blockade'],
         ['market_disruption', 'Market Disruption', 'technology vertical + low innovation', 'Disruptive competitor captures 40% market share']])
    
    doc.add_heading('6.2 Foreshadowing Events', level=2)
    doc.add_paragraph('Each pathway plants foreshadowing news items in the Market Feed between R5-R8. These subtle signals allow attentive players to anticipate the R10 crisis:')
    add_screenshot_placeholder(doc, 'Market Feed showing foreshadowing news item')
    add_bullet_list(doc, [
        'Activist Ultimatum: R6 — "FutureFirst Fund increases Muressons stake to 4.8%"; R8 — "Activist consortium reportedly near blocking threshold"',
        'Climate Black Swan: R6 — "IPCC fast-tracks special report on industrial emissions"; R7 — "EU carbon border adjustment negotiations accelerate"',
        'Regulatory Shutdown: R6 — "DG FISMA opens preliminary governance review"; R8 — "Commissioner Petrova signals enforcement action"',
    ])
    
    doc.add_heading('6.3 Pathway-Specific M_R Calculators', level=2)
    doc.add_paragraph('Each pathway has a custom M_R bonus calculator that replaces or supplements the default formula:')
    add_bullet_list(doc, [
        'Activist Ultimatum: SAE (Stakeholder Alignment Efficiency) = weighted score across all agent tolerances',
        'Climate Black Swan: CRI (Climate Risk Index) = CI reduction × nature-based investment / carbon tax exposure',
        'Regulatory Shutdown: GCI (Governance Compliance Index) = governance risk reduction × disclosure quality',
        'Community Uprising: SCI (Social Cohesion Index) = SLO × just transition investment / community grievances',
    ], bold_prefix=True)

def build_section7(doc):
    add_page_break(doc)
    doc.add_heading('§7. Terminal Valuation Deep Dive', level=1)
    
    doc.add_heading('7.1 Full Formula', level=2)
    p = doc.add_paragraph()
    r = p.add_run('TV = (EBITDA - Carbon_Tax × CO₂_Tonnage) × Exit_Multiple × M_R')
    r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(11)
    
    doc.add_heading('7.2 Worked Examples', level=2)
    add_styled_table(doc, ['Scenario', 'EBITDA', 'Carbon Cost', 'Net', 'Multiple', 'M_R', 'Terminal Value'],
        [['Regenerative Titan', '$12.5M', '$2.1M', '$10.4M', '12.0×', '1.85', '~$230M'],
         ['De-risked Safe Haven', '$10.0M', '$3.5M', '$6.5M', '12.0×', '1.30', '~$101M'],
         ['Fragile Giant', '$8.0M', '$5.0M', '$3.0M', '12.0×', '0.90', '~$32M'],
         ['Stranded Relic', '$5.0M', '$6.0M', '-$1.0M', '12.0×', '0.60', '~-$7.2M']])
    add_callout(doc, 'The spread between Titan ($230M) and Relic (-$7.2M) is the core teaching moment. A 25× gap driven entirely by strategic decisions across 10 rounds.', 'tip')
    
    doc.add_heading('7.3 Carbon Tax Impact', level=2)
    add_styled_table(doc, ['Tax Rate', 'Low CI Team (15 avg)', 'Mid CI Team (40 avg)', 'High CI Team (70 avg)'],
        [['$250/ton', '-$0.9M', '-$2.5M', '-$4.4M'],
         ['$350/ton', '-$1.3M', '-$3.5M', '-$6.1M'],
         ['$750/ton', '-$2.8M', '-$7.5M', '-$13.1M']])
    
    doc.add_heading('7.4 Archetype Classification', level=2)
    add_styled_table(doc, ['Archetype', 'M_R Range', 'Description'],
        [['Regenerative Titan', '≥ 1.80', 'Industry leader in sustainable value creation. ESG-integrated strategy generates premium returns.'],
         ['De-risked Safe Haven', '1.20 – 1.79', 'Solid ESG performance with moderate innovation. Attractive to institutional investors.'],
         ['Fragile Giant', '0.80 – 1.19', 'Financially adequate but systemically vulnerable. ESG gaps create hidden risk exposure.'],
         ['Stranded Relic', '< 0.80', 'Terminal decline. Stranded assets, regulatory exposure, and stakeholder revolt make recovery unlikely.']])
    add_screenshot_placeholder(doc, 'Final Report with terminal valuation breakdown and archetype badge')
    add_screenshot_placeholder(doc, 'Sustainability Balanced Scorecard with M_R breakdown table')

def build_section8(doc):
    add_page_break(doc)
    doc.add_heading('§8. Side Tracks', level=1)
    doc.add_heading('8.1 Architecture Overview', level=2)
    doc.add_paragraph('Side tracks are optional enrichment modules that run parallel to the main 10-round loop. Each track has its own scoring dimensions, data bridges to the main simulation, and facilitator assignment controls.')
    add_screenshot_placeholder(doc, 'Facilitator Dashboard side track assignment panel')
    
    doc.add_heading('8.2 Track Catalog', level=2)
    add_styled_table(doc, ['Track', 'Rounds', 'Scoring Dimensions', 'Main Sim Integration'],
        [['Supply Chain Ethics', '7 rounds', 'Transparency, Labour, Environment, Governance, Innovation, Community, Compliance', 'Tyler Consumer Trust Index feeds reputation; disruption score affects OPEX'],
         ['Ethics & Sustainability', '5 rounds', 'Ethical reasoning, stakeholder analysis, regulatory awareness', 'Ethics score modifies governance risk; framework mastery unlocks M_R micro-bonus'],
         ['Stakeholder Management', '5 rounds', 'Engagement quality, stakeholder satisfaction, communication', 'Stakeholder scores modify agent tolerance levels'],
         ['Sustainability Reporting', '5 rounds', 'ESRS compliance, data quality, materiality accuracy', 'Reporting score modifies Green Bond eligibility and investor confidence']])
    
    doc.add_heading('8.3 Supply Chain Deep Dive', level=2)
    doc.add_paragraph('The Supply Chain Ethics track is the most complex side track, running for 7 rounds with a 7-dimension weighted composite score. Each round presents an ethical dilemma in supply chain management.')
    doc.add_paragraph('Tyler Consumer Trust Index (CTI): A composite metric that bridges supply chain transparency decisions back to the main simulation, affecting group reputation and consumer confidence in the Consumer Goods BU.')

def build_section9(doc):
    add_page_break(doc)
    doc.add_heading('§9. Autonomous Stakeholder Agents', level=1)
    doc.add_heading('9.1 System Overview', level=2)
    doc.add_paragraph('Five autonomous NPC stakeholders monitor simulation metrics independently and react based on satisfaction thresholds. They escalate through 4 lifecycle states: Supportive → Concerned → Hostile → Adversarial.')
    add_screenshot_placeholder(doc, 'Autonomous Stakeholders panel showing agent states')
    
    doc.add_heading('9.2 Agent Profiles', level=2)
    add_styled_table(doc, ['Agent', 'Name', 'Icon', 'Monitored Metrics', 'Escalation Trigger'],
        [['Activist Investor', 'Elise Thornton', '🦅', 'Reputation, Carbon Intensity, Governance', 'Rep < 40 → Public Campaign; < 30 → Proxy Fight'],
         ['EU Regulator', 'Commissioner Sofia Petrova', '🏛️', 'Governance Risk, TNFD Disclosure', 'Gov Risk > 60 → Investigation; Greenwashing → Enforcement'],
         ['Community Leader', 'Rajesh Patil', '🏘️', 'Social License, Water Stress, Just Transition Fund', 'SLO < 40 → Protest; Water Stress > 60 → Legal Action'],
         ['Journalist', 'Jaya Mehta', '📰', 'Transparency, Reputation, Governance', 'Rep drop > 10 → Investigation; Greenwash → Exposé']])
    
    doc.add_heading('9.3 Cascade Chain Analysis', level=2)
    doc.add_paragraph('When one agent enters hostile state, it can trigger cascades to other agents:')
    add_bullet_list(doc, [
        'Journalist hostile → -5 rep → triggers Activist Investor escalation → may trigger Regulator investigation',
        'Community Leader protest → -3 reputation → Journalist investigation → viral story → Activist response',
        'Regulator enforcement → €5-25M fine → treasury hit → triggers all agents to reassess satisfaction',
    ])
    add_callout(doc, 'Total Corporate Collapse: If ALL 4 agents reach adversarial state simultaneously, the simulation triggers a special game-over scenario. This is extremely rare but pedagogically powerful.', 'important')

def build_section10(doc):
    add_page_break(doc)
    doc.add_heading('§10. Facilitator God Mode & Overrides', level=1)
    doc.add_paragraph('God Mode provides the Super Administrator with system-wide control over all simulation parameters. These tools should be used judiciously to enhance learning outcomes.')
    
    items = [
        'Carbon Tax Override: Adjust $/ton in real-time ($250 default, range $0-$1000). Use to demonstrate carbon pricing impact on terminal value.',
        'Custom Archetypes: Define M_R thresholds, custom archetype names, icons, and gradient colours for each cohort.',
        'Pedagogical Toggles: 30+ feature flags controlling engine visibility, prediction gates, timer pressure, peer learning, board governance, etc.',
        'Ending Pathway Selection: Pre-select a specific ending pathway or allow flag-based automatic selection.',
        'Industry Vertical Substitution: Replace default BUs with industry-specific alternatives (see §10C).',
        'What-If Mode: Terminal valuation predictor that shows projected outcomes based on hypothetical decisions.',
        'WebSocket Real-Time Interference: Live interventions pushed to all connected clients via WebSocket.',
        'Option Shuffle Engine: Anti-positional-bias system that randomizes A/B/C option order per session. Deterministic shuffle ensures reproducibility.',
        'Decision Timer: Configurable 3-10 minute countdown per round. Auto-submit or reputation penalty on expiry. Models real-world executive time pressure.',
    ]
    add_bullet_list(doc, items, bold_prefix=True)

def build_section10c(doc):
    add_page_break(doc)
    doc.add_heading('§10C. Industry Vertical Swapping Guide', level=1)
    
    doc.add_heading('10C.1 Overview', level=2)
    doc.add_paragraph('The simulation supports industry vertical substitution — replacing default BUs with industry-specific alternatives that share structural characteristics. This allows facilitators to tailor the simulation to cohort expertise (e.g., Oil & Gas for energy sector MBA students).')
    add_screenshot_placeholder(doc, 'God Mode dashboard — Industry Vertical selector')
    
    doc.add_heading('10C.2 Slot-Fit Architecture', level=2)
    doc.add_paragraph('Each of the 4 default BU "slots" can only be replaced by verticals sharing industry characteristics (heavy/light, physical/digital):')
    add_styled_table(doc, ['Default Slot', 'Slot Characteristics', 'Compatible Verticals'],
        [['Pharma 💊', 'Heavy industry, physical assets, regulatory', 'Oil & Gas 🛢️'],
         ['Electronics ⚡', 'High carbon, complex supply chain', 'Oil & Gas 🛢️'],
         ['Consumer Goods 🛒', 'Supply chain, natural resources, packaging', 'Retail/FMCG 🛍️, Agriculture 🌾'],
         ['Software 💻', 'Asset-light, governance-heavy, talent-dependent', 'Banking & Financial Services 🏦, Technology 🧠']])
    
    doc.add_heading('10C.3 Vertical Profiles', level=2)
    add_styled_table(doc, ['Vertical', 'Icon', 'Slot', 'Revenue', 'OPEX', 'CI', 'Water', 'NCD', 'Gov Risk', 'Description'],
        [['Oil & Gas', '🛢️', 'pharma/electronics', '$22M', '$15M', '95', '70', '350', '20', 'Extreme carbon, stranded asset risk'],
         ['Banking & FS', '🏦', 'software', '$14M', '$8M', '8', '5', '15', '30', 'High financed emissions, systemic risk'],
         ['Retail/FMCG', '🛍️', 'consumer_goods', '$12M', '$9M', '42', '55', '160', '12', 'Packaging waste, labour supply chains'],
         ['Agriculture', '🌾', 'consumer_goods', '$9M', '$6.5M', '55', '90', '280', '15', 'Extreme water dependency, biodiversity'],
         ['Technology', '🧠', 'software', '$15M', '$9M', '15', '10', '40', '28', 'AI/ML, data centre energy, brain-drain']])
    
    doc.add_heading('10C.4 Blindspot Flag Mapping', level=2)
    doc.add_paragraph('Each vertical has its own blindspot flag equivalent to electronics_blindspot:')
    add_styled_table(doc, ['Vertical', 'Blindspot Flag', 'R4 Narrative Adaptation'],
        [['Oil & Gas', 'refinery_blindspot', 'Refinery safety incident / pipeline leak exposé'],
         ['Banking & FS', 'governance_blindspot', 'Financed emissions scandal / greenwashing fund'],
         ['Retail/FMCG', 'supply_chain_blindspot', 'Labour exploitation in garment supply chain'],
         ['Agriculture', 'land_use_blindspot', 'Deforestation-linked commodity sourcing exposé'],
         ['Technology', 'data_centre_blindspot', 'Data centre energy consumption / AI bias overlap']])
    
    doc.add_heading('10C.5 Market Overlap Matrix', level=2)
    doc.add_paragraph('When substituting verticals, cross-BU synergy effects change based on market overlap:')
    add_styled_table(doc, ['Pair', 'Overlap', 'Synergy Implication'],
        [['Banking × Technology', '0.55', 'Fintech convergence — high synergy potential'],
         ['Retail × Agriculture', '0.50', 'Food supply chain vertical integration'],
         ['Technology × Software', '0.75', 'Direct substitution — very high synergy'],
         ['Oil & Gas × Agriculture', '0.30', 'Energy inputs / fertiliser feedstock'],
         ['Banking × Software', '0.50', 'Enterprise SaaS overlap']])
    
    doc.add_heading('10C.6 Facilitation Guidance', level=2)
    add_bullet_list(doc, [
        'Novice Cohorts: Use default 4-BU lineup. The narrative is optimised for the default composition.',
        'Energy Sector MBA: Swap Pharma → Oil & Gas. The extreme carbon intensity (95) creates dramatic tension in R3/R7/R10.',
        'Finance Cohort: Swap Software → Banking & FS. Governance risk (30) is highest, making R2 and R5 critical.',
        'Agribusiness: Swap Consumer Goods → Agriculture. Water dependency (90) makes R8 Blue Stress devastating.',
        'Tech Leadership: Swap Software → Technology. Brain-drain risk amplified; R6 AI Bias becomes deeply personal.',
        'Maximum Difficulty: Oil & Gas + Agriculture — extreme carbon and water exposure simultaneously.',
    ], bold_prefix=True)
