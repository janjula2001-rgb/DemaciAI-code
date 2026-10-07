// Batch capture of onetricks.gg matchup builds (built-in browser, javascript_tool, run from any onetricks.gg tab).
// Before running: replace ENEMIES with e.g. ['Pantheon','Gragas'] and CAPTURE_DATE with today's date
// (and role=top in load() if needed). Same extractor as onetricks_extract.js, run in same-site hidden iframes.
// Save the returned JSON as data/raw/onetricks/_batch.json, then: split_onetricks_batch.py <role>.
const extract = (doc) => {
  const win = doc.defaultView, a = doc.querySelector('article'); if (!a) return null;
  const out = [];
  const hdr = /^(?:\w+ )?(Starting Items|Build Path|Popular Items|Boots|Legendary|Runes|Skills and Spells|Summoners|Levels 1-3|Skill Priority|Levels 1-13|Recent Games)$/;
  const ownText = n => [...n.childNodes].filter(c => c.nodeType === 3).map(c => c.textContent).join('').trim();
  const w = doc.createTreeWalker(a, 1); let n;
  while ((n = w.nextNode())) {
    const cl = (n.className || '').toString();
    const t = n.children.length === 0 || /^H\d$/.test(n.tagName) ? n.textContent.trim() : '';
    if (hdr.test(t)) { out.push('\n#' + t.replace(/^Garen /, '')); if (/Recent Games/.test(t)) break; continue; }
    const tip = n.getAttribute('data-tooltip-html');
    if (tip) { if (/nonActive/i.test(cl)) continue; const m = tip.match(/<b>(.*?)<\/b>/); out.push('[' + (m ? m[1] : tip.replace(/<[^>]+>/g, ' ').trim().slice(0, 30)) + ']'); continue; }
    if (n.tagName === 'IMG' && n.alt && !/Rank=/.test(n.alt)) out.push('[' + n.alt + ']');
    const st = n.getAttribute('style') || '';
    const sp = st.match(/(\d+\.\d+\.\d+)\/img\/sprite\/(spell\d+)\./);
    if (sp) { const cs = win.getComputedStyle(n); out.push('SP:' + sp[1] + '/' + sp[2] + '@' + cs.backgroundPosition.replace(/px/g, '').replace(' ', ',') + '/' + parseInt(cs.width)); }
    const own = ownText(n);
    if (/^\d+(\.\d+)?\s*%$/.test(own)) { out.push(own.replace(/\s/g, '')); continue; }
    if (/skillLevelUp/.test(cl)) out.push('L' + n.textContent.trim() + ':' + 'QWER'[[...n.parentElement.children].indexOf(n)]);
  }
  const ks = {}; const cell = st => { const [x, y] = st.match(/background-position:\s*([^;]+)/)[1].split(' ').map(parseFloat); const ww = parseFloat(st.match(/width:\s*([\d.]+)px/)[1]); return Math.round(-x / ww) + 5 * Math.round(-y / ww); };
  a.querySelectorAll('[data-tooltip-html][style*=keystone]').forEach(e => { const m = e.getAttribute('data-tooltip-html').match(/<b>(.*?)<\/b>/); if (m) ks[cell(e.getAttribute('style'))] = m[1]; });
  const rc = [...a.querySelectorAll('h2')].find(h => /Runes$/.test(h.textContent.trim()));
  const opts = rc ? [...rc.closest('.cardBorder').querySelectorAll('div[style*="cursor:pointer"]')].filter(o => /%/.test(o.textContent)) : [];
  const keystones = opts.map(o => { const img = o.querySelector('img'), sp = o.querySelector('div[style*=keystone]'); const name = img ? img.alt : sp ? (ks[cell(sp.getAttribute('style'))] || 'cell:' + cell(sp.getAttribute('style'))) : '?'; return '[' + name + '] ' + o.textContent.trim() + (/border:1px/.test(o.getAttribute('style') || '') ? ' (shown below)' : ''); });
  const range = (a.innerText.match(/\b\d+\.\d+\s*-\s*\d+\.\d+\b/) || [(a.innerText.match(/\b1\d\.\d+\b/) || ['?'])[0]])[0].replace(/\s/g, '');
  return doc.location.href + '\n# patches ' + range + '\n# captured CAPTURE_DATE via built-in browser + scripts/onetricks_extract.js; page filter: Masters+, All Major regions\n#Keystones ' + keystones.join(' | ') + '\n' + out.join(' ');
};
const load = (enemy) => new Promise(res => {
  const f = document.createElement('iframe'); f.style.cssText = 'width:1300px;height:900px;position:fixed;left:-3000px;top:0';
  f.src = '/champions/builds/Garen?matchup=' + enemy + '&role=top';
  document.body.appendChild(f);
  const t0 = Date.now();
  const poll = setInterval(() => { let d; try { d = f.contentDocument; } catch (e) {}
    const ready = d && d.querySelector('article') && /Recent Games/.test(d.querySelector('article').innerText) && d.querySelector('[class*=skillLevelUp]');
    if (ready || Date.now() - t0 > 25000) { clearInterval(poll); setTimeout(() => { const r = ready ? extract(d) : 'TIMEOUT ' + enemy; f.remove(); res(r); }, 1500); } }, 500);
});
const res = {}; for (const e of ENEMIES) { res[e] = await load(e); await new Promise(r => setTimeout(r, 2000)); }
JSON.stringify(res)
