# Auth-Gated App Testing Playbook (ForHer)

## Step 1: Create Test User & Session
```
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date().toISOString(),
  consent: null,
  settings: { cycle_context: 'unknown', language: 'en', lock_enabled: false, lock_timeout_min: 5, reduced_motion: false }
});
db.user_sessions.insertOne({
  id: 'sess-' + Date.now(),
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString(),
  last_seen: new Date().toISOString(),
  user_agent: 'test'
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API
```
curl -X GET "$API_URL/api/auth/me" -H "Authorization: Bearer YOUR_SESSION_TOKEN"
curl -X GET "$API_URL/api/logs?from=2026-05-01&to=2026-06-30" -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Step 3: Browser Testing
```
await page.context.add_cookies([{
    "name": "session_token", "value": "YOUR_SESSION_TOKEN",
    "domain": "<preview-host>", "path": "/", "httpOnly": true, "secure": true, "sameSite": "None"
}]);
await page.goto("https://<preview-host>/app");
```

## Clean test data
```
mongosh --eval "use('test_database'); db.users.deleteMany({email: /test\.user\./}); db.user_sessions.deleteMany({session_token: /test_session/});"
```

Checklist: user has `user_id`; session `user_id` matches; backend reads cookie first then Bearer; `/api/auth/me` returns user; `/app` loads dashboard (not landing).
