# Telephony / VoIP — office IP-PBX (Asterisk + FreePBX)

Reproducible config for the **Telephony** portfolio case: a small-office IP-PBX
on **Asterisk 21 + FreePBX 17**, in Docker, demonstrating inbound routing, an
IVR, a call queue, call recording, business-hours time conditions and internal
extensions for remote staff.

This is a **throwaway demo stand**. It is brought up only to configure the
scenario and capture proof (screenshots + a real test call → CDR + recording),
then torn down. A publicly-closed SIP service gives a site visitor nothing live,
and a running PBX is needless attack surface — these configs make the whole thing
reproducible from scratch instead.

## Security model (the important part)

> An Asterisk/SIP service exposed to the public internet draws toll-fraud and
> brute-force registration bots within **hours** — a direct financial risk.

So on this stand:

- **SIP (5060) and RTP are never published to the host.** The `freepbx` service
  has no `ports:` mapping for SIP/RTP — they listen only inside the internal
  Docker network (`172.30.0.0/16`). No host firewall rules are added or needed.
- **The web admin is bound to loopback only** — `127.0.0.1:8088` — never
  `0.0.0.0`. It is unreachable from the internet; screenshots are taken locally.
- Secrets (DB passwords, the FreePBX admin login) live in gitignored files
  (`*.txt`) and are **not** in this repo. Exported Asterisk auth is redacted.

In a real client deployment the SIP **trunk** dials out to the client's chosen
provider; endpoints still listen on a private interface / VPN, not the open net.

## Layout

```
docker-compose.yaml         FreePBX + MariaDB; web on 127.0.0.1:8088 only, no SIP/RTP published
my.cnf, init.sql            MariaDB bootstrap (asterisk + asteriskcdrdb databases)
scripts/configure.php       Builds the whole scenario via the FreePBX API (idempotent):
                              4 extensions, IVR, Support queue, recording, time condition
asterisk/
  extensions_custom.conf    Hand-written demo dialplan: auto-answer agent + a simulated
                              external caller, so the local proof-call self-completes
  generated/                Sanitized snapshots of the FreePBX-generated Asterisk config:
    pjsip.endpoint.conf       PJSIP endpoints 101-104
    pjsip.aor.conf            PJSIP AORs
    pjsip.auth.conf           PJSIP auth — passwords REDACTED
    queues_additional.conf    Support queue 2001
    dialplan-office.conf      IVR (ivr-2), time conditions, queue entry contexts
```

## The office scenario

| Object | Value |
|---|---|
| Extensions | 101 Reception · 102 Sales · 103 Support · 104 Manager (PJSIP) |
| IVR "Main Menu" | press **1 → Sales** (102) · press **2 → Support queue** (2001) |
| Queue 2001 "Support" | ringall · members 103/104 · **recording forced on** |
| Time Condition | Mon–Fri 09:00–18:00 → IVR · otherwise → closed (hangup) |

## Reproduce

```bash
# 1) secrets (NOT committed)
printf "%s" "$(openssl rand -hex 16)" > mysql_root_password.txt
printf "%s" "$(openssl rand -hex 16)" > freepbxuser_password.txt
printf "[smtp.example.com]:587 noreply@example.com:unused" > sasl_passwd.txt
chmod 600 *.txt

# 2) bring up (web reachable only at http://127.0.0.1:8088)
docker compose -p telephony up -d

# 3) install FreePBX into the container
docker compose -p telephony exec -w /usr/local/src/freepbx freepbx \
  php install -n --dbuser=freepbxuser --dbpass="$(cat freepbxuser_password.txt)" --dbhost=db

# 4) (FreePBX 17 mirror may 503 — the office modules ivr/queues/timeconditions/recordings
#     can be fetched from github.com/FreePBX/<module> @ release/17.0 and installed with
#     `fwconsole ma -f install <module>`)

# 5) build the office scenario
docker cp scripts/configure.php telephony-freepbx-1:/tmp/ && \
docker compose -p telephony exec freepbx php /tmp/configure.php && \
docker compose -p telephony exec freepbx fwconsole reload

# 6) generate a real local test call (no handset needed): caller -> IVR(2) -> queue -> agent
docker compose -p telephony exec freepbx \
  asterisk -rx 'channel originate Local/s@demo-inbound application Wait 120'
#    -> produces a genuine CDR row (asteriskcdrdb) + a recording .wav under
#       /var/spool/asterisk/monitor/
```
