"""Save console evidence and print only recent test/error context."""
from measure_server_boot import rpc,STUDIO,ROOT
value=rpc('get_console_output',{'studio_id':STUDIO})
if not isinstance(value,str): value=str(value)
(ROOT/'.tools/studio_console_latest.txt').write_text(value,encoding='utf-8')
lines=value.splitlines()
for index,line in enumerate(lines):
    if 'AtmosphereExperiment' in line or 'invariant' in line or 'late update' in line or 'RuntimeError' in line:
        print('\n'.join(lines[max(0,index-3):index+5]))
print('\n'.join(lines[-20:]))
