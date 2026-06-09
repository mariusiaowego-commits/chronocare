#!/usr/bin/env python3
"""
Download CT images - scroll until no new images per series.
"""
import json, time, base64
from pathlib import Path
from playwright.sync_api import sync_playwright

SHARE_URL = "https://zscloud.zs-hospital.sh.cn/film/#/shared?code=v8VOtIVNAhkR0I1NOkLaOxpLG2J%2FJg0k86F9CrEeJ1hu9CGk"
OUTPUT_DIR = Path("/Users/mt16/dev/chronocare/data/medical_images/tjh_ct_20250417")

XHR_INTERCEPTOR = '''() => {
    if (window._allImages) return;
    window._allImages = {};
    const origOpen = XMLHttpRequest.prototype.open;
    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this._url = url;
        return origOpen.call(this, method, url, ...args);
    };
    XMLHttpRequest.prototype.send = function(...args) {
        this.addEventListener('load', function() {
            if (this._url && this._url.includes('getJpegFilm')) {
                try {
                    const buf = this.response;
                    if (buf instanceof ArrayBuffer) {
                        const bytes = new Uint8Array(buf);
                        if (bytes[0] === 0xFF && bytes[1] === 0xD8) {
                            const m = this._url.match(/objectUID=([^&]+)/);
                            const uid = m ? m[1] : null;
                            if (uid && !window._allImages[uid]) {
                                let bin = '';
                                for (let i = 0; i < bytes.length; i += 8192) {
                                    bin += String.fromCharCode.apply(null, bytes.subarray(i, Math.min(i + 8192, bytes.length)));
                                }
                                window._allImages[uid] = btoa(bin);
                            }
                        }
                    }
                } catch(e) {}
            }
        });
        return origSend.call(this, ...args);
    };
}'''

def main():
    hierarchy_data = [None]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel='chrome')
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        def on_resp(response):
            if 'getHierachy' in response.url and response.status == 200:
                try:
                    hierarchy_data[0] = response.json()
                except:
                    pass
        page.on('response', on_resp)

        print("Loading...", flush=True)
        page.goto(SHARE_URL, timeout=45000)
        time.sleep(12)
        page.get_by_text('查看影像').click()
        time.sleep(10)

        # Parse hierarchy
        h = hierarchy_data[0].get('data', {})
        if isinstance(h, str):
            h = json.loads(h)
        patient = h['PatientInfo']
        
        uid_to_series = {}
        series_meta = {}
        for study in patient['StudyList']:
            for series in study['SeriesList']:
                snum = series['SeriesNum']
                series_meta[snum] = {
                    'name': series.get('SeriesDes', '').strip(),
                    'protocol': series.get('ProtocolName', ''),
                    'modality': series.get('Modality', ''),
                    'expected': len(series.get('ImageList', [])),
                }
                for img in series.get('ImageList', []):
                    uid_to_series[img['UID']] = snum

        print(f"UIDs: {len(uid_to_series)}, Series: {len(series_meta)}", flush=True)

        page.evaluate(XHR_INTERCEPTOR)

        series_count = page.evaluate('() => document.querySelectorAll(".series-selector .selector").length')
        
        for i in range(1, series_count + 1):
            page.click(f'.series-selector .selector:nth-child({i})')
            time.sleep(2)
            
            # Scroll until no new images
            prev_count = 0
            stale = 0
            cur = 0
            scroll_round = 0
            for scroll_round in range(200):
                page.evaluate('''() => {
                    document.querySelectorAll('.el-scrollbar__wrap').forEach(c => {
                        if (c.scrollHeight > c.clientHeight) c.scrollTop += 1000;
                    });
                }''')
                time.sleep(0.15)
                
                cur = page.evaluate('() => Object.keys(window._allImages).length')
                if cur > prev_count:
                    prev_count = cur
                    stale = 0
                else:
                    stale += 1
                
                if stale >= 20:
                    break
            
            print(f"  Series {i}: {cur} total ({scroll_round} scrolls)", flush=True)

        # Extract and organize
        all_images = page.evaluate('() => window._allImages')
        print(f"\nCaptured: {len(all_images)} unique", flush=True)

        # Clear old series dirs
        for d in OUTPUT_DIR.iterdir():
            if d.is_dir() and d.name.startswith('series_'):
                import shutil
                shutil.rmtree(d, ignore_errors=True)

        series_dirs = {}
        series_counts = {}
        for snum in sorted(series_meta.keys()):
            meta = series_meta[snum]
            name = meta['name'] or f'Series{snum}'
            safe = name.replace(' ', '_').replace('/', '_').replace('.', 'd').replace('%', 'pct')[:50]
            d = OUTPUT_DIR / f'series_{snum:02d}_{safe}'
            d.mkdir(exist_ok=True)
            series_dirs[snum] = d
            series_counts[snum] = 0

        for uid, b64 in all_images.items():
            img_bytes = base64.b64decode(b64)
            if img_bytes[:2] != b'\xff\xd8':
                continue
            snum = uid_to_series.get(uid)
            if snum and snum in series_dirs:
                fname = uid.replace('.', '_')[:60] + '.jpg'
                with open(series_dirs[snum] / fname, 'wb') as f:
                    f.write(img_bytes)
                series_counts[snum] += 1

        total = 0
        for snum in sorted(series_meta.keys()):
            meta = series_meta[snum]
            dl = series_counts[snum]
            exp = meta['expected']
            total += dl
            mark = "✓" if dl == exp else f"(-{exp-dl})"
            print(f"  S{snum:2d} [{meta['name'][:35]:35s}]: {dl:4d}/{exp:4d} {mark}", flush=True)
        
        print(f"\nTotal: {total}/{len(uid_to_series)}", flush=True)

        manifest = {
            'patient': patient['Name'],
            'patient_id': patient['ID'],
            'study_date': '20250417',
            'total_downloaded': total,
            'total_expected': len(uid_to_series),
            'series': {}
        }
        for snum in sorted(series_meta.keys()):
            meta = series_meta[snum]
            manifest['series'][str(snum)] = {
                'name': meta['name'], 'protocol': meta['protocol'],
                'modality': meta['modality'], 'expected': meta['expected'],
                'downloaded': series_counts[snum], 'dir': str(series_dirs[snum])
            }
        with open(OUTPUT_DIR / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        browser.close()

if __name__ == "__main__":
    main()
