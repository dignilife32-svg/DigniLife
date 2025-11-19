# GO LIVE CHECKLIST — DIGINILIFE

> Target env: **prod**
> Owner: **@Dignilocal | Backup: **@ops**
> Date: ___ / ___ / ___

## 0) Preflight
- [ ] Repo clean (`git status` = clean), version tag planned (e.g. `v1.0.0`).
- [ ] `.env.prod` prepared & stored in secrets manager (no secrets in git).
- [ ] DNS ready (A/AAAA/CNAME) for `api.example.com`, `grafana.example.com`.

## 1) Secrets & Config
- [ ] `DB_URL` (Postgres) valid & reachable
- [ ] `HMAC_SECRET` / `JWT_SECRET` ≥ 32 chars
- [ ] `REDIS_URL` (if ratelimit/idempotency used)
- [ ] Traefik ACME email + contact info set
- [ ] `FACE_PROVIDER_*` creds set (if using external face match)

## 2) Database & Migrations
- [ ] Run: `alembic upgrade head` ✅
- [ ] Seed (optional): `python seed_demo_user.py` ✅
- [ ] Backups: `pg_dump` script + restore test passed

## 3) Build & Containers
- [ ] `docker build -t diginilife-api:$(git rev-parse --short HEAD) .` ok
- [ ] Image scanned (trivy/grype) – no critical vulns
- [ ] Compose files reviewed: `docker-compose.prod.yml`

## 4) Networking & TLS
- [ ] Traefik routes up; HTTP→HTTPS redirect works
- [ ] Valid certs via Let’s Encrypt; HSTS enabled
- [ ] CORS allowlist matches app domains

## 5) App Health (Core Routes)
- [ ] `GET /ai/heartbeat` → 200
- [ ] `POST /echo` → 200
- [ ] Wallet:
  - [ ] `GET /wallet/summary` → 200
  - [ ] `POST /wallet/earn` (test user) → 200, balance ↑
  - [ ] `POST /wallet/withdraw/req` → 200 (reserve ok)
  - [ ] `POST /wallet/withdraw/commit` → 200 (commit ok)
- [ ] Facegate:
  - [ ] `POST /safety/face/verify` → token issued & single-use verified

## 6) Background Jobs
- [ ] Server startup loop running (no crash)
- [ ] Manual tick: `POST /admin/ai_worker/tick` → 200
- [ ] Auto-refill bonus pool recorded in ledger
- [ ] Graceful shutdown cancels background task cleanly

## 7) Observability
- [ ] Prometheus scrape targets UP
- [ ] Grafana: dashboards provisioned (`dashboards/diginilife.json`)
- [ ] Alerts loaded (`ops/alert_rules.yml`) & test fire/resolve works
- [ ] Structured logs to `runtime/logs/` (or log aggregator)

## 8) Limits, Auth, Safety
- [ ] Rate limit (Redis) enabled for public routes
- [ ] AuthSig / API keys enforced where required
- [ ] Idempotency middleware enabled on money-mutating endpoints
- [ ] Facegate replay protection (nonce) verified

## 9) Tests & Smoke
- [ ] `pytest -q` → all green
- [ ] `./scripts/smoke.sh` → green
- [ ] `tests/test_wallet_flow.py` → green

## 10) Performance (quick)
- [ ] p50/p95 latency < target on `/wallet/*`
- [ ] DB connections under pool max; no slow queries flagged
- [ ] CPU/RAM headroom ≥ 30%

## 11) Legal & Content
- [ ] Privacy Policy & ToS linked in UI footer
- [ ] Multilingual policy pages render & correct
- [ ] Cookie banner/consent (if web client) configured

## 12) Rollout Plan
- [ ] Blue/Green or zero-downtime deploy plan written
- [ ] Rollback command documented & tested
- [ ] Comms: release notes + status page update template

---

### Quick Commands

```bash
# migrations
alembic upgrade head

# prod-like up
docker compose -f docker-compose.prod.yml up -d

# health checks (example)
curl -f https://api.example.com/ai/heartbeat
curl -f -X POST https://api.example.com/admin/ai_worker/tick

# tests
pytest -q
./scripts/smoke.sh
