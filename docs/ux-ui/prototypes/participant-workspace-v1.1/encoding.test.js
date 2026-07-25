"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync(
  "docs/ux-ui/prototypes/participant-workspace-v1.1/TPS360 Participant Wireframes.html",
  "utf8"
);
const text = (...codes) => String.fromCodePoint(...codes);
const mojibake = [
  text(0x0420, 0x0405),
  text(0x0420, 0x00b5),
  text(0x0421, 0x0458),
  text(0x0420, 0x00a0)
];
const ukrainian = [
  text(0x0412, 0x0445, 0x0456, 0x0434),
  text(0x0423, 0x0447, 0x0430, 0x0441, 0x043d, 0x0438, 0x043a)
];

test("participant workspace is UTF-8 and contains readable Ukrainian text", () => {
  assert.match(html, /<meta charset="UTF-8">/);
  for (const marker of mojibake) assert.equal(html.includes(marker), false);
  for (const phrase of ukrainian) assert.equal(html.includes(phrase), true);
});
