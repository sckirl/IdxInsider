const { chromium } = require('playwright');

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const IDX_ANNOUNCEMENT_URL = 'https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/';

async function runExternalQA() {
    console.log('--- STARTING EXTERNAL QA CROSS-CHECK ---');
    console.log(`Target Backend: ${BACKEND_URL}`);
    
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    try {
        console.log(`Navigating to IDX: ${IDX_ANNOUNCEMENT_URL}`);
        await page.goto(IDX_ANNOUNCEMENT_URL, { waitUntil: 'networkidle' });
        
        // Use the browser to fetch the same API the scraper uses, or scrape the DOM
        const keyword = "Laporan Kepemilikan";
        console.log(`Searching for keyword: ${keyword}`);
        
        // Wait for table to load
        console.log('Waiting for announcement table...');
        await page.waitForSelector('.table-announcement, table', { timeout: 10000 });
        
        const externalItems = await page.evaluate(() => {
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            return rows.map(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length < 5) return null;
                const link = row.querySelector('a[href*=".pdf"]');
                return {
                    date: cells[1]?.innerText.strip,
                    ticker: cells[2]?.innerText.trim(),
                    title: cells[3]?.innerText.trim(),
                    url: link ? link.href : null
                };
            }).filter(item => item && item.url);
        });
        
        console.log(`Found ${externalItems.length} announcements on IDX DOM.`);
        
        if (externalItems.length === 0) {
            console.log('No recent announcements found on IDX to cross-check.');
            // Fallback: try the API again but with more care
            console.log('Retrying via API with direct navigation...');
            const dateFrom = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0].replace(/-/g, '');
            const apiUrl = `https://www.idx.co.id/primary/ListedCompany/GetAnnouncement?kodeEmiten=&emitenType=*&indexFrom=0&pageSize=20&dateFrom=${dateFrom}&dateTo=20261231&lang=id&keyword=Laporan%20Kepemilikan`;
            await page.goto(apiUrl);
            const content = await page.innerText('body');
            try {
                const data = JSON.parse(content);
                const items = data.Results || data.Replies || [];
                console.log(`API Retry found ${items.length} items.`);
                // Process these items... (omitted for brevity in this replace, I'll update the whole logic)
            } catch (e) {
                console.error('API Retry failed to parse JSON.');
            }
            return;
        }

        // Get latest from backend
        console.log('Fetching data from Backend...');
        let backendData = [];
        try {
            const backendRes = await fetch(`${BACKEND_URL}/insider/latest`);
            backendData = await backendRes.json();
        } catch (err) {
            console.error(`Could not reach backend at ${BACKEND_URL}. Verification partially failed.`);
            console.log('Sample External URLs that SHOULD be in DB:');
            externalItems.slice(0, 3).forEach(item => {
                const att = item.Attachments?.[0];
                if (att) console.log(` - ${att.FullSizeUrl || att.FullSavePath}`);
            });
            return;
        }

        const backendUrls = new Set(backendData.map(t => t.source_url));
        
        let matchCount = 0;
        let missingCount = 0;
        
        for (const item of externalItems) {
            const url = item.url;
            if (!url) continue;
            
            if (backendUrls.has(url)) {
                matchCount++;
            } else {
                console.warn(`[MISSING] Announcement not in DB: ${url} (${item.title})`);
                missingCount++;
            }
        }
        
        console.log('--- QA RESULTS ---');
        console.log(`Total External Filings Checked: ${externalItems.length}`);
        console.log(`Matched in DB: ${matchCount}`);
        console.log(`Missing in DB: ${missingCount}`);
        
        if (missingCount === 0 && matchCount > 0) {
            console.log('SUCCESS: All recent IDX filings are present in the system.');
        } else if (matchCount === 0) {
            console.error('FAILURE: No matching filings found. Database might be empty or scraper is failing.');
        } else {
            console.warn(`WARNING: ${missingCount} filings are missing. Scraper might need to be triggered.`);
        }

    } catch (err) {
        console.error('QA Script Error:', err.message);
    } finally {
        await browser.close();
    }
}

runExternalQA();
