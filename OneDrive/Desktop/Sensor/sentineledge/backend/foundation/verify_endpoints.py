"""Quick verification of key live endpoints."""
import urllib.request, json, sys

BASE = 'http://localhost:5000'

def get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, json.loads(r.read())

def post(url, data, headers=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method='POST')
    req.add_header('Content-Type', 'application/json')
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def check(name, cond):
    print(f'  {"PASS" if cond else "FAIL"} -- {name}')
    return cond

results = []

# TEST 01 - Health
print('TEST 01 - Health Check')
code, h = get(BASE + '/api/health')
r = check('status 200', code == 200)
r &= check('has status key', 'status' in h)
r &= check('has environment', 'environment' in h)
r &= check('has uptime', 'uptime' in h)
r &= check('has timestamp', 'timestamp' in h)
r &= check('has modules', 'modules' in h)
r &= check('has connected_clients', 'connected_clients' in h)
r &= check('has alerts_today', 'alerts_today' in h)
r &= check('has last_reading key', 'last_reading' in h)
r &= check('database=ok', h.get('modules', {}).get('database') == 'ok')
r &= check('sensor=ok', h.get('modules', {}).get('sensor') == 'ok')
results.append(('01 Health', r))

# TEST 02 - Recent readings
print('TEST 02 - Recent Readings')
code, d = get(BASE + '/api/readings/recent')
r = check('status 200', code == 200)
r &= check('is array', isinstance(d, list))
if d:
    r &= check('has temperature', 'temperature' in d[0])
    r &= check('has humidity', 'humidity' in d[0])
    r &= check('has timestamp', 'timestamp' in d[0])
results.append(('02 Readings', r))

# TEST 05 - Thresholds
print('TEST 05 - Thresholds Config')
code, t = get(BASE + '/api/config/thresholds')
r = check('status 200', code == 200)
r &= check('temp unit is degree C', t.get('temperature', {}).get('unit') == '\u00b0C')
r &= check('source is default', t.get('source') == 'default')
r &= check('temp_high=38.0', t.get('temperature', {}).get('high') == 38.0)
r &= check('temp_low=22.0', t.get('temperature', {}).get('low') == 22.0)
r &= check('humidity_high=80.0', t.get('humidity', {}).get('high') == 80.0)
r &= check('humidity_low=35.0', t.get('humidity', {}).get('low') == 35.0)
results.append(('05 Thresholds', r))

# TEST 10 - Auth enforced
print('TEST 10 - Admin Auth Required')
code, d = post(BASE + '/api/subscribers',
    {'name': 'X', 'phone': '+919876543210', 'email': 'x@y.com', 'escalation_order': 3},
    {})
r = check('status 401', code == 401)
results.append(('10 Auth', r))

# TEST 22 - 404
print('TEST 22 - 404 Handler')
try:
    urllib.request.urlopen(BASE + '/api/nonexistent')
    r = check('should have 404', False)
except urllib.error.HTTPError as e:
    d = json.loads(e.read())
    r = check('status 404', e.code == 404)
    r &= check('error=NotFound', d.get('error') == 'NotFound')
    r &= check('has timestamp', 'timestamp' in d)
results.append(('22 404', r))

# TEST 24 - Backup
print('TEST 24 - Backup Endpoint')
code, d = post(BASE + '/api/admin/backup', {}, {'X-Admin-Password': 'admin123'})
r = check('status 200', code == 200)
r &= check('status=success', d.get('status') == 'success')
r &= check('filename ends in .db', str(d.get('filename', '')).endswith('.db'))
r &= check('size_mb > 0', d.get('size_mb', 0) > 0)
results.append(('24 Backup', r))

print()
print('SUMMARY:')
all_pass = True
for name, passed in results:
    print(f'  {"PASS" if passed else "FAIL"} -- {name}')
    if not passed:
        all_pass = False

print()
if all_pass:
    print('All key tests PASSED.')
else:
    print('Some tests FAILED.')
    sys.exit(1)
