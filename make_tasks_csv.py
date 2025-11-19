# make_tasks_csv.py
import csv, datetime

rows = []

def add(code,name,category,value,time,ai,gate,desc,prompt,thr,bonus):
    rows.append({
        "code":code,"name":name,"category":category,"display_value_usd":value,
        "expected_time_sec":time,"ai_required":ai,"prereq_gate":gate,
        "languages":"auto","description":desc,"user_prompt":prompt,
        "quality_rubric":"A=high;B=ok;C=poor","bonus_eligible":bonus,
        "review_threshold":thr,"is_active":True,"notes":""
    })

# TEXT (20)
for code,name in [
("text_note","Write a short note"),
("text_translate_simple","Translate a simple sentence"),
("text_fix_grammar","Fix grammar of a sentence"),
("text_sentiment_label","Label sentiment of a message"),
("text_intent_label","Label the intent of a chat"),
("text_paraphrase","Paraphrase a sentence"),
("text_summarize","Summarize 3–5 lines"),
("text_tag_topic","Tag the topic of a paragraph"),
("text_keyphrase","Extract 3 key phrases"),
("text_recipe_tip","Share a cooking tip"),
("text_health_tip","Share a health tip"),
("text_safety_tip","Share a local safety tip"),
("text_market_price","Report a local price (item)"),
("text_weather_report","Describe today’s weather"),
("text_event_notice","Announce a local event"),
("text_bus_route","Describe common bus route"),
("text_place_description","Describe a public place"),
("text_job_hint","Share a job tip"),
("text_proverb","Share a local proverb"),
("text_story_short","Tell a short story (3 lines)"),
]:
    add(code,name,"text",2.00,20,True,False,
        "Type in any language; AI auto-detects relevance.",
        "Write in your own words; keep it short and clear.",
        0.6,"streak,speed,quality,diversity")

# VOICE (15)
for code,name in [
("voice_answer","Answer a simple question by voice"),
("voice_read_sign","Read any nearby sign aloud"),
("voice_name_objects","Name 3 objects around you"),
("voice_feelings","Say how you feel today"),
("voice_weather","Describe the weather by voice"),
("voice_translate","Speak a translation of a short sentence"),
("voice_count","Count to five in your dialect"),
("voice_teach_phrase","Teach one local phrase"),
("voice_tonguetwister","Say a tongue twister"),
("voice_directions","Explain how to get to a nearby place"),
("voice_market_price","Say today’s price of an item"),
("voice_menu_item","Read a menu item aloud"),
("voice_colors","Name the colors you see"),
("voice_memory","Recall a childhood place"),
("voice_opinion","Give an opinion about a photo (generic)"),
]:
    add(code,name,"voice",2.00,20,True,False,
        "Speak naturally; try to be clear.",
        "Hold phone near your mouth and speak in your language.",
        0.6,"streak,speed,quality,diversity")

# TAP (10)
for code,name in [
("tap_vote_emotion","Tap the happier image"),
("tap_ab_choose","Choose A or B (best UX)"),
("tap_relevance","Is this answer relevant?"),
("tap_spam_check","Is this spam?"),
("tap_quality_grade","Grade this answer A/B/C"),
("tap_prefer_lang","Which language is clearer?"),
("tap_sound_quality","Is this sound clear?"),
("tap_image_ok","Is this photo usable?"),
("tap_topic_match","Does text match topic?"),
("tap_next_best","Pick the next best task type for you"),
]:
    add(code,name,"tap",2.00,5,False,False,
        "Quick choice to help AI learn quality.",
        "Tap the best option shown on screen.",
        0.5,"streak,speed")

# IMAGE (18)
for code,name in [
("img_desc","Describe what’s in a photo"),
("img_objects_circle","Point at 2 objects (auto-detect)"),
("img_selfie_expression","Smile or blink (liveness)"),
("img_receipt_scan","Scan a small receipt"),
("img_poster_scan","Scan a poster or QR"),
("img_food_plate","Take a photo of a meal"),
("img_public_place","Take a photo of a public place sign"),
("img_book_page","Take a photo of a book/page"),
("img_menu_board","Photo of a menu board"),
("img_water_source","Photo of water source"),
("img_street_name","Photo of street name sign"),
("img_bus_stop","Photo of bus stop sign"),
("img_price_tag","Photo of price tag"),
("img_product_front","Photo of product front label"),
("img_storefront","Photo of storefront"),
("img_id_like","Photo of an object you like"),
("img_local_art","Photo of local art/craft"),
("img_tool_item","Photo of a tool you use"),
]:
    add(code,name,"img",3.00,25,True,True,
        "Capture a clear image; avoid faces unless asked.",
        "Hold steady for 1–2 seconds; ensure readable text if present.",
        0.7,"streak,speed,quality")

# GEO (10)
for code,name in [
("geo_ping","Check-in your location"),
("geo_weather_now","Verify weather matches your area"),
("geo_store_price","Submit price at a nearby store"),
("geo_bus_frequency","How often buses pass here?"),
("geo_noise_level","Is it quiet or noisy here?"),
("geo_safety_view","Is this area safe now?"),
("geo_open_hours","Is this shop open now?"),
("geo_traffic","Is traffic heavy now?"),
("geo_water_quality","Is local water clear?"),
("geo_air_quality","How is the air today?"),
]:
    add(code,name,"geo",3.00,10,True,True,
        "Share approximate location to validate local facts.",
        "Tap 'Ping' then answer the short question shown.",
        0.7,"streak")

# QUIZ (12)
for code,name in [
("quiz_daily","Daily 3-question quiz"),
("quiz_math_easy","Basic math (3Qs)"),
("quiz_language_match","Match word to meaning"),
("quiz_picture_reason","Reason about a simple picture"),
("quiz_safe_or_not","Is this safe?"),
("quiz_true_false","True/False quick round"),
("quiz_sequence","Put steps in order"),
("quiz_map_read","Read a simple map"),
("quiz_time_read","Read a clock/time"),
("quiz_currency_count","Count notes/coins"),
("quiz_signs","Identify common signs"),
("quiz_health","Basic health knowledge"),
]:
    add(code,name,"quiz",3.00,30,True,False,
        "Short adaptive quiz to personalize tasks.",
        "Answer as best as you can; no penalty for mistakes.",
        0.6,"streak,quality")

# TEACH (15)
for code,name in [
("teach_ai_word","Teach a new word in your dialect"),
("teach_ai_phrase","Teach a useful phrase"),
("teach_ai_proverb","Teach a local proverb"),
("teach_ai_count","Teach counting to five"),
("teach_ai_colors","Teach color names in dialect"),
("teach_ai_places","Teach names of places"),
("teach_ai_animals","Teach animal names"),
("teach_ai_foods","Teach food names"),
("teach_ai_verbs","Teach common verbs"),
("teach_ai_numbers","Teach numbers 1–10"),
("teach_ai_greetings","Teach greeting phrases"),
("teach_ai_questions","Teach question words"),
("teach_ai_myth","Tell a local myth (short)"),
("teach_ai_songline","Speak a line from a folk song"),
("teach_ai_spell","Spell a tricky local word"),
]:
    add(code,name,"teach",5.00,45,True,False,
        "Contribute genuine dialect knowledge; duplicates may be reduced.",
        "Speak or type the item and explain meaning and usage.",
        0.8,"streak,quality,teach")

# REF (5)
for code,name in [
("referral_check","Invite a friend + face confirm"),
("referral_device_bind","Bind invitee’s device"),
("referral_language_pair","Confirm invitee language"),
("referral_onboard_help","Help invitee complete first pack"),
("referral_quality_review","Review invitee’s first submissions"),
]:
    add(code,name,"ref",10.00,120,True,True,
        "Grow the community with verified, real users only.",
        "Have your friend scan face and complete onboarding steps.",
        0.9,"streak,quality")

# GATE (5)
for code,name in [
("face_gate","Unlock via face scan"),
("device_check","Device integrity scan"),
("anti_spoof_prompt","Anti-spoof challenge"),
("privacy_ack","Acknowledge privacy policy"),
("tutorial_done","Finish tutorial & safety tips"),
]:
    add(code,name,"gate",0.00,8,True,True,
        "Required step to ensure safety and quality.",
        "Follow on-screen instructions.",
        1.0,"")

# MARKET/ECON (10)
for code,name in [
("market_rice_kg","Price of 1kg rice"),
("market_egg_10","Price of 10 eggs"),
("market_oil_1l","Price of 1L cooking oil"),
("market_flour_1kg","Price of 1kg flour"),
("market_milk_1l","Price of 1L milk"),
("market_bus_fare","Bus fare common route"),
("market_phone_topup","Phone top-up common pack"),
("market_water_1l","Price of 1L bottled water"),
("market_gas_can","Price of household gas can"),
("market_veg_bundle","Price of mixed vegetables bundle"),
]:
    add(code,name,"text",3.00,25,True,False,
        "Report a real local price; AI cross-checks with geo/time.",
        "Type item, brand (if any), and price you see today.",
        0.7,"streak,quality")

# CIVIC (10)
for code,name in [
("civic_clinic_hours","Clinic opening hours"),
("civic_school_hours","School opening hours"),
("civic_water_point","Nearest public water point"),
("civic_trash_spot","Report public trash spot"),
("civic_light_out","Report street light outage"),
("civic_bus_stop_loc","Nearest bus stop location"),
("civic_safe_zone","Report a safe waiting area"),
("civic_help_center","Nearest help center/NGO"),
("civic_event_today","Community event today"),
("civic_feedback_ui","Feedback about app UI"),
]:
    add(code,name,"text",3.00,25,True,False,
        "Share local civic info to help the community and improve maps.",
        "Describe the place, rough location, and what you observed.",
        0.7,"streak,quality,diversity")

out = "dignilife_tasks_120_distinct.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} tasks -> {out}")
