import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = defineConfig([
  ...nextVitals,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // Disable React Compiler rules added in eslint-plugin-react-hooks v7.
  // This project does not use the React Compiler, so these rules produce
  // false positives for common patterns like setLoading before a fetch.
  // Keep rules-of-hooks and exhaustive-deps which are broadly applicable.
  {
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/set-state-in-render": "off",
      "react-hooks/purity": "off",
      "react-hooks/refs": "off",
      "react-hooks/immutability": "off",
      "react-hooks/globals": "off",
      "react-hooks/static-components": "off",
      "react-hooks/use-memo": "off",
      "react-hooks/component-hook-factories": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/incompatible-library": "off",
      "react-hooks/error-boundaries": "off",
      "react-hooks/unsupported-syntax": "off",
      "react-hooks/config": "off",
      "react-hooks/gating": "off",
    },
  },
  // QA-2026-07-16 #12: nudge KPI number formatting toward the single source of
  // truth (app/utils/kpiFormats.js) so the same metric renders identically on
  // the player, facilitator and admin surfaces. Advisory (warn) — existing
  // inline formatting is migrated opportunistically; new code imports kpiFormats.
  {
    files: ["app/components/**/*.{js,jsx}"],
    ignores: ["app/utils/**"],
    rules: {
      "no-restricted-syntax": [
        "warn",
        {
          selector: "CallExpression[callee.property.name='toLocaleString']",
          message:
            "Prefer kpiFormats (app/utils/kpiFormats.js) for KPI/currency formatting so metrics stay consistent across dashboards (QA #12).",
        },
      ],
    },
  },
]);

export default eslintConfig;
