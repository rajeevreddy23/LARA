"""
LARA Autonomous WhatsApp Web Automation Engine.
Uses Playwright with a persistent Google Chrome browser profile to directly
search contacts/groups, open conversations, and transmit messages via DOM manipulation.
"""

import os
import re
import time
import asyncio
import logging
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger("lara.whatsapp.web_engine")

SESSION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "wa_chrome_profile"))
os.makedirs(SESSION_DIR, exist_ok=True)


class WhatsAppWebEngine:
    def __init__(self):
        self._lock = asyncio.Lock()

    async def send_message(
        self,
        recipient: str,
        message: str,
        phone: Optional[str] = None,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        Autonomously dispatch a message to a contact/group name (e.g. 'Project Hub')
        or a phone number via Playwright.
        """
        async with self._lock:
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    # Launch persistent Chrome context
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=SESSION_DIR,
                        channel="chrome",
                        headless=headless,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--start-maximized"
                        ],
                        viewport=None
                    )

                    page = context.pages[0] if context.pages else await context.new_page()

                    # Flow 1: Direct Phone Number URL
                    if phone:
                        clean_phone = re.sub(r"[^\d+]", "", phone).replace("+", "")
                        encoded_msg = urllib.parse.quote(message)
                        target_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
                        logger.info("Navigating to direct phone URL: %s", target_url)
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)

                        # Wait for send button or message box
                        try:
                            send_btn = await page.wait_for_selector(
                                'span[data-icon="send"], button[aria-label="Send"]',
                                timeout=20000
                            )
                            if send_btn:
                                await send_btn.click()
                                await asyncio.sleep(2.0)
                                await context.close()
                                return {
                                    "success": True,
                                    "method": "direct_phone",
                                    "recipient": recipient,
                                    "message": message
                                }
                        except Exception:
                            # Fallback enter press
                            await page.keyboard.press("Enter")
                            await asyncio.sleep(2.0)
                            await context.close()
                            return {
                                "success": True,
                                "method": "direct_phone_enter",
                                "recipient": recipient,
                                "message": message
                            }

                    # Flow 2: Live Contact / Group Search & Send (e.g. 'Project Hub')
                    logger.info("Opening https://web.whatsapp.com for search & send...")
                    await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=45000)

                    # 1. Check if logged in or if QR code is visible
                    search_selector = (
                        'div[contenteditable="true"][data-tab="3"], '
                        '[aria-label="Search input textbox"], '
                        '[aria-label="Search or start new chat"], '
                        'div[title="Search input textbox"]'
                    )

                    search_box = None
                    try:
                        search_box = await page.wait_for_selector(search_selector, timeout=12000)
                    except Exception:
                        qr_canvas = await page.query_selector("canvas")
                        if qr_canvas:
                            logger.info("WhatsApp Web QR code detected. Waiting up to 60s for user to scan with phone...")
                            try:
                                search_box = await page.wait_for_selector(search_selector, timeout=60000)
                            except Exception:
                                return {
                                    "success": False,
                                    "requires_qr": True,
                                    "error": "WhatsApp Web requires a one-time QR scan. Please link your phone in the browser window on your screen."
                                }

                    if not search_box:
                        raise RuntimeError("Could not find search input on WhatsApp Web.")

                    # 2. Click search box and type recipient name
                    logger.info("Typing recipient '%s' into WhatsApp search box...", recipient)
                    await search_box.click()
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await page.keyboard.type(recipient, delay=35)
                    await asyncio.sleep(1.8)

                    # 3. Locate chat result item and click it
                    chat_clicked = False
                    for pattern in [recipient, recipient.lower(), recipient.title(), recipient.upper()]:
                        try:
                            item = await page.wait_for_selector(
                                f'span[title*="{pattern}" i], div[role="listitem"]:has-text("{pattern}"), span:has-text("{pattern}")',
                                timeout=3000
                            )
                            if item:
                                await item.click()
                                chat_clicked = True
                                await asyncio.sleep(1.0)
                                break
                        except Exception:
                            pass

                    if not chat_clicked:
                        logger.info("Chat selector not found, navigating with ArrowDown + Enter...")
                        await page.keyboard.press("ArrowDown")
                        await asyncio.sleep(0.3)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(1.0)

                    # 4. Type and send message in active conversation
                    msg_box_selector = (
                        'footer div[contenteditable="true"], '
                        'div[contenteditable="true"][data-tab="10"], '
                        'div[title="Type a message"]'
                    )
                    try:
                        msg_box = await page.wait_for_selector(msg_box_selector, timeout=8000)
                        await msg_box.click()
                        await page.keyboard.type(message, delay=20)
                        await asyncio.sleep(0.3)
                        send_btn = await page.query_selector('span[data-icon="send"], button[aria-label="Send"], button span[data-icon="send"]')
                        if send_btn:
                            await send_btn.click()
                        else:
                            await page.keyboard.press("Enter")
                        await asyncio.sleep(2.0)
                    except Exception:
                        await page.keyboard.type(message, delay=20)
                        await asyncio.sleep(0.3)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(2.0)

                    # 5. Verify that the message appears as sent in the conversation
                    verified_sent = False
                    try:
                        # Check for sent message bubble with matching text
                        sent_bubble = await page.wait_for_selector(f'div.message-out span:has-text("{message}")', timeout=5000)
                        if sent_bubble:
                            verified_sent = True
                    except Exception:
                        # Fallback verification: message input box is now empty and not containing unsubmitted text
                        try:
                            box_content = await msg_box.inner_text()
                            if not box_content.strip():
                                verified_sent = True
                        except Exception:
                            pass

                    logger.info("Message sent (verified=%s) via WhatsApp Web engine to '%s'.", verified_sent, recipient)
                    await context.close()
                    return {
                        "success": True,
                        "verified_sent": verified_sent,
                        "method": "live_web_search_and_send",
                        "recipient": recipient,
                        "message": message
                    }

            except Exception as ex:
                logger.error("WhatsApp Web engine error: %s", ex)
                return {"success": False, "error": str(ex)}


wa_web_engine = WhatsAppWebEngine()
