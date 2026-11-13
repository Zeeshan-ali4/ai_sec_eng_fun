const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../../static/proposal2/investigation.js'), 'utf8');
const guide = vm.runInNewContext(script + '\ninvestigationGuide');
for (let i = 1; i <= 7; i++) {
  const id = `DP-${String(i).padStart(3, '0')}`;
  test(`${id} has incident, objective and three distinct progressive hints`, () => {
    assert.ok(guide[id].incident.length > 40);
    assert.ok(guide[id].objective.length > 70);
    assert.equal(guide[id].hints.length, 3);
    assert.equal(new Set(guide[id].hints).size, 3);
  });
}
test('controlled values and distinct-source limitations become discoverable', () => {
  assert.match(guide['DP-004'].hints[2], /starlight mode/);
  assert.doesNotMatch(guide['DP-004'].incident + guide['DP-004'].objective + guide['DP-004'].hints.slice(0, 2).join(' '), /starlight mode/);
  assert.match(guide['DP-003'].hints[2], /distinct source/);
  assert.match(guide['DP-005'].hints[2], /same source/);
  assert.match(guide['DP-006'].hints[2], /LK-005/);
});
