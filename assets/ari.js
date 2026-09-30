/* ARI Physical Therapy — site search, click tracking and the analytics opt-out notice.
   Loaded with `defer` on every page. The search index (search-index.json) is built by
   _tools/build_search_index.py and fetched only when someone starts to search. */
(function(){
  'use strict';
  var GA_ID = 'G-30S49569Y9';

  /* ---------- analytics helpers ---------- */
  function track(name, params){
    if(typeof gtag === 'function' && !window['ga-disable-' + GA_ID]) gtag('event', name, params || {});
  }
  function where(el){
    return el.closest('.top-bar') ? 'top_bar'
         : el.closest('.nav-contact') ? 'mobile_menu'
         : el.closest('.nav-links') ? 'nav'
         : el.closest('.page-hero, .hero-full') ? 'hero'
         : el.closest('.side-card') ? 'sidebar'
         : el.closest('.site-search') ? 'search'
         : el.closest('.cond-actions') ? 'condition_list'
         : el.closest('footer') ? 'footer' : 'page_body';
  }
  /* Search terms are recorded to learn what patients look for; anything that looks like
     contact details is stripped first so a visitor's own phone or email is never stored. */
  function clean(term){
    return term.replace(/\S+@\S+/g, '[email]').replace(/\+?\d[\d\s().-]{6,}\d/g, '[number]').slice(0, 80);
  }

  /* ---------- click tracking (phone/fax/email taps are tracked inline on each page) ---------- */
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a, .cond-tab');
    if(!a) return;
    if(a.classList.contains('cond-tab')){ track('condition_tab_select', { tab: a.getAttribute('aria-controls') }); return; }
    var href = a.getAttribute('href') || '';
    if(/appointment\.html/.test(href)) track('book_click', { link_location: where(a), link_text: (a.textContent || '').trim().slice(0, 40) });
    else if(/google\.[a-z.]+\/maps|maps\.apple\.com|maps\.google/.test(href)) track('directions_click', { link_location: where(a) });
    else if(a.classList.contains('cond-link')) track('condition_guide_click', { condition_page: href.split('?')[0] });
    else if(/ReferralPadForm\.pdf/.test(href)) track('referral_form_download', { link_location: where(a) });
  });

  /* ---------- analytics opt-out notice (?notrack=1 / ?notrack=0, handled in <head>) ---------- */
  (function(){
    var m = location.search.match(/[?&]notrack=([01])/);
    if(!m) return;
    var n = document.createElement('div');
    n.className = 'notrack-toast'; n.setAttribute('role', 'status');
    n.textContent = m[1] === '1'
      ? 'This browser is no longer counted in ARI website analytics.'
      : 'This browser is counted in ARI website analytics again.';
    document.body.appendChild(n);
    setTimeout(function(){ n.classList.add('out'); }, 5000);
  })();

  /* ---------- search ---------- */
  var index = null, loading = null;
  var STOP = ' a about after all also am an and any are at be been before but can do does doing during for from get got had has have he her him his how i if im in into is it its just me my not of on or our out over really she so some that the their them there they this to up very was we were what when where which while who why will with would you your '.split(' ');
  /* everyday words -> the words the site uses */
  var SYN = {
    dizzy:'vertigo dizziness bppv', dizziness:'vertigo', spinning:'vertigo', vertigo:'bppv dizziness',
    leak:'bladder incontinence', leaking:'bladder incontinence', pee:'bladder urine incontinence', urine:'bladder incontinence',
    incontinence:'bladder leaks', bladder:'incontinence',
    heel:'plantar fasciitis foot', foot:'plantar fasciitis heel', plantar:'heel',
    jaw:'tmj', tmj:'jaw', clicking:'tmj jaw',
    back:'sciatica spine', sciatic:'sciatica', disc:'sciatica herniated', spine:'sciatica back',
    neck:'headaches whiplash', headache:'headaches neck', migraine:'headaches',
    shoulder:'rotator cuff frozen', rotator:'shoulder', elbow:'tennis golfers', wrist:'carpal tunnel', hand:'carpal tunnel numbness',
    knee:'arthritis', arthritis:'knee osteoarthritis', hip:'orthopedic',
    pregnant:'prenatal postpartum pregnancy', pregnancy:'prenatal postpartum', baby:'postpartum pediatric', postpartum:'diastasis pelvic',
    prolapse:'pelvic organ', pelvic:'pelvic floor', sex:'pelvic pain painful',
    kid:'pediatric child', kids:'pediatric children', child:'pediatric', children:'pediatric', son:'pediatric', daughter:'pediatric',
    bone:'osteoporosis', bones:'osteoporosis', osteopenia:'osteoporosis', fall:'balance osteoporosis',
    car:'accident whiplash', accident:'whiplash car', crash:'accident whiplash',
    surgery:'post-surgical surgical prehab', replacement:'surgery joint knee', acl:'sports surgery',
    sports:'sports injury athletes', sport:'sports injury', soccer:'sports injury', football:'sports injury', basketball:'sports injury',
    baseball:'sports injury', softball:'sports injury', volleyball:'sports injury', running:'sports injury', runner:'sports injury', golf:'sports golfers',
    insurance:'medicare insurance plans', medicare:'insurance', cost:'insurance', pay:'insurance payment',
    referral:'referral doctor prescription direct access', doctor:'referral physician', prescription:'referral',
    appointment:'book schedule evaluation', book:'appointment', schedule:'appointment', hours:'open monday friday',
    parking:'parking park', park:'parking', location:'address stockdale located', address:'stockdale located', directions:'located parking',
    spanish:'languages español hindi', hindi:'languages', language:'languages', cancel:'cancellation', cancellation:'cancel',
    telehealth:'virtual online person', virtual:'telehealth', first:'first visit evaluation expect', visit:'evaluation expect'
  };

  function norm(s){ return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9\s-]/g, ' '); }
  function words(s){ return norm(s).split(/[\s-]+/).filter(Boolean); }
  function near(a, b){                      /* true if b is within 1 edit of a (2 for long words) */
    var max = a.length >= 7 ? 2 : 1;
    if(Math.abs(a.length - b.length) > max) return false;
    var prev = [], cur, i, j;
    for(j = 0; j <= b.length; j++) prev[j] = j;
    for(i = 1; i <= a.length; i++){
      cur = [i]; var best = i;
      for(j = 1; j <= b.length; j++){
        cur[j] = Math.min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + (a[i-1] === b[j-1] ? 0 : 1));
        if(cur[j] < best) best = cur[j];
      }
      if(best > max) return false;
      prev = cur;
    }
    return prev[b.length] <= max;
  }
  function prep(list){
    list.forEach(function(e){
      e._f = [[words(e.title), 8], [words(e.k), 5], [words(e.h), 3], [words(e.d), 2], [words(e.x), 1]];
      e._w = e.t === 'condition' ? 1.25 : e.t === 'page' ? 1.1 : 1;
    });
    return list;
  }
  function load(){
    if(index) return Promise.resolve(index);
    if(!loading) loading = fetch('search-index.json').then(function(r){ return r.json(); }).then(function(d){ index = prep(d); return index; });
    return loading;
  }
  function score(e, terms){
    var total = 0, hitTerms = 0;
    terms.forEach(function(t){
      var best = 0;
      e._f.forEach(function(f){
        var ws = f[0], w = f[1];
        for(var i = 0; i < ws.length; i++){
          var x = ws[i], s = 0;
          if(x === t.w) s = w;
          else if(t.w.length >= 3 && x.indexOf(t.w) === 0) s = w * 0.8;
          else if(t.w.length >= 4 && x[0] === t.w[0] && near(t.w, x)) s = w * 0.6;   /* typo-tolerant, same first letter */
          if(s){ s *= t.weight; if(s > best) best = s; }
        }
      });
      if(best){ total += best; if(t.weight === 1) hitTerms++; }
    });
    return total ? (total + hitTerms * 10) * e._w : 0;
  }
  function search(q){
    var base = words(q).filter(function(w){ return STOP.indexOf(w) === -1; });
    if(!base.length) return [];
    var terms = base.map(function(w){ return { w: w, weight: 1 }; });
    base.forEach(function(w){ (SYN[w] ? words(SYN[w]) : []).forEach(function(s){ terms.push({ w: s, weight: 0.6 }); }); });
    /* who/what the visitor is asking about: a child, or a sport */
    var kid = /\b(kid|kids|child|children|son|daughter|toddler|teen|teenager|baby|infant)\b/.test(norm(q));
    var sporty = /\b(soccer|football|basketball|baseball|softball|volleyball|running|runner|sport|sports|athlete|golf|tennis)\b/.test(norm(q));
    function boost(e){
      return (kid && /pediatric/.test(e.u) ? 1.8 : 1) * (sporty && /sports-injury/.test(e.u) ? 1.5 : 1)
           * (e.t === 'faq' && e.u === 'faq.html' ? 1.15 : 1);   /* prefer the general FAQ's wording */
    }
    var ranked = index.map(function(e){ var sc = score(e, terms); return { e: e, s: sc * (sc ? boost(e) : 1) }; })
      .filter(function(r){ return r.s > 0; })
      .sort(function(a, b){ return b.s - a.s; });
    /* drop weak tail matches (e.g. a page that only mentions a word in passing) */
    var cut = ranked.length ? ranked[0].s * 0.45 : 0;
    /* collapse near-duplicate questions ("Do I need a referral for X / for Y…") to the best one */
    var seen = {};
    return ranked.filter(function(r){
      if(r.s < cut) return false;
      if(r.e.t !== 'faq') return true;
      var key = words(r.e.title).slice(0, 5).join(' ');
      if(seen[key]) return false;
      return (seen[key] = true);
    }).slice(0, 7).map(function(r){ return r.e; });
  }
  function esc(s){ return (s || '').replace(/[&<>"]/g, function(c){ return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;' }[c]; }); }
  var LABEL = { page: 'Page', faq: 'Question', condition: 'Condition' };

  /* One search widget; used inline on the homepage and inside the header dialog. */
  function widget(root){
    var input = root.querySelector('.site-search-input'), out = root.querySelector('.site-search-results'), timer, lastLogged = '';
    function render(q){
      if(!q.trim()){ out.innerHTML = ''; out.hidden = true; return; }
      load().then(function(){
        var res = search(q);
        out.hidden = false;
        if(!res.length){
          out.innerHTML = '<p class="site-search-empty">No matches. Call us at <a href="tel:6612828584">(661) 282-8584</a> and we&rsquo;ll answer your question.</p>';
        } else {
          out.innerHTML = '<ul>' + res.map(function(e, i){
            var snippet = e.t === 'faq' ? e.d : (e.d || e.x);
            if(snippet.length > 170) snippet = snippet.slice(0, 167).replace(/\s+\S*$/, '') + '…';
            var href = e.u === '/' ? 'index.html' : e.u;
            return '<li><a href="' + esc(href) + '" data-rank="' + (i + 1) + '"><span class="ss-type">' + LABEL[e.t] + '</span>'
                 + '<span class="ss-title">' + esc(e.title) + '</span><span class="ss-snip">' + esc(snippet) + '</span></a></li>';
          }).join('') + '</ul>';
        }
        clearTimeout(timer);
        timer = setTimeout(function(){
          var term = clean(q.trim().toLowerCase());
          if(term.length > 2 && term !== lastLogged){ lastLogged = term; track('search', { search_term: term, results: res.length }); }
        }, 1200);
      });
    }
    input.addEventListener('focus', load);
    input.addEventListener('input', function(){ render(input.value); });
    root.addEventListener('submit', function(e){ e.preventDefault(); var first = out.querySelector('a'); if(first) first.click(); });
    out.addEventListener('click', function(e){
      var a = e.target.closest('a[data-rank]');
      if(a) track('search_result_click', { search_term: clean(input.value.trim().toLowerCase()), result_url: a.getAttribute('href'), result_rank: +a.getAttribute('data-rank') });
    });
    root.querySelectorAll('.ss-chip').forEach(function(c){
      c.addEventListener('click', function(){ input.value = c.getAttribute('data-q'); input.focus(); render(input.value); });
    });
    input.addEventListener('keydown', function(e){
      var links = [].slice.call(out.querySelectorAll('a'));
      if(e.key === 'ArrowDown' && links.length){ e.preventDefault(); links[0].focus(); }
    });
    out.addEventListener('keydown', function(e){
      var links = [].slice.call(out.querySelectorAll('a')), i = links.indexOf(document.activeElement);
      if(e.key === 'ArrowDown' && i < links.length - 1){ e.preventDefault(); links[i + 1].focus(); }
      if(e.key === 'ArrowUp'){ e.preventDefault(); (i > 0 ? links[i - 1] : input).focus(); }
    });
    return { input: input, render: render };
  }

  var CHIPS = [['Back pain','back pain'],['Vertigo','dizzy'],['Pelvic health','pelvic floor'],['Kids','pediatric'],['Do I need a referral?','referral'],['Insurance','insurance']];
  function chipsHtml(){ return '<div class="ss-chips">' + CHIPS.map(function(c){ return '<button type="button" class="ss-chip" data-q="' + c[1] + '">' + c[0] + '</button>'; }).join('') + '</div>'; }

  /* homepage inline search */
  var inline = document.querySelector('.site-search-inline');
  if(inline){
    inline.insertAdjacentHTML('beforeend', chipsHtml());
    widget(inline);
  }

  /* header search button -> dialog */
  var btn = document.querySelector('.nav-search');
  var dlg, api, lastFocus;
  function openSearch(){
    if(!dlg){
      dlg = document.createElement('div');
      dlg.className = 'search-dialog'; dlg.hidden = true;
      dlg.innerHTML = '<div class="search-dialog-backdrop" data-close></div>'
        + '<div class="search-dialog-panel" role="dialog" aria-modal="true" aria-label="Search ARI Physical Therapy">'
        + '<form class="site-search" role="search"><div class="ss-row">'
        + '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-search"/></svg>'
        + '<input class="site-search-input" type="search" placeholder="Search conditions, services, questions…" aria-label="Search the site" autocomplete="off">'
        + '<button type="button" class="ss-close" data-close aria-label="Close search">Esc</button></div>'
        + '<div class="site-search-results" hidden></div>' + chipsHtml() + '</form></div>';
      document.body.appendChild(dlg);
      api = widget(dlg.querySelector('.site-search'));
      dlg.addEventListener('click', function(e){ if(e.target.closest('[data-close]')) closeSearch(); });
      dlg.addEventListener('keydown', function(e){
        if(e.key === 'Escape'){ closeSearch(); return; }
        if(e.key === 'Tab'){                     /* keep focus inside the dialog */
          var f = [].slice.call(dlg.querySelectorAll('input, button, a[href]')).filter(function(x){ return x.offsetParent; });
          if(!f.length) return;
          if(e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length-1].focus(); }
          else if(!e.shiftKey && document.activeElement === f[f.length-1]){ e.preventDefault(); f[0].focus(); }
        }
      });
    }
    lastFocus = document.activeElement;
    dlg.hidden = false; document.documentElement.classList.add('search-open');
    btn && btn.setAttribute('aria-expanded', 'true');
    api.input.focus(); load();
  }
  function closeSearch(){
    if(!dlg) return;
    dlg.hidden = true; document.documentElement.classList.remove('search-open');
    btn && btn.setAttribute('aria-expanded', 'false');
    if(lastFocus && lastFocus.focus) lastFocus.focus();
  }
  if(btn) btn.addEventListener('click', openSearch);
  document.addEventListener('keydown', function(e){
    var t = e.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
    if(e.key === '/' && !typing && btn){ e.preventDefault(); openSearch(); }
  });
})();
