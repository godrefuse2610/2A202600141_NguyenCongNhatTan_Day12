# Deployment Information

## Public URL
https://2a202600141nguyencongnhattanday12-production-9dc8.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://2a202600141nguyencongnhattanday12-production-9dc8.up.railway.app/health
# Expected: {"status": "ok", ...}
```

### API Test (with authentication)
```bash
# Thay YOUR_KEY bằng giá trị AGENT_API_KEY trong Railway Variables
curl -X POST https://2a202600141nguyencongnhattanday12-production-9dc8.up.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello, how are you?"}'
```

## Environment Variables Set
- `PORT`: (Managed by Railway)
- `REDIS_URL`: (Managed by Railway Redis Service)
- `AGENT_API_KEY`: (Your secret key)
- `JWT_SECRET`: (Your JWT secret)
- `ENVIRONMENT`: `production`

## Screenshots
Screenshots are located in the `day12/2A202600141_NguyenCongNhatTan_Day12/02-docker/production/` directory or equivalent.
- [Service running](c:/Users/Admin/LAB/day12/2A202600141_NguyenCongNhatTan_Day12/02-docker/production/Screenshot_app.png)
