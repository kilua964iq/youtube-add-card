import asyncio
import random
from playwright.async_api import async_playwright

# ═══════════════════════════════
#      إعدادات عامة
# ═══════════════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ═══════════════════════════════
#      تأخير بشري عشوائي
# ═══════════════════════════════

async def human_delay(min_ms=500, max_ms=2000):
    delay = random.randint(min_ms, max_ms)
    await asyncio.sleep(delay / 1000)

async def human_type(page, selector, text):
    """كتابة بشرية بتأخير عشوائي بين كل حرف"""
    element = await page.wait_for_selector(selector, timeout=10000)
    await element.click()
    await human_delay(200, 500)
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))

async def human_click(page, selector):
    """ضغط بشري مع تحريك الماوس"""
    element = await page.wait_for_selector(selector, timeout=10000)
    box = await element.bounding_box()
    if box:
        x = box["x"] + box["width"] / 2 + random.randint(-5, 5)
        y = box["y"] + box["height"] / 2 + random.randint(-5, 5)
        await page.mouse.move(x, y)
        await human_delay(100, 300)
        await page.mouse.click(x, y)
    else:
        await element.click()
    await human_delay(300, 800)

# ═══════════════════════════════
#      إعداد المتصفح
# ═══════════════════════════════

async def create_browser(playwright):
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-gpu",
            "--window-size=1280,800",
            "--start-maximized",
            "--disable-web-security",
            "--allow-running-insecure-content",
        ]
    )

    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=random.choice(USER_AGENTS),
        locale="en-US",
        timezone_id="America/New_York",
        permissions=["geolocation"],
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
    )

    # إخفاء علامات الأتمتة
    await context.add_init_script("""
        // إخفاء webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // إخفاء plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // إخفاء languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // إخفاء chrome
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // إخفاء permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // إخفاء automation
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    """)

    return browser, context

# ═══════════════════════════════
#      تسجيل الدخول
# ═══════════════════════════════

async def google_login(page, email, password):
    try:
        await page.goto(
            "https://accounts.google.com/signin/v2/identifier",
            wait_until="networkidle",
            timeout=30000
        )
        await human_delay(1000, 2000)

        # إدخال الإيميل
        await human_type(page, 'input[type="email"]', email)
        await human_delay(500, 1000)
        await page.keyboard.press("Enter")
        await human_delay(2000, 3000)

        # التحقق من OTP بعد الإيميل
        if await check_otp(page):
            return "otp"

        # التحقق من الحساب غير موجود
        if await check_selector(page, '[data-error="noAccount"]'):
            return "no_account"

        # إدخال الباسورد
        await human_type(page, 'input[type="password"]', password)
        await human_delay(500, 1000)
        await page.keyboard.press("Enter")
        await human_delay(3000, 4000)

        # التحقق من النتيجة
        current_url = page.url

        if await check_otp(page):
            return "otp"

        if await check_selector(page, '[data-error="wrongpassword"]'):
            return "wrong_password"

        if await check_selector(page, 'text="couldn\'t sign you in"'):
            return "blocked"

        if await check_selector(page, 'text="account has been disabled"'):
            return "disabled"

        if "myaccount.google.com" in current_url or \
           "google.com" in current_url and "signin" not in current_url:
            return "success"

        # محاولة إضافية للتحقق
        await human_delay(2000, 3000)
        current_url = page.url
        if "accounts.google.com" not in current_url:
            return "success"

        return "success"

    except Exception as e:
        return f"error:{str(e)}"

# ═══════════════════════════════
#      إضافة البطاقة
# ═══════════════════════════════

async def add_card_to_google(page, card):
    try:
        # الذهاب لصفحة Google Pay
        await page.goto(
            "https://pay.google.com/gp/w/u/0/home/paymentmethods",
            wait_until="networkidle",
            timeout=30000
        )
        await human_delay(2000, 3000)

        # التحقق من تحميل الصفحة
        current_url = page.url
        if "accounts.google.com" in current_url:
            return "session_expired"

        if await check_otp(page):
            return "otp"

        # البحث عن زر إضافة بطاقة
        add_button_selectors = [
            'button[data-action="add"]',
            'button:has-text("Add card")',
            'button:has-text("Add a card")',
            'button:has-text("Add payment method")',
            '[aria-label="Add card"]',
            '[aria-label="Add a card"]',
            'c-wiz button:first-of-type',
        ]

        add_button = None
        for selector in add_button_selectors:
            try:
                add_button = await page.wait_for_selector(selector, timeout=5000)
                if add_button:
                    break
            except:
                continue

        if not add_button:
            return "no_add_button"

        await human_click(page, add_button if isinstance(add_button, str) else None)
        if not isinstance(add_button, str):
            await add_button.click()
        await human_delay(2000, 3000)

        # ملء بيانات البطاقة
        fill_result = await fill_card_details(page, card)
        if fill_result != "success":
            return fill_result

        # حفظ البطاقة
        save_result = await save_card(page)
        if save_result != "success":
            return save_result

        # التحقق من النتيجة
        await human_delay(3000, 4000)
        return await check_card_added(page, card["number"])

    except Exception as e:
        return f"error:{str(e)}"

# ═══════════════════════════════
#      ملء بيانات البطاقة
# ═══════════════════════════════

async def fill_card_details(page, card):
    number = card["number"]
    month = card["month"]
    year = card["year"]
    cvv = card["cvv"]

    try:
        # محاولة مع iframe
        try:
            await page.wait_for_selector("iframe", timeout=5000)
            frames = page.frames

            for frame in frames:
                try:
                    card_input = await frame.wait_for_selector(
                        'input[autocomplete="cc-number"], input[name="cardnumber"]',
                        timeout=3000
                    )
                    if card_input:
                        await card_input.fill(number)
                        await human_delay(500, 1000)

                        exp_input = await frame.wait_for_selector(
                            'input[autocomplete="cc-exp"], input[name="exp-date"]',
                            timeout=3000
                        )
                        await exp_input.fill(f"{month}/{year}")
                        await human_delay(500, 1000)

                        cvv_input = await frame.wait_for_selector(
                            'input[autocomplete="cc-csc"], input[name="cvc"]',
                            timeout=3000
                        )
                        await cvv_input.fill(cvv)
                        await human_delay(500, 1000)

                        return "success"
                except:
                    continue
        except:
            pass

        # محاولة بدون iframe
        selectors_map = {
            "number": [
                'input[autocomplete="cc-number"]',
                'input[name="cardnumber"]',
                'input[id*="card"]',
            ],
            "expiry": [
                'input[autocomplete="cc-exp"]',
                'input[name="exp-date"]',
                'input[id*="expiry"]',
                'input[id*="exp"]',
            ],
            "cvv": [
                'input[autocomplete="cc-csc"]',
                'input[name="cvc"]',
                'input[id*="cvv"]',
                'input[id*="cvc"]',
            ]
        }

        # رقم البطاقة
        for sel in selectors_map["number"]:
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el:
                    await el.fill(number)
                    await human_delay(500, 1000)
                    break
            except:
                continue

        # تاريخ الانتهاء
        for sel in selectors_map["expiry"]:
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el:
                    await el.fill(f"{month}/{year}")
                    await human_delay(500, 1000)
                    break
            except:
                continue

        # CVV
        for sel in selectors_map["cvv"]:
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el:
                    await el.fill(cvv)
                    await human_delay(500, 1000)
                    break
            except:
                continue

        return "success"

    except Exception as e:
        return f"fill_error:{str(e)}"

# ═══════════════════════════════
#      حفظ البطاقة
# ═══════════════════════════════

async def save_card(page):
    save_selectors = [
        'button:has-text("Save")',
        'button:has-text("Add")',
        'button:has-text("Submit")',
        'button[type="submit"]',
        '[aria-label="Save"]',
    ]
    for selector in save_selectors:
        try:
            btn = await page.wait_for_selector(selector, timeout=3000)
            if btn:
                await btn.click()
                await human_delay(1000, 2000)
                return "success"
        except:
            continue
    return "no_save_button"

# ═══════════════════════════════
#      التحقق من إضافة البطاقة
# ═══════════════════════════════

async def check_card_added(page, card_number):
    last4 = card_number[-4:]
    try:
        # نجاح
        success_checks = [
            f'text="{last4}"',
            'text="Card added"',
            'text="Payment method added"',
        ]
        for sel in success_checks:
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el:
                    return "success"
            except:
                continue

        # بطاقة مرفوضة
        if await check_selector(page, 'text="declined"') or \
           await check_selector(page, 'text="invalid"'):
            return "declined"

        # بطاقة منتهية
        if await check_selector(page, 'text="expired"'):
            return "expired"

        # موجودة مسبقاً
        if await check_selector(page, 'text="already"'):
            return "already_exists"

        # OTP
        if await check_otp(page):
            return "otp"

        return "success"

    except:
        return "success"

# ═══════════════════════════════
#      دوال مساعدة
# ═══════════════════════════════

async def check_otp(page):
    otp_selectors = [
        'input[type="tel"]',
        'input[autocomplete="one-time-code"]',
        'text="2-Step Verification"',
        'text="Verify it\'s you"',
        'text="Check your phone"',
        'text="Enter the code"',
    ]
    for sel in otp_selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=1000)
            if el:
                return True
        except:
            continue
    return False

async def check_selector(page, selector):
    try:
        el = await page.wait_for_selector(selector, timeout=1000)
        return el is not None
    except:
        return False

# ═══════════════════════════════
#      الدالة الرئيسية
# ═══════════════════════════════

async def link_card(account: dict, card: dict) -> str:
    email = account["email"]
    password = account["password"]
    masked = f"****{card['number'][-4:]}"

    async with async_playwright() as p:
        browser = None
        try:
            browser, context = await create_browser(p)
            page = await context.new_page()

            # تسجيل الدخول
            login_result = await google_login(page, email, password)

            if login_result == "otp":
                await browser.close()
                return (
                    f"⚠️ *يحتاج تحقق OTP*\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif login_result == "wrong_password":
                await browser.close()
                return (
                    f"❌ *باسورد غلط*\n"
                    f"👤 `{email}`"
                )
            elif login_result == "no_account":
                await browser.close()
                return (
                    f"❌ *الحساب غير موجود*\n"
                    f"👤 `{email}`"
                )
            elif login_result == "blocked":
                await browser.close()
                return (
                    f"🚫 *الحساب محظور*\n"
                    f"👤 `{email}`"
                )
            elif login_result == "disabled":
                await browser.close()
                return (
                    f"🚫 *الحساب معطل*\n"
                    f"👤 `{email}`"
                )
            elif login_result.startswith("error:"):
                await browser.close()
                return (
                    f"❌ *خطأ في تسجيل الدخول*\n"
                    f"👤 `{email}`\n"
                    f"⚠️ `{login_result}`"
                )

            # إضافة البطاقة
            card_result = await add_card_to_google(page, card)
            await browser.close()

            if card_result == "success":
                return (
                    f"✅ *تم الربط بنجاح!*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif card_result == "otp":
                return (
                    f"⚠️ *البطاقة تحتاج تحقق OTP*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif card_result == "declined":
                return (
                    f"❌ *البطاقة مرفوضة من البنك*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif card_result == "expired":
                return (
                    f"❌ *البطاقة منتهية الصلاحية*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif card_result == "already_exists":
                return (
                    f"⚠️ *البطاقة مضافة مسبقاً*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif card_result == "session_expired":
                return (
                    f"❌ *انتهت الجلسة*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            elif card_result == "no_add_button":
                return (
                    f"❌ *ما قدرت أوصل لصفحة الدفع*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`"
                )
            else:
                return (
                    f"❌ *فشل الربط*\n\n"
                    f"👤 `{email}`\n"
                    f"💳 `{masked}`\n"
                    f"⚠️ `{card_result}`"
                )

        except Exception as e:
            if browser:
                await browser.close()
            return (
                f"❌ *خطأ غير متوقع*\n\n"
                f"👤 `{email}`\n"
                f"💳 `{masked}`\n"
                f"⚠️ `{str(e)}`"
            )
