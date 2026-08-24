const fs = require("fs");
const path = require("path");

// Raw list from satya.min.js – these are the 109 rules the engine exposes.
const RAW_RULES = [
  "Image-Missing Alt",
  "Button-Accessible name",
  "HTML-Missing lang",
  "Forms-Missing label",
  "Link-Accessible name",
  "Frame- Accessible name",
  "Document-Missing title",
  "Heading-Hierarchical order",
  "Viewport- disabled scaling/ zooming",
  "Video-Missing caption",
  "HTML-Required H1",
  "Image-Required non-empty alt",
  "Duplicate-ID",
  "Heading-Required text",
  "Area-Missing alt",
  "InputImage-Missing alt",
  "Object-Missing alt",
  "SVG-Accessible name",
  "Media-Missing audio description",
  "Media-Autoplay",
  "LinkTarget-Missing security/ performance",
  "Accesskey-Required unique",
  "Aria-Hidden body",
  "Blink-Depricated",
  "marquee-Depricated",
  "Meta-Refresh delay",
  "Audio-Missing caption",
  "Focus-Order meaningful",
  "DL-Missing DL",
  "ListItem-Correct semantics",
  "DefinitionList-CorrectSemantics",
  "Select-Accessible name",
  "SkipLink-Required",
  "RoleImg-Accessible name",
  "Para-Correct semantics",
  "HTML-Valid lang",
  "HTML-Consistent lang",
  "Image alt-Required unique text",
  "InputButton-Accessible name",
  "TabIndex-Required positive",
  "Scope-Correct semantics",
  "Aria-Valid specs",
  "AriaInput-Correct semantics",
  "HiddenContent-Non focusable",
  "Table-Correct headers",
  "aria-allowed-attr",
  "aria-required-attr",
  "aria-roles",
  "aria-valid-attr-value",
  "landmark-one-main",
  "landmark-unique",
  "landmark-no-duplicate-banner",
  "landmark-no-duplicate-contentinfo",
  "aria-required-children",
  "aria-required-parent",
  "bypass",
  "css-orientation-lock",
  "aria-command-name",
  "aria-meter-name",
  "aria-progressbar-name",
  "aria-tooltip-name",
  "aria-treeitem-name",
  "server-side-image-map",
  "th-has-data-cells",
  "region",
  "nested-interactive",
  "scrollable-region-focusable",
  "link-in-text-block",
  "table-duplicate-name",
  "form-field-multiple-labels",
  "identical-links-same-purpose",
  "landmark-complementary-is-top-level",
  "label-title-only",
  "presentation-role-conflict",
  "aria-hidden-focus",
  "label-content-name-mismatch",
  "aria-text",
  "duplicate-id-aria",
  "avoid-inline-spacing",
  "landmark-main-is-top-level",
  "aria-roledescription",
  "target-size",
  "aria-allowed-role",
  "aria-dialog-name",
  "aria-toggle-field-name",
  "empty-table-header",
  "frame-focusable-content",
  "landmark-banner-is-top-level",
  "landmark-contentinfo-is-top-level",
  "table-fake-caption",
  "duplicate-id-active",
  "list",
  "frame-title-unique",
  "video-description",
  "radiogroup",
  "avoid-autofocus",
  "svg-img-alt",
  "aria-deprecated-role",
  "color-contrast",
  "interactive-supports-focus",
  "aria-keyshortcuts",
  "no-autoplay-audio",
  "link-ambiguous-text",
  "aria-braille-label",
  "aria-braille-roledescription",
  "aria-redundant-attribute",
  "text-spacing",
  "aria-prohibited-attr",
];

/**
 * Normalise a raw display name into the lowercase-kebab-case rule ID
 * used by the engine (e.g. "Button-Accessible name" → "button-accessible-name").
 */
function toRuleId(raw) {
  let id = raw.trim();
  // Trim leading block-name prefix that already has a trailing space,
  // e.g. "Frame- Accessible name" → "Accessible name"
  id = id.replace(/^[A-Z][a-z]+-\s*/, "");
  id = id.toLowerCase();
  // Replace any remaining spaces with hyphens
  id = id.replace(/\s+/g, "-");
  // Collapse double hyphens that may appear after space-replacement
  id = id.replace(/-{2,}/g, "-");
  return id;
}

const unique = [...new Set(RAW_RULES.map(toRuleId))].sort();
console.log("Normalised unique rule IDs:", unique.length);
console.log("---");
unique.forEach((r) => console.log('  "' + r + '",'));
console.log("\n// Array for direct copy-paste:");
console.log("const ALL_AVAILABLE_RULES = [");
unique.forEach((r) => console.log('  "' + r + '",'));
console.log("];");
