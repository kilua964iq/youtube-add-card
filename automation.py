import asyncio
import random
from playwright.async_api import async_playwright

# ═══════════════════════════════
#      إعدادات عامة
# ═══════════════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ═══════════════════════════════
#      تأخير بشري عشوائي
# ═══════════════════════════════

async def human_delay(min_ms=800, max_ms=2500):
    delay = random.randint(min_ms, max_ms)
    await asyncio.sleep(delay / 1000)

async def human_type(element, text):
    await element.click()
    await human_delay(200, 500)
    await element.fill("")
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))
    await human_delay(200, 400)

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
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--ignore-certificate-errors",
        ]
    )

    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=random.choice(USER_AGENTS),
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    )

    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
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
        # فتح صفحة تسجيل الدخول
        await page.goto(
            "https://accounts.google.com/signin/v2/identifier",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await human_delay(2000, 3000)

        # إدخال الإيميل
        email_input = None
        email_selectors = [
            'input[type="email"]',
            'input[id="identifierId"]',
            '#identifierId',
        ]
        for sel in email_selectors:
            try:
                email_input = await page.wait_for_selector(sel, timeout=15000)
                if email_input:
                    break
            except:
                continue

        if not email_input:
            return "error:email_input_not_found"

        await human_type(email_input, email)
        await human_delay(500, 1000)

        # الضغط على Next
        next_selectors = [
            '#identifierNext',
            'button:has-text("Next")',
            'div[id="identifierNext"]',
        ]
        for sel in next_selectors:
            try:
                btn = await page.wait_for_selector(sel, timeout=5000)
                if btn:
                    await btn.click()
                    break
            except:
                continue

        await human_delay(3000, 5000)

        # التحقق من OTP بعد الإيميل
        if await check_otp(page):
            return "otp"

        # التحقق من الحساب غير موجود
        if await check_selector(page, 'text="Couldn\'t find your Google Account"', 2000):
            return "no_account"
        if await check_selector(page, 'text="Could not find your Google Account"', 2000):
            return "no_account"

        # إدخال الباسورد
        pass_input = None
        pass_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            '#password input',
        ]
        for sel in pass_selectors:
            try:
                pass_input = await page.wait_for_selector(sel, timeout=15000)
                if pass_input:
                    break
            except:
                continue

        if not pass_input:
            return "error:password_input_not_found"

        await human_type(pass_input, password)
        await human_delay(500, 1000)

        # الضغط على Next
        pass_next_selectors = [
            '#passwordNext',
            'button:has-text("Next")',
            'div[id="passwordNext"]',
        ]
        for sel in pass_next_selectors:
            try:
                btn = await page.wait_for_selector(sel, timeout=5000)
                if btn:
                    await btn.click()
                    break
            except:
                continue

        await human_delay(4000, 6000)

        # التحقق من النتيجة
        if await check_otp(page):
            return "otp"

        if await check_selector(page, 'text="Wrong password"', 2000):
            return "wrong_password"
        if await check_selector(page, 'text="wrong password"', 2000):
            return "wrong_password"

        if await check_selector(page, 'text="account has been disabled"', 2000):
            return "disabled"

        if await check_selector(page, 'text="couldn\'t sign you in"', 2000):
            return "blocked"

        # تحقق من النجاح
        current_url = page.url
        if "myaccount.google.com" in current_url:
            return "success"
        if "google.com" in current_url and "accounts" not in current_url:
            return "success"
        if "signin" not in current_url and "google.com" in current_url:
            return "success"

        # انتظار إضافي
        await human_delay(3000, 4000)
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
        await page.goto(
            "https://pay.google.com/gp/w/u/0/home/paymentmethods",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await human_delay(3000, 5000)

        current_url = page.url
        if "accounts.google.com" in current_url:
            return "session_expired"

        if await check_otp(page):
            return "otp"

        # البحث عن زر إضافة
        add_button = None
        add_selectors = [
            'button:has-text("Add card")',
            'button:has-text("Add a card")',
            'button:has-text("Add payment method")',
            '[data-action="add"]',
            '[aria-label="Add card"]',
            '[aria-label="Add a card"]',
        ]
        for sel in add_selectors:
            try:
                add_button = await page.wait_for_selector(sel, timeout=8000)
                if add_button:
                    break
            except:
                continue

        if not add_button:
            return "no_add_button"

        await add_button.click()
        await human_delay(2000, 3000)

        # ملء البطاقة
        fill_result = await fill_card_details(page, card)
        if fill_result != "success":
            return fill_result

        # حفظ
        save_result = await save_card_button(page)
        if save_result != "success":
            return save_result

        await human_delay(3000, 5000)
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
            await page.wait_for_selector("iframe", timeout=8000)
            frames = page.frames

            for frame in frames:
                try:
                    card_input = await frame.wait_for_selector(
                        'input[autocomplete="cc-number"], input[name="cardnumber"]',
                        timeout=5000
                    )
                    if card_input:
                        await human_type(card_input, number)

                        exp_input = await frame.wait_for_selector(
                            'input[autocomplete="cc-exp"], input[name="exp-date"]',
                            timeout=5000
                        )
                        await human_type(exp_input, f"{month}/{year}")

                        cvv_input = await frame.wait_for_selector(
                            'input[autocomplete="cc-csc"], input[name="cvc"]',
                            timeout=5000
                        )
                        await human_type(cvv_input, cvv)

                        return "success"
                except:
                    continue
        except:
            pass

        # بدون iframe
        number_selectors = [
            'input[autocomplete="cc-number"]',
            'input[name="cardnumber"]',
            'input[id*="card-number"]',
            'input[placeholder*="card"]',
        ]
        exp_selectors = [
            'input[autocomplete="cc-exp"]',
            'input[name="exp-date"]',
            'input[id*="expiry"]',
            'input[placeholder*="MM"]',
        ]
        cvv_selectors = [
            'input[autocomplete="cc-csc"]',
            'input[name="cvc"]',
            'input[id*="cvv"]',
            'input[id*="cvc"]',
            'input[placeholder*="CVV"]',
        ]

        for sel in number_selectors:
            try:
                el = await page.wait_for_selector(sel, timeout=5000)
                if el:
                    await human_type(el, number)
                    break
            except:
                continue

        for sel in exp_selectors:
            try:
                el = await page.wait_for_selector(sel, timeout=5000)
                if el:
                    await human_type(el, f"{month}/{year}")
                    break
            except:
                continue

        for sel in cvv_selectors:
            try:
                el = await page.wait_for_selector(sel, timeout=5000)
                if el:
                    await human_type(el, cvv)
                    break
            except:
                continue

        return "success"

    except Exception as e:
        return f"fill_error:{str(e)}"

# ═══════════════════════════════
#      حفظ البطاقة
# ═══════════════════════════════

async def save_card_button(page):
    save_selectors = [
        'button:has-text("Save")',
        'button:has-text("Add")',
        'button:has-text("Submit")',
        'button[type="submit"]',
        '[aria-label="Save"]',
    ]
    for sel in save_selectors:
        try:
            btn = await page.wait_for_selector(sel, timeout=5000)
            if btn:
                await btn.click()
                await human_delay(2000, 3000)
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
        success_checks = [
            f'text="{last4}"',
            'text="Card added"',
            'text="Payment method added"',
            'text="card has been added"',
        ]
        for sel in success_checks:
            try:
                el = await page.wait_for_selector(sel, timeout=5000)
                if el:
                    return "success"
            except:
                continue

        if await check_selector(page, 'text="declined"', 3000):
            return "declined"
        if await check_selector(page, 'text="invalid"', 3000):
            return "declined"
        if await check_selector(page, 'text="expired"', 3000):
            return "expired"
        if await check_selector(page, 'text="already"', 3000):
            return "already_exists"
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
        'text="Get a verification code"',
    ]
    for sel in otp_selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=1000)
            if el:
                return True
        except:
            continue
    return False

async def check_selector(page, selector, timeout=1000):
    try:
        el = await page.wait_for_selector(selector, timeout=timeout)
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
                    f"❌ *البطاقة مرفوضة*\n\n"
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
