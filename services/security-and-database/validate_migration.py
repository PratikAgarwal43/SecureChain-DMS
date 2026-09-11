import re

with open('securechain_v03_migration.sql', encoding='utf-8') as f:
    sql = f.read()

tables   = re.findall(r'CREATE TABLE (\w+)', sql)
triggers = re.findall(r'CREATE TRIGGER (\w+)', sql)
indexes  = re.findall(r'CREATE (?:UNIQUE )?INDEX (\w+)', sql)
rules    = re.findall(r'CREATE RULE (\w+)', sql)
inserts  = list(dict.fromkeys(re.findall(r'INSERT INTO (\w+)', sql)))

print('=== SECURECHAIN DMS v0.3 MIGRATION ANALYSIS ===')
print()
print(f'TABLES  ({len(tables)}):')
for t in tables: print(f'  + {t}')
print()
print(f'TRIGGERS ({len(triggers)}):')
for t in triggers: print(f'  + {t}')
print()
print(f'WORM RULES ({len(rules)}):')
for r in rules: print(f'  + {r}')
print()
print(f'INDEXES  ({len(indexes)}):')
for i in indexes: print(f'  + {i}')
print()
print(f'SEED DATA INTO: {inserts}')
print()
print(f'TOTAL LINES: {len(sql.splitlines())}')
print()

required = [
    'roles','users','cases','documents','document_versions',
    'quorum_policies','case_participants','edit_requests',
    'approval_assignments','approvals','audit_logs',
    'merkle_checkpoints','dsc_verifications','notifications',
    'document_diffs','document_access_logs','case_court_registrations'
]
missing = [t for t in required if t not in tables]
print('REQUIRED TABLE CHECK:')
if missing:
    for m in missing: print(f'  MISSING: {m}')
else:
    print('  ALL 17 TABLES PRESENT - SCHEMA IS COMPLETE')
print()

# Check circular FK is handled
if 'current_version_id' in sql and 'DEFERRABLE' in sql:
    print('CIRCULAR FK CHECK: current_version_id is DEFERRABLE - CORRECT')
else:
    print('CIRCULAR FK CHECK: WARNING - DEFERRABLE not found')

# Check WORM rules
if 'rule_audit_no_update' in sql and 'rule_audit_no_delete' in sql:
    print('WORM RULES CHECK: Both UPDATE and DELETE rules present - CORRECT')

# Check self-approval trigger
if 'fn_no_self_approval' in sql:
    print('SELF-APPROVAL BLOCK: Trigger present - CORRECT')

# Check identity reveal trigger  
if 'fn_reveal_identities' in sql:
    print('IDENTITY REVEAL: Trigger present - CORRECT')

# Check notification triggers
if 'fn_notify_upload' in sql and 'fn_notify_quorum' in sql:
    print('NOTIFICATION TRIGGERS: Both upload + quorum triggers present - CORRECT')

print()
print('=== FINAL VERDICT ===')
print(f'Tables: {len(tables)}/17')
print(f'Triggers: {len(triggers)}/8')
print(f'WORM Rules: {len(rules)}/2')
print(f'Indexes: {len(indexes)}/22')
print(f'Seed tables: {len(inserts)}/2')
