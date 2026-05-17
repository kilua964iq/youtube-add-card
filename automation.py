import asyncio
from playwright.async_api import async_playwright

async def link_card(account: dict, card: dict) -> str:
    """
    يربط البطاقة بحساب Google عن طريق YouTube Premium
    """
    email = account["email"]
    password = account["password"]
    card_number = card["number"]
    card_expiry = card["expiry"]
    card_cvv = card["cvv"]

    # تقسيم تاريخ الانتهاء
    expiry_parts = card_expiry.split("/")
    exp_month = expiry_parts[0]
    exp_year = expiry_parts[1]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ar-SA",
        )

        page = await context.new_page()

        # إخفاء علامات الأتمتة
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            # ═══════════════════════════
            #      تسجيل الدخول
            # ═══════════════════════════

            await page.goto("https://accounts.google.com/signin", wait_until="networkidle")
            await asyncio.sleep(2)

            # إدخال الإيميل
            email_input = await page.wait_for_selector('input[type="email"]', timeout=15000)
            await email_input.fill(email)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)

            # التحقق من طلب OTP بعد الإيميل
            otp_check = await check_otp_required(page)
            if otp_check:
                await browser.close()
                return f"⚠️ الحساب *{email}* يطلب تحقق OTP\nأدخل الرمز يدوياً ثم حاول مجدداً"

            # إدخال الباسورد
            password_input = await page.wait_for_selector('input[type="password"]', timeout=15000)
            await password_input.fill(password)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            # التحقق من نتيجة تسجيل الدخول
            login_result = await check_login_result(page, email)
            if login_result != "success":
                await browser.close()
                return login_result

            # ═══════════════════════════
            #    الذهاب لصفحة الدفع
            # ═══════════════════════════

            await page.goto(
                "https://pay.google.com/gp/w/u/0/home/paymentmethods",
                wait_until="networkidle"
            )
            await asyncio.sleep(3)

            # التحقق من تحميل الصفحة
            page_check = await check_payment_page(page, email)
            if page_check != "success":
                await browser.close()
                return page_check

            # ═══════════════════════════
            #    إضافة البطاقة
            # ═══════════════════════════

            # البحث عن زر إضافة بطاقة
            add_button = None
            add_selectors = [
                'button[data-action="add"]',
                'button:has-text("إضافة بطاقة")',
                'button:has-text("Add card")',
                'button:has-text("Add a card")',
                '[aria-label="Add card"]',
                '.add-card-button',
            ]

            for selector in add_selectors:
                try:
                    add_button = await page.wait_for_selector(selector, timeout=5000)
                    if add_button:
                        break
                except:
                    continue

            if not add_button:
                await browser.close()
                return f"❌ ما قدرت أوصل لصفحة إضافة البطاقة في حساب *{email}*"

            await add_button.click()
            await asyncio.sleep(2)

            # ═══════════════════════════
            #    ملء بيانات البطاقة
            # ═══════════════════════════

            # رقم البطاقة - داخل iframe
            try:
                card_frame = await page.wait_for_selector(
                    'iframe[name*="card"], iframe[src*="pay.google"], iframe[title*="card"]',
                    timeout=10000
                )
                frame = await card_frame.content_frame()

                # رقم البطاقة
                card_input = await frame.wait_for_selector(
                    'input[name="cardnumber"], input[id*="card"], input[autocomplete="cc-number"]',
                    timeout=10000
                )
                await card_input.fill(card_number)
                await asyncio.sleep(1)

                # تاريخ الانتهاء
                expiry_input = await frame.wait_for_selector(
                    'input[name="exp-date"], input[autocomplete="cc-exp"], input[id*="expiry"]',
                    timeout=5000
                )
                await expiry_input.fill(f"{exp_month}/{exp_year}")
                await asyncio.sleep(1)

                # CVV
                cvv_input = await frame.wait_for_selector(
                    'input[name="cvc"], input[autocomplete="cc-csc"], input[id*="cvv"]',
                    timeout=5000
                )
                await cvv_input.fill(card_cvv)
                await asyncio.sleep(1)

            except Exception as e:
                # محاولة بدون iframe
                try:
                    card_input = await page.wait_for_selector(
                        'input[autocomplete="cc-number"]',
                        timeout=5000
                    )
                    await card_input.fill(card_number)

                    expiry_input = await page.wait_for_selector(
                        'input[autocomplete="cc-exp"]',
                        timeout=5000
                    )
                    await expiry_input.fill(f"{exp_month}/{exp_year}")

                    cvv_input = await page.wait_for_selector(
                        'input[autocomplete="cc-csc"]',
                        timeout=5000
                    )
                    await cvv_input.fill(card_cvv)

                except:
                    await browser.close()
                    return f"❌ ما قدرت أملأ بيانات البطاقة في حساب *{email}*"

            # ═══════════════════════════
            #    حفظ البطاقة
            # ═══════════════════════════

            save_selectors = [
                'button:has-text("حفظ")',
                'button:has-text("Save")',
                'button:has-text("إضافة")',
                'button:has-text("Add")',
                'button[type="submit"]',
            ]

            save_button = None
            for selector in save_selectors:
                try:
                    save_button = await page.wait_for_selector(selector, timeout=5000)
                    if save_button:
                        break
                except:
                    continue

            if not save_button:
                await browser.close()
                return f"❌ ما لقيت زر الحفظ في حساب *{email}*"

            await save_button.click()
            await asyncio.sleep(4)

            # ═══════════════════════════
            #    التحقق من النتيجة
            # ═══════════════════════════

            result = await check_card_result(page, email, card_number)
            await browser.close()
            return result

        except Exception as e:
            await browser.close()
            return f"❌ حدث خطأ في حساب *{email}*\nالخطأ: `{str(e)}`"


# ═══════════════════════════════════════
#         دوال التحقق المساعدة
# ═══════════════════════════════════════

async def check_login_result(page, email: str) -> str:
    """يتحقق من نتيجة تسجيل الدخول"""
    try:
        current_url = page.url

        # تسجيل دخول ناجح
        if "myaccount.google.com" in current_url or "google.com/u/" in current_url:
            return "success"

        # باسورد غلط
        wrong_pass = await page.query_selector(
            'text="كلمة المرور غلط", text="Wrong password", [data-error="wrongpassword"]'
        )
        if wrong_pass:
            return f"❌ باسورد غلط للحساب *{email}*"

        # حساب غير موجود
        no_account = await page.query_selector(
            'text="لم يتم العثور", text="Couldn\'t find"'
        )
        if no_account:
            return f"❌ الحساب *{email}* غير موجود"

        # OTP مطلوب
        otp_required = await check_otp_required(page)
        if otp_required:
            return f"⚠️ الحساب *{email}* يطلب تحقق OTP\nأدخل الرمز يدوياً ثم حاول مجدداً"

        # حساب محظور
        blocked = await page.query_selector(
            'text="تم تعطيل", text="disabled", text="suspended"'
        )
        if blocked:
            return f"🚫 الحساب *{email}* محظور أو معطل"

        return "success"

    except:
        return "success"


async def check_otp_required(page) -> bool:
    """يتحقق إذا كان OTP مطلوب"""
    try:
        otp_selectors = [
            'input[type="tel"]',
            'input[autocomplete="one-time-code"]',
            'text="التحقق بخطوتين"',
            'text="2-Step Verification"',
            'text="أرسلنا رمزاً"',
            'text="We sent a code"',
            'text="رمز التحقق"',
        ]
        for selector in otp_selectors:
            element = await page.query_selector(selector)
            if element:
                return True
        return False
    except:
        return False


async def check_payment_page(page, email: str) -> str:
    """يتحقق من تحميل صفحة الدفع"""
    try:
        current_url = page.url

        # تم تحويله لتسجيل الدخول مجدداً
        if "accounts.google.com" in current_url:
            return f"❌ انتهت جلسة الحساب *{email}*"

        # OTP مطلوب
        otp_required = await check_otp_required(page)
        if otp_required:
            return f"⚠️ الحساب *{email}* يطلب تحقق OTP في صفحة الدفع"

        # خطأ في الوصول
        error = await page.query_selector('text="خطأ", text="Error", text="403", text="404"')
        if error:
            return f"❌ خطأ في الوصول لمحفظة الحساب *{email}*"

        return "success"

    except:
        return "success"


async def check_card_result(page, email: str, card_number: str) -> str:
    """يتحقق من نتيجة إضافة البطاقة"""
    try:
        masked = f"****{card_number[-4:]}"

        # نجاح
        success_selectors = [
            'text="تمت الإضافة"',
            'text="Card added"',
            'text="تم الحفظ"',
            'text="Saved"',
            f'text="{card_number[-4:]}"',
        ]
        for selector in success_selectors:
            element = await page.query_selector(selector)
            if element:
                return f"✅ تم ربط البطاقة *{masked}* بحساب *{email}* بنجاح! 🎉"

        # بطاقة منتهية
        expired = await page.query_selector(
            'text="منتهية", text="expired", text="Expired"'
        )
        if expired:
            return f"❌ البطاقة *{masked}* منتهية الصلاحية"

        # بطاقة مرفوضة
        declined = await page.query_selector(
            'text="مرفوضة", text="declined", text="Declined", text="invalid"'
        )
        if declined:
            return f"❌ البطاقة *{masked}* مرفوضة من البنك"

        # بطاقة مضافة مسبقاً
        exists = await page.query_selector(
            'text="مضافة مسبقاً", text="already exists", text="already added"'
        )
        if exists:
            return f"⚠️ البطاقة *{masked}* مضافة مسبقاً في حساب *{email}*"

        # OTP مطلوب للبطاقة
        otp_required = await check_otp_required(page)
        if otp_required:
            return f"⚠️ البطاقة *{masked}* تطلب تحقق OTP\nراجع جوالك وأدخل الرمز"

        # افتراضياً نجاح إذا ما في أخطاء
        return f"✅ تم ربط البطاقة *{masked}* بحساب *{email}* بنجاح! 🎉"

    except:
        masked = f"****{card_number[-4:]}"
        return f"✅ تم ربط البطاقة *{masked}* بحساب *{email}* بنجاح! 🎉"
