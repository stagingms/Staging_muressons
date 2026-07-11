const fs = require('fs');

function replaceInFile(filePath, replacements) {
    if (!fs.existsSync(filePath)) return;
    let content = fs.readFileSync(filePath, 'utf8');
    for (const [oldStr, newStr] of replacements) {
        if (oldStr instanceof RegExp) {
            content = content.replace(oldStr, newStr);
        } else {
            content = content.split(oldStr).join(newStr);
        }
    }
    fs.writeFileSync(filePath, content, 'utf8');
}

// 1. page.js
replaceInFile('frontend/app/page.js', [
    [/const SEED_BUS_SDG = \[[\s\S]*?\];\n\n/g, ''],
    [/const ROUND_TITLES_SDG = \{[\s\S]*?\};\n\n/g, ''],
    [/const CRISES_SDG = \{[\s\S]*?\};\n\n  const CRISES = useMemo\(\(\) => isSDG \? CRISES_SDG : CRISES_ESG, \[isSDG\]\);/g, 'const CRISES = CRISES_ESG;'],
    [
        "const isSDG = _tempBus ? _tempBus.some(b => ['sub_saharan_corridor', 'south_asia_subcontinent', 'southeast_asia_hub', 'northern_transition_zone'].includes(b.bu_id)) : false;",
        ""
    ],
    [
        "const businessUnits = _tempBus || (isSDG ? SEED_BUS_SDG : isHealthcare ? SEED_BUS_HEALTHCARE : SEED_BUS);",
        "const businessUnits = _tempBus || (isHealthcare ? SEED_BUS_HEALTHCARE : SEED_BUS);"
    ],
    [
        "          isSDG={isSDG}\n",
        ""
    ],
    [
        "isSDG={isSDG}",
        ""
    ]
]);

// 2. CreateCohortModal.js
replaceInFile('frontend/app/components/CreateCohortModal.js', [
    ["        un_sdg: 'UN SDG Edition',", ""],
    [
        "                                        background: detectedParadigm === 'un_sdg' ? 'rgba(16,185,129,0.1)' : 'rgba(99,102,241,0.1)',",
        "                                        background: 'rgba(99,102,241,0.1)',"
    ],
    [
        "                                        border: `1px solid ${detectedParadigm === 'un_sdg' ? 'rgba(16,185,129,0.3)' : 'rgba(99,102,241,0.3)'}`,",
        "                                        border: `1px solid rgba(99,102,241,0.3)`,"
    ],
    [
        "                                        color: detectedParadigm === 'un_sdg' ? '#10b981' : '#6366f1',",
        "                                        color: '#6366f1',"
    ],
    [
        "                                        {detectedParadigm === 'un_sdg' ? '🌍' : detectedParadigm === 'healthcare' ? '🏥' : '⚙️'}{' '}",
        "                                        {detectedParadigm === 'healthcare' ? '🏥' : '⚙️'}{' '}"
    ]
]);

// 3. DecisionParadigmConfig.js
replaceInFile('frontend/app/components/DecisionParadigmConfig.js', [
    ["    un_sdg: 'UN SDG Edition',", ""],
    [
        "const label = paradigm === 'legacy_abc' ? 'Narrative Crises' : paradigm === 'healthcare' ? 'Healthcare' : paradigm === 'un_sdg' ? 'UN SDG' : 'Strategic Pillars';",
        "const label = paradigm === 'legacy_abc' ? 'Narrative Crises' : paradigm === 'healthcare' ? 'Healthcare' : 'Strategic Pillars';"
    ],
    [
        "      } else if (paradigm === 'un_sdg') {\n        d.un_sdg = extractOverrides(unSdgOverrides);\n",
        "      \n"
    ],
    [
        "      key: 'un_sdg',",
        "      key: 'DELETED',"
    ]
]);

// Let's just strip out the un_sdg tab completely using regex
replaceInFile('frontend/app/components/DecisionParadigmConfig.js', [
    [/<button[\s\S]*?onClick=\{\(\) => setActiveEditorTab\('un_sdg'\)\}[\s\S]*?UN SDG[\s\S]*?<\/button>/g, ''],
    [new RegExp("\\\\{\\\\!matrixLoading && matrixData && matrixData\\\\.merged_sdg && activeEditorTab === 'un_sdg'[\\\\s\\\\S]*?\\\\{\\\\/\\\\* End UN SDG Tab \\\\*\\\\/\\\\}", "g"), '']
]);

console.log("Frontend un_sdg refs cleaned");
