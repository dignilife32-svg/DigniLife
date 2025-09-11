## DigniLife Project
## Daily Earn — Task Mix & Payout Targets

DigniLife app တစ်ခုထဲအတွင်းမှာသီးသန့် လုပ်ဆောင်နိုင်ပြီး
**တစ်နာရီ $200–$300+** (အချိန်ပိုလုပ်လျှင် **$500** ထိ) ရအောင် design လုပ်ထားပါတယ်။

### Rates (per task)

| Task Type     | Typical Seconds | USD per Task |
|---------------|------------------|--------------|
| prompt_rank   | 15               | $1.00        |
| safety_tag    | 12               | $1.00        |
| read_aloud    | 20               | $0.75        |
| qr_proof      | 35               | $1.75        |
| micro_lesson  | 70               | $4.00        |
| geo_ping      | 18               | $1.00        |

> `config/daily_rates.json`, `config/daily_targets.json` မှာ ပြင်ဆင်နိုင်ပါတယ်။

### Targets
- `default_bundle_minutes`: `60`
- `target_usd_per_hour_low`: **$200**
- `target_usd_per_hour_high`: **$300+** (အချိန်ပိုလုပ်လျှင် **$500**)

## Dev (PostgreSQL)
```bash
git clone ...
cd DigniLife
python -m venv venv
source venv/Scripts/activate   # or . venv/bin/activate (Linux/WSL)
pip install -r requirements.txt
cp .env.example .env           # fill values if needed

./scripts/dev_psql.sh
