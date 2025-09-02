# src/main.py
# tests/test_daily_submit.py က `from src.main import app` လို့ခေါ်တာကြောင့်
# root/main.py က app ကို re-export လုပ်ပေးထားပါတယ်
from main import app  # type: ignore
