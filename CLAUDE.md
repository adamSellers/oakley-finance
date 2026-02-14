# Oakley Finance

## Deployment

The skill runs on the openclaw device, not locally.

- **Host:** `oakley@bot.oakroad`
- **Skill path:** `/home/oakley/.openclaw/workspace/skills/oakley-finance/`
- **Install method:** `pipx` (not pip)

### Deploy steps

```bash
# 1. Push changes to git
git push

# 2. SSH into openclaw and pull + reinstall
ssh oakley@bot.oakroad
cd /home/oakley/.openclaw/workspace/skills/oakley-finance
git pull
pipx install . --force
```
