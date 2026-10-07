// Run in the browser on a rendered onetricks.gg builds page (built-in browser, javascript_tool).
// Returns a compact token stream; save it to data/raw/onetricks/<role>_<enemy>.txt and parse in Python.
//   #Section          section header
//   [Name]            selected item / rune / ability (from the icon's tooltip; non-selected runes skipped)
//   12.3%             share / pick rate shown next to the preceding icons
//   SP:<ver>/spell0@x,y/w  summoner-spell sprite; decode with Data Dragon <ver> summoner.json (48px grid, scale 48/w)
//   L<n>:<Q|W|E|R>    skill levelled at level n
(() => {
  const a = document.querySelector('article');
  const out = [];
  const hdr = /^(?:\w+ )?(Starting Items|Build Path|Popular Items|Boots|Legendary|Runes|Skills and Spells|Summoners|Levels 1-3|Skill Priority|Levels 1-13|Recent Games)$/;
  const ownText = n => [...n.childNodes].filter(c => c.nodeType === 3).map(c => c.textContent).join('').trim();
  const w = document.createTreeWalker(a, NodeFilter.SHOW_ELEMENT);
  let n;
  while ((n = w.nextNode())) {
    const cl = (n.className || '').toString();
    const t = n.children.length === 0 || /^H\d$/.test(n.tagName) ? n.textContent.trim() : '';
    if (hdr.test(t)) { out.push('\n#' + t.replace(/^Garen /, '')); if (/Recent Games/.test(t)) break; continue; }
    const tip = n.getAttribute('data-tooltip-html');
    if (tip) {
      if (/nonActive/i.test(cl)) continue;
      const m = tip.match(/<b>(.*?)<\/b>/);
      out.push('[' + (m ? m[1] : tip.replace(/<[^>]+>/g, ' ').trim().slice(0, 30)) + ']');
      continue;
    }
    if (n.tagName === 'IMG' && n.alt && !/Rank=/.test(n.alt)) { out.push('[' + n.alt + ']'); }
    const st = n.getAttribute('style') || '';
    const sp = st.match(/(\d+\.\d+\.\d+)\/img\/sprite\/(spell\d+)\./);
    if (sp) {
      const cs = getComputedStyle(n);
      out.push('SP:' + sp[1] + '/' + sp[2] + '@' + cs.backgroundPosition.replace(/px/g, '').replace(' ', ',') + '/' + parseInt(cs.width));
    }
    const own = ownText(n);
    if (/^\d+(\.\d+)?\s*%$/.test(own)) { out.push(own.replace(/\s/g, '')); continue; }
    if (/skillLevelUp/.test(cl)) {
      // Each level is a column of 4 cells (Q, W, E, R); the levelled cell's index gives the skill.
      out.push('L' + n.textContent.trim() + ':' + 'QWER'[[...n.parentElement.children].indexOf(n)]);
    }
  }
  // Keystone picker: options are an <img alt> or an unnamed sprite. Name sprites via the rune tree,
  // whose keystone sprites carry tooltips (sprite grid: 5 columns, cell = element width).
  const ks = {};
  const cell = st => {
    const [x, y] = st.match(/background-position:\s*([^;]+)/)[1].split(' ').map(parseFloat);
    const w = parseFloat(st.match(/width:\s*([\d.]+)px/)[1]);
    return Math.round(-x / w) + 5 * Math.round(-y / w);
  };
  a.querySelectorAll('[data-tooltip-html][style*=keystone]').forEach(e => {
    const m = e.getAttribute('data-tooltip-html').match(/<b>(.*?)<\/b>/);
    if (m) ks[cell(e.getAttribute('style'))] = m[1];
  });
  const runesCard = [...a.querySelectorAll('h2')].find(h => /Runes$/.test(h.textContent.trim()));
  const opts = runesCard ? [...runesCard.closest('.cardBorder').querySelectorAll('div[style*="cursor:pointer"]')].filter(o => /%/.test(o.textContent)) : [];
  const keystones = opts.map(o => {
    const img = o.querySelector('img'), sp = o.querySelector('div[style*=keystone]');
    const name = img ? img.alt : sp ? (ks[cell(sp.getAttribute('style'))] || 'cell:' + cell(sp.getAttribute('style'))) : '?';
    return '[' + name + '] ' + o.textContent.trim() + (/border:1px/.test(o.getAttribute('style') || '') ? ' (shown below)' : '');
  });
  const range = (a.innerText.match(/\b\d+\.\d+-\d+\.\d+\b/) || ['?'])[0];
  return location.href + '\n# patches ' + range + '\n#Keystones ' + keystones.join(' | ') + '\n' + out.join(' ');
})()
