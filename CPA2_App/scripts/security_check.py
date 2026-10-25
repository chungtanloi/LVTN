"""Check direct AND resolved Python dependencies against OSV, without printing secrets."""
import importlib.metadata
import json
import sys
import urllib.request

packages = sorted((dist.metadata['Name'], dist.version) for dist in importlib.metadata.distributions() if dist.metadata['Name'].lower() not in ('pip', 'setuptools'))
request = urllib.request.Request('https://api.osv.dev/v1/querybatch', data=json.dumps({'queries': [{'package': {'name': name, 'ecosystem': 'PyPI'}, 'version': version} for name, version in packages]}).encode(), headers={'Content-Type': 'application/json'})
result = json.load(urllib.request.urlopen(request, timeout=30))
findings = []
for (name, version), item in zip(packages, result['results']):
    if item.get('vulns'):
        findings.append(name)
        print(f'FAIL {name}=={version}: ' + ', '.join(vuln['id'] for vuln in item['vulns']))
print(f'OSV: {len(packages)} resolved packages checked, {len(findings)} with advisories.')
sys.exit(bool(findings))
