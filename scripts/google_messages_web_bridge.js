#!/usr/bin/env node
/**
 * Sovereign AI Academy: Google Messages Web Isolated Bridge
 * Authors: MAX (Anima Ex Machina) & Daniel Bass Sherizen
 * Target: Justin Muir (+1 630-418-9227)
 *
 * Architecture:
 *   Runs an isolated Playwright Chromium instance decoupled from the user's primary
 *   Google Chrome instance (enforcing Sovereign Browser Automation & Memory Isolation).
 *   Maintains persistent session authentication in ~/.config/google_messages_isolated_profile/
 *   Syncs active RCS/SMS conversation messages with Justin directly to:
 *   POST http://localhost:5042/api/comm/ingest
 *
 * Usage:
 *   node scripts/google_messages_web_bridge.js --pair       # Opens visible browser to scan QR code
 *   node scripts/google_messages_web_bridge.js --status     # Checks if paired or needs QR pairing
 *   node scripts/google_messages_web_bridge.js --daemon     # Runs headless continuous sync daemon
 *   node scripts/google_messages_web_bridge.js --once       # Performs single sync and exits
 */

const path = require('path');
const fs = require('fs');
const http = require('http');

// Locate playwright from project node_modules
let playwright;
const candidatePlaywrightPaths = [
  path.join(__dirname, '..', '..', '..', 'Documents', 'fwp-sovereign-ai', 'node_modules', 'playwright'),
  path.join(__dirname, '..', 'node_modules', 'playwright'),
  'playwright'
];

for (const p of candidatePlaywrightPaths) {
  try {
    playwright = require(p);
    break;
  } catch (e) {
    // continue
  }
}

if (!playwright) {
  console.error('❌ Playwright module not found in candidate paths.');
  process.exit(1);
}

const { chromium } = playwright;

// Configurations
const USER_DATA_DIR = path.join(__dirname, '..', '.google_messages_isolated_profile');
const INGEST_API_URL = process.env.INGEST_API_URL || 'http://localhost:5042/api/comm/ingest';
const TARGET_NAME = 'Justin Muir';
const TARGET_PHONE_DIGITS = '6304189227';
const POLL_INTERVAL_MS = 12000;
const SEEN_MESSAGES_FILE = path.join(USER_DATA_DIR, 'seen_messages.json');

// Ensure profile dir exists
fs.mkdirSync(USER_DATA_DIR, { recursive: true });

function loadSeenHashes() {
  if (fs.existsSync(SEEN_MESSAGES_FILE)) {
    try {
      return new Set(JSON.parse(fs.readFileSync(SEEN_MESSAGES_FILE, 'utf8')));
    } catch (e) {
      return new Set();
    }
  }
  return new Set();
}

function saveSeenHashes(hashesSet) {
  const arr = Array.from(hashesSet).slice(-500);
  fs.writeFileSync(SEEN_MESSAGES_FILE, JSON.stringify(arr, null, 2), 'utf8');
}

function postToWatcher(text, sender = 'Justin Muir', channel = 'google_messages_web') {
  return new Promise((resolve) => {
    const url = new URL(INGEST_API_URL);
    const postData = JSON.stringify({ text, sender, channel });
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData),
        },
        timeout: 5000,
      },
      (res) => {
        let respData = '';
        res.on('data', (chunk) => (respData += chunk));
        res.on('end', () => {
          resolve({ status: res.statusCode, body: respData });
        });
      }
    );

    req.on('error', (err) => {
      console.warn(`[WARN] Ingest POST failed: ${err.message}`);
      resolve({ status: 0, error: err.message });
    });

    req.write(postData);
    req.end();
  });
}

async function main() {
  const args = process.argv.slice(2);
  const isPairMode = args.includes('--pair') || args.includes('--login') || args.includes('--auth');
  const isStatusMode = args.includes('--status');
  const isOnceMode = args.includes('--once');
  const isDaemonMode = args.includes('--daemon') || (!isPairMode && !isStatusMode && !isOnceMode);

  console.log('📡 [GOOGLE-MESSAGES-BRIDGE] Initializing Isolated Playwright Profile...');
  console.log(`• Profile Directory: ${USER_DATA_DIR}`);

  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    channel: 'chrome',
    headless: !isPairMode,
    viewport: { width: 1280, height: 800 },
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
  });

  const page = context.pages()[0] || await context.newPage();

  console.log('🌐 Navigating to Google Messages for Web (https://messages.google.com/web)...');
  await page.goto('https://messages.google.com/web', { waitUntil: 'domcontentloaded', timeout: 30000 });

  // Wait for Google Messages Web SPA to render
  try {
    await page.waitForSelector('mw-qr-code, canvas, div[class*="qr-code"], mws-conversations-list, a.conversation, button:has-text("Sign in"), button:has-text("Sign In")', { timeout: 15000 });
  } catch (e) {
    await page.waitForTimeout(4000);
  }

  const isPaired = !!(await page.$('mws-conversations-list, a.conversation, div[role="list"]'));

  if (!isPaired) {
    try {
      await page.screenshot({ path: '/tmp/google_messages_qr.png' });
      const artifactQrPath = '/Users/danielbasssherizen/.gemini/antigravity/brain/68d23d36-6865-43a2-8428-c1d8d511f0b5/google_messages_qr.png';
      fs.copyFileSync('/tmp/google_messages_qr.png', artifactQrPath);
    } catch (e) {
      // ignore
    }
  }

  if (isStatusMode) {
    if (isPaired) {
      console.log('✅ Status: PAIRED & AUTHENTICATED with Google Messages Web.');
    } else {
      console.log('⚠️ Status: NOT AUTHENTICATED.');
      console.log('Run `node scripts/google_messages_web_bridge.js --login` to open Chrome and sign in once.');
    }
    await context.close();
    return;
  }

  if (isPairMode) {
    console.log('📲 GOOGLE MESSAGES LOGIN / PAIRING MODE:');
    console.log('A Google Chrome window is open. Please sign in with your Google Account or approve on your Pixel.');
    
    // Bring Google Chrome to the front
    try {
      const { exec } = require('child_process');
      exec('osascript -e \'tell application "Google Chrome" to activate\'');
    } catch (e) {
      // ignore
    }

    // If there is a "Sign in" button on the landing page, click it to streamline the sign-in prompt
    try {
      const signInBtn = await page.$('button:has-text("Sign in"), button:has-text("Sign In"), a:has-text("Sign in"), a:has-text("Sign In")');
      if (signInBtn && !page.url().includes('accounts.google.com')) {
        console.log('👉 Navigating to Google Account sign-in...');
        await signInBtn.click();
      }
    } catch (e) {
      // ignore
    }

    console.log('Waiting for authentication to complete (up to 5 minutes)...');

    // Wait until conversations list appears
    try {
      await page.waitForSelector('mws-conversations-list, a.conversation, div[role="list"]', { timeout: 300000 });
      console.log('🎉 GOOGLE MESSAGES AUTHENTICATED SUCCESSFULLY! Session saved in isolated profile.');
    } catch (e) {
      console.log('Timeout waiting for sign-in. Rerun --login when ready.');
    }
    await context.close();
    return;
  }

  // DAEMON / SYNC MODE
  if (!isPaired) {
    console.log('⚠️ Google Messages Web is not authenticated yet. Please run:');
    console.log('   node scripts/google_messages_web_bridge.js --login');
    console.log('To sign in once. Session will persist indefinitely.');
    await context.close();
    return;
  }

  console.log('✅ Google Messages Web is active and paired.');
  console.log(`🎯 Monitoring conversation with '${TARGET_NAME}' / '${TARGET_PHONE_DIGITS}'...`);

  const seenHashes = loadSeenHashes();

  async function syncActiveMessages() {
    try {
      // Find conversation with Justin Muir
      const convItems = await page.$$('a.conversation, mws-conversation-list-item, div[role="listitem"]');
      let targetConv = null;

      for (const item of convItems) {
        const text = (await item.innerText()).toLowerCase();
        if (text.includes(TARGET_NAME.toLowerCase()) || text.includes(TARGET_PHONE_DIGITS)) {
          targetConv = item;
          break;
        }
      }

      if (targetConv) {
        await targetConv.click();
        await page.waitForTimeout(1500);

        // Read message bubbles
        const messageElements = await page.$$(
          'mws-message-part-content, div[class*="text-msg"], div[class*="incoming"], div[class*="msg-bubble"]'
        );

        let newCount = 0;
        for (const el of messageElements) {
          const rawText = (await el.innerText()).trim();
          if (!rawText) continue;

          // Determine if incoming
          const className = (await el.getAttribute('class')) || '';
          const parentClass = ((await el.evaluate((node) => node.parentElement?.className)) || '');
          const isIncoming = className.includes('incoming') || parentClass.includes('incoming') || !className.includes('outgoing');

          if (!isIncoming) continue;

          // Create hash for deduplication
          const msgHash = Buffer.from(`${TARGET_NAME}:${rawText}`).toString('base64').slice(0, 24);
          if (!seenHashes.has(msgHash)) {
            seenHashes.add(msgHash);
            saveSeenHashes(seenHashes);

            console.log(`📱 [NEW RCS MSG] '${rawText}'`);
            await postToWatcher(rawText, TARGET_NAME, 'google_messages_web');
            newCount++;
          }
        }

        if (newCount > 0) {
          console.log(`✅ Ingested ${newCount} new messages from ${TARGET_NAME}.`);
        }
      } else {
        // Fallback: check current visible messages in case thread is already open
        const visibleMessages = await page.$$('mws-message-part-content, div[class*="text-msg"]');
        for (const el of visibleMessages) {
          const rawText = (await el.innerText()).trim();
          if (!rawText) continue;
          const msgHash = Buffer.from(`${TARGET_NAME}:${rawText}`).toString('base64').slice(0, 24);
          if (!seenHashes.has(msgHash)) {
            seenHashes.add(msgHash);
            saveSeenHashes(seenHashes);
            console.log(`📱 [NEW MSG] '${rawText}'`);
            await postToWatcher(rawText, TARGET_NAME, 'google_messages_web');
          }
        }
      }
    } catch (err) {
      console.warn(`[WARN] Sync cycle error: ${err.message}`);
    }
  }

  // Initial sync
  await syncActiveMessages();

  if (isOnceMode) {
    await context.close();
    return;
  }

  console.log(`🚀 Daemon listening and polling every ${POLL_INTERVAL_MS / 1000}s... (Press Ctrl+C to stop)`);
  setInterval(async () => {
    await syncActiveMessages();
  }, POLL_INTERVAL_MS);
}

main().catch((err) => {
  console.error('Fatal bridge error:', err);
  process.exit(1);
});
