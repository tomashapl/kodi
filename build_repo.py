#!/usr/bin/env python3
"""Build Kodi addon repository.

Scans for addon directories, generates addons.xml + addons.xml.md5,
and creates ZIP archives. Output goes to `repo/` directory ready for
deployment to GitHub Pages.
"""

import hashlib
import os
import shutil
import xml.etree.ElementTree as ET
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'repo')

# Addon directories to include (must contain addon.xml)
ADDON_DIRS = [
    'repository.tomashapl',
    'service.sc.cachewarmup',
    'plugin.video.streambox',
]


def read_addon_xml(addon_dir):
    """Read and return the addon.xml content and parsed addon id/version."""
    path = os.path.join(SCRIPT_DIR, addon_dir, 'addon.xml')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    root = ET.fromstring(content)
    addon_id = root.attrib['id']
    version = root.attrib['version']
    return addon_id, version, content


def build_zip(addon_dir, addon_id, version):
    """Create a ZIP archive for the addon."""
    zip_name = f'{addon_id}-{version}.zip'
    zip_path = os.path.join(OUTPUT_DIR, addon_id, zip_name)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    src_dir = os.path.join(SCRIPT_DIR, addon_dir)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            # Skip __pycache__ and hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]
            for filename in files:
                if filename.startswith('.'):
                    continue
                filepath = os.path.join(root, filename)
                arcname = os.path.join(addon_id, os.path.relpath(filepath, src_dir))
                zf.write(filepath, arcname)

    print(f'  ZIP: {addon_id}/{zip_name}')
    return zip_path


def generate_addons_xml(addon_xmls):
    """Generate combined addons.xml from individual addon.xml contents."""
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>']
    for xml_content in addon_xmls:
        # Strip XML declaration if present
        content = xml_content.strip()
        if content.startswith('<?xml'):
            content = content.split('?>', 1)[1].strip()
        parts.append(content)
    parts.append('</addons>')
    return '\n'.join(parts)


def generate_md5(content):
    """Generate MD5 checksum of content."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def main():
    print('Building Kodi addon repository...\n')

    # Clean output dir
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    addon_xmls = []
    for addon_dir in ADDON_DIRS:
        addon_path = os.path.join(SCRIPT_DIR, addon_dir, 'addon.xml')
        if not os.path.exists(addon_path):
            print(f'  SKIP: {addon_dir} (no addon.xml)')
            continue

        addon_id, version, xml_content = read_addon_xml(addon_dir)
        print(f'  Found: {addon_id} v{version}')
        addon_xmls.append(xml_content)
        build_zip(addon_dir, addon_id, version)

    # Generate addons.xml
    addons_xml = generate_addons_xml(addon_xmls)
    addons_xml_path = os.path.join(OUTPUT_DIR, 'addons.xml')
    with open(addons_xml_path, 'w', encoding='utf-8') as f:
        f.write(addons_xml)
    print(f'\n  addons.xml generated')

    # Generate addons.xml.md5
    md5 = generate_md5(addons_xml)
    md5_path = os.path.join(OUTPUT_DIR, 'addons.xml.md5')
    with open(md5_path, 'w', encoding='utf-8') as f:
        f.write(md5)
    print(f'  addons.xml.md5: {md5}')

    print(f'\nDone! Output in: {OUTPUT_DIR}/')


if __name__ == '__main__':
    main()
