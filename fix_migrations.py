import os, glob

for filepath in glob.glob('backend/alembic/versions/*.py'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace("sa.text('(CURRENT_TIMESTAMP)')", "sa.text('CURRENT_TIMESTAMP')")
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
