"""Embed private capture-derived initialization without putting it in Git."""
Import('env')
from pathlib import Path
import json
root = Path(env['PROJECT_DIR']).parents[1]
steps = json.loads((root / 'private/activation-profile.json').read_text())
assert len(steps) == 3
out = Path(env.subst('$BUILD_DIR')) / 'private_include'
out.mkdir(parents=True, exist_ok=True)
lines = ['#pragma once', '#include <stddef.h>', '#include <stdint.h>',
         'struct InitStep { const uint8_t* tx; size_t txSize; const uint8_t* rx; size_t rxSize; int mask; };']
for i, step in enumerate(steps):
    for field in ('tx', 'rx'):
        b = bytes.fromhex(step[field])
        assert 0 < len(b) <= 128
        lines.append('static const uint8_t %s%d[] = {%s};' % (field, i, ','.join(str(v) for v in b)))
    assert step['mask'] in ([], [10])
lines.append('static const InitStep initSteps[] = {')
for i, step in enumerate(steps):
    lines.append('{tx%d,sizeof(tx%d),rx%d,sizeof(rx%d),%d},' % (i,i,i,i,10 if step['mask'] else -1))
lines.append('};')
p = out / 'activation_profile.h'
p.write_text('\n'.join(lines))
p.chmod(0o600)
env.Append(CPPPATH=[str(out)])
