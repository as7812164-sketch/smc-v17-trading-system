import os
import shutil

base = 'nexuspro_apk_src'

# 1. Update AndroidManifest.xml
manifest_path = os.path.join(base, 'AndroidManifest.xml')
with open(manifest_path, 'r', encoding='utf-8') as f:
    m_content = f.read()

m_content = m_content.replace('package="com.hermes.trading.terminal"', 'package="com.nexuspro.trading.terminal"')
m_content = m_content.replace('com.hermes.trading.terminal.', 'com.nexuspro.trading.terminal.')

with open(manifest_path, 'w', encoding='utf-8') as f:
    f.write(m_content)
print('Updated AndroidManifest.xml')

# 2. Update strings.xml
strings_path = os.path.join(base, 'res', 'values', 'strings.xml')
with open(strings_path, 'r', encoding='utf-8') as f:
    s_content = f.read()

s_content = s_content.replace('<string name="appName">HERMES 2.5 APEX Trading Terminal</string>', '<string name="appName">NexusPro APEX Trading Terminal</string>')
s_content = s_content.replace('<string name="launcherName">Hermes APEX</string>', '<string name="launcherName">NexusPro</string>')
s_content = s_content.replace('smc-ai-agent.onrender.com', 'nexuspro-terminal.onrender.com')
s_content = s_content.replace('https://smc-ai-agent.onrender.com/?view=mobile', 'https://nexuspro-terminal.onrender.com/trade?view=mobile')
s_content = s_content.replace('com.hermes.trading.terminal.fileprovider', 'com.nexuspro.trading.terminal.fileprovider')

with open(strings_path, 'w', encoding='utf-8') as f:
    f.write(s_content)
print('Updated strings.xml')

# 3. Update smali files and rename directory
old_smali_dir = os.path.join(base, 'smali', 'com', 'hermes', 'trading', 'terminal')
new_smali_dir = os.path.join(base, 'smali', 'com', 'nexuspro', 'trading', 'terminal')

os.makedirs(new_smali_dir, exist_ok=True)

if os.path.exists(old_smali_dir):
    for fname in os.listdir(old_smali_dir):
        old_f = os.path.join(old_smali_dir, fname)
        new_f = os.path.join(new_smali_dir, fname)
        with open(old_f, 'r', encoding='utf-8') as f:
            code = f.read()
        code = code.replace('Lcom/hermes/trading/terminal/', 'Lcom/nexuspro/trading/terminal/')
        with open(new_f, 'w', encoding='utf-8') as f:
            f.write(code)
        os.remove(old_f)
        print(f'Migrated smali: {fname}')

    try:
        os.rmdir(old_smali_dir)
        os.rmdir(os.path.join(base, 'smali', 'com', 'hermes', 'trading'))
        os.rmdir(os.path.join(base, 'smali', 'com', 'hermes'))
        print('Cleaned up old smali directory structure')
    except Exception as e:
        print('Dir cleanup note:', e)

print('Transformation complete!')
