(function(){
  /* ---------- LOADER ---------- */
  var loader=document.getElementById('loader');
  function hideLoader(){ if(loader) loader.classList.add('hide'); }
  window.addEventListener('DOMContentLoaded',function(){ setTimeout(hideLoader,200); });
  setTimeout(hideLoader,1500);

  /* ---------- THEME ---------- */
  var root=document.documentElement;
  var themeBtn=document.getElementById('themeBtn');
  var sun=document.getElementById('themeIconSun');
  var moon=document.getElementById('themeIconMoon');
  function syncIcons(){ var dark=document.documentElement.getAttribute('data-theme')==='dark'; themeBtn.setAttribute('aria-pressed',dark?'true':'false'); }
  syncIcons();
  themeBtn.addEventListener('click',function(){
    var de=document.documentElement,next=de.getAttribute('data-theme')==='dark'?'light':'dark';
    function apply(){ de.setAttribute('data-theme',next); try{ localStorage.setItem('theme',next); }catch(e){} var mt=document.getElementById('metaTheme'); if(mt) mt.setAttribute('content',next==='dark'?'#9A7AFB':'#70A1FC'); var ms=document.getElementById('metaScheme'); if(ms) ms.setAttribute('content',next); syncIcons(); }
    var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
    if(!document.startViewTransition||reduce){ apply(); return; }
    var r=themeBtn.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;
    var rad=Math.hypot(Math.max(x,innerWidth-x),Math.max(y,innerHeight-y));
    de.classList.add('theme-swap');
    var t=document.startViewTransition(apply);
    t.ready.then(function(){ de.animate({clipPath:['circle(0px at '+x+'px '+y+'px)','circle('+rad+'px at '+x+'px '+y+'px)']},{duration:650,easing:'cubic-bezier(.4,0,.2,1)',pseudoElement:'::view-transition-new(root)'}); });
    t.finished.then(function(){ de.classList.remove('theme-swap'); },function(){ de.classList.remove('theme-swap'); });
  });

  /* ---------- MOBILE MENU ---------- */
  var ham=document.getElementById('hamBtn');
  var menu=document.getElementById('mobileMenu');
  ham.addEventListener('click',function(){
    var open=menu.classList.toggle('open');
    ham.setAttribute('aria-expanded',open?'true':'false');
  });
  menu.querySelectorAll('a').forEach(function(a){
    a.addEventListener('click',function(){
      menu.classList.remove('open');
      ham.setAttribute('aria-expanded','false');
    });
  });

  /* ---------- TOAST ---------- */
  var toast=document.getElementById('toast'),toastT;
  function say(msg){
    toast.textContent=msg;
    toast.classList.add('show');
    clearTimeout(toastT);
    toastT=setTimeout(function(){ toast.classList.remove('show'); },1600);
  }

  /* ---------- TOOL DOCK + QUICK/DEEP ---------- */
  var chips=[].slice.call(document.querySelectorAll('#modeDock .mode-chip'));
  var panes={topic:'pane-topic',paste:'pane-paste',image:'pane-image',pdf:'pane-pdf',youtube:'pane-youtube'};
  var depth='deep';
  var genLabel=document.getElementById('generateLabel');

  function setMode(mode){
    chips.forEach(function(c){
      var on=c.getAttribute('data-mode')===mode;
      c.classList.toggle('active',on);
      c.setAttribute('aria-selected',on?'true':'false');
    });
    Object.keys(panes).forEach(function(k){
      document.getElementById(panes[k]).classList.toggle('active',k===mode);
    });
  }
  chips.forEach(function(c){
    c.addEventListener('click',function(){ setMode(c.getAttribute('data-mode')); });
  });

  var depthBtns=[].slice.call(document.querySelectorAll('#depthSeg .depth-chip'));
  function setDepth(d){
    depth=d;
    depthBtns.forEach(function(b){
      var on=b.getAttribute('data-depth')===d;
      b.classList.toggle('active',on);
      b.setAttribute('aria-pressed',on?'true':'false');
    });
    genLabel.textContent='Generate '+d+' mind map';
  }
  depthBtns.forEach(function(b){
    b.addEventListener('click',function(){ setDepth(b.getAttribute('data-depth')); });
  });

  /* generate demo */
  var gen=document.getElementById('generateBtn');
  var prog=document.getElementById('genProgress');
  gen.addEventListener('click',function(){
    if(gen.disabled) return;
    gen.disabled=true;
    prog.hidden=false;
    genLabel.textContent='Generating...';
    setTimeout(function(){
      prog.hidden=true;
      gen.disabled=false;
      setDepth(depth);
      say('Demo only: nothing was generated');
    },1400);
  });

  /* paste counter */
  var paste=document.getElementById('pasteInput');
  var pbar=document.getElementById('pasteBar');
  var pcount=document.getElementById('pasteCount');
  paste.addEventListener('input',function(){
    var n=paste.value.length;
    pcount.textContent=n+' / 6000';
    pbar.style.width=Math.min(100,n/60)+'%';
  });

  /* youtube validate */
  var yt=document.getElementById('ytInput');
  var ytHint=document.getElementById('ytHint');
  document.getElementById('ytFetch').addEventListener('click',function(){
    var ok=/^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{6,}/.test(yt.value.trim());
    yt.classList.toggle('is-error',!ok);
    yt.classList.toggle('is-success',ok);
    ytHint.className='hint '+(ok?'ok':'err');
    ytHint.textContent=ok?'Link looks good. Captions would be fetched here.':'Please paste a valid YouTube link.';
  });

  /* ---------- FILE DROPS ---------- */
  function fmt(b){
    if(b<1024) return b+' B';
    if(b<1048576) return (b/1024).toFixed(1)+' KB';
    return (b/1048576).toFixed(1)+' MB';
  }
  function wireDrop(cfg){
    var drop=document.getElementById(cfg.drop);
    var input=document.getElementById(cfg.input);
    var nameEl=document.getElementById(cfg.name);
    var pv=document.getElementById(cfg.preview);
    var pvName=document.getElementById(cfg.pvName);
    var pvSize=document.getElementById(cfg.pvSize);
    var rm=document.getElementById(cfg.remove);
    var url='';

    function clear(){
      input.value='';
      nameEl.textContent='';
      pv.classList.remove('show');
      if(cfg.img) cfg.img.removeAttribute('src');
      if(url){ URL.revokeObjectURL(url); url=''; }
    }
    function show(file){
      if(!file || !cfg.ok(file)){
        nameEl.textContent='';
        say(cfg.error);
        return;
      }
      if(url){ URL.revokeObjectURL(url); url=''; }
      nameEl.textContent=file.name;
      pvName.textContent=file.name;
      pvSize.textContent=fmt(file.size);
      if(cfg.img){ url=URL.createObjectURL(file); cfg.img.src=url; }
      pv.classList.add('show');
    }
    drop.addEventListener('click',function(){ input.click(); });
    drop.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); }
    });
    input.addEventListener('change',function(){ show(input.files&&input.files[0]); });
    ['dragenter','dragover'].forEach(function(t){
      drop.addEventListener(t,function(e){ e.preventDefault(); e.stopPropagation(); drop.classList.add('dragover'); });
    });
    ['dragleave','drop'].forEach(function(t){
      drop.addEventListener(t,function(e){ e.preventDefault(); e.stopPropagation(); drop.classList.remove('dragover'); });
    });
    drop.addEventListener('drop',function(e){
      var f=e.dataTransfer.files&&e.dataTransfer.files[0];
      if(f){
        try{ var dt=new DataTransfer(); dt.items.add(f); input.files=dt.files; }catch(err){}
        show(f);
      }
    });
    rm.addEventListener('click',clear);
  }
  wireDrop({
    drop:'imageDrop',input:'imageInput',name:'imageName',preview:'imagePreview',
    pvName:'imagePvName',pvSize:'imagePvSize',remove:'imageRemove',
    img:document.getElementById('previewImage'),
    ok:function(f){ return f.type.indexOf('image/')===0; },
    error:'Please choose a valid image (JPG, PNG or WebP).'
  });
  wireDrop({
    drop:'pdfDrop',input:'pdfInput',name:'pdfName',preview:'pdfPreview',
    pvName:'pdfPvName',pvSize:'pdfPvSize',remove:'pdfRemove',
    ok:function(f){ return f.type==='application/pdf'||/\.pdf$/i.test(f.name); },
    error:'Please choose a PDF file.'
  });

  /* ---------- CHIPS + TABS DEMO ---------- */
  function exclusive(sel,cls){
    var items=[].slice.call(document.querySelectorAll(sel));
    items.forEach(function(el){
      el.addEventListener('click',function(){
        items.forEach(function(o){ o.classList.remove(cls); });
        el.classList.add(cls);
      });
    });
  }
  exclusive('.chip-filter','active');
  exclusive('#demoTabs .tab','active');
  var modeChips=[].slice.call(document.querySelectorAll('.chip-row .chip:not(.chip-filter)'));
  modeChips.forEach(function(c){ c.addEventListener('click',function(){ c.classList.toggle('active'); }); });

  /* ---------- COPY SWATCH HEX ---------- */
  document.querySelectorAll('.sw').forEach(function(s){
    s.addEventListener('click',function(){
      var hex=s.getAttribute('data-copy');
      function done(){ say('Copied '+hex); }
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(hex).then(done,done);
      }else{ done(); }
    });
  });

  /* ---------- ICON LIBRARY: SEARCH + COPY SVG ---------- */
  (function(){
    var tiles=[].slice.call(document.querySelectorAll('.ic-tile'));
    if(!tiles.length) return;
    var attrs='xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';
    tiles.forEach(function(t){
      t.addEventListener('click',function(){
        var code='<svg '+attrs+'>'+t.querySelector('svg').innerHTML+'</svg>';
        var name=t.getAttribute('data-icon');
        function done(){ say('Copied '+name+' SVG'); }
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(code).then(done,done);
        }else{ done(); }
      });
    });
    var box=document.getElementById('iconSearch');
    var empty=document.getElementById('iconEmpty');
    var blocks=[].slice.call(document.querySelectorAll('.ic-block'));
    if(box){
      box.addEventListener('input',function(){
        var q=box.value.trim().toLowerCase().replace(/\s+/g,'-');
        var shown=0;
        tiles.forEach(function(t){
          var hit=!q||t.getAttribute('data-icon').indexOf(q)!==-1;
          t.hidden=!hit; if(hit) shown++;
        });
        blocks.forEach(function(b){
          b.hidden=!b.querySelector('.ic-tile:not([hidden])');
        });
        if(empty) empty.hidden=shown!==0;
      });
    }
  })();

  /* ---------- BOTTOM DOCK ---------- */
  var dock=document.querySelector('.dock');
  var ind=dock.querySelector('.dock-indicator');
  var btns=[].slice.call(dock.querySelectorAll('.dock-btn'));
  var active=btns.filter(function(b){ return b.getAttribute('aria-current')==='page'; })[0]||btns[3];
  function x(b){ return b.offsetLeft+(b.offsetWidth-ind.offsetWidth)/2; }
  function place(){ ind.style.setProperty('--dx',x(active)+'px'); }
  ind.classList.add('no-anim'); place(); void ind.offsetWidth; ind.classList.remove('no-anim');
  requestAnimationFrame(function(){ requestAnimationFrame(place); });
  window.addEventListener('resize',place);
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(place);

  var dockToMode={pdf:'pdf',youtube:'youtube',url:'paste',topic:'topic',ocr:'image',presets:'topic',save:'topic'};
  btns.forEach(function(b){
    b.addEventListener('pointerdown',function(){
      var r=document.createElement('span');
      r.className='dock-ripple';
      b.appendChild(r);
      setTimeout(function(){ r.remove(); },600);
    });
    b.addEventListener('click',function(){
      btns.forEach(function(o){ o.removeAttribute('aria-current'); });
      b.setAttribute('aria-current','page');
      active=b;
      place();
      var m=dockToMode[b.getAttribute('data-tab')];
      if(m) setMode(m);
    });
  });

  /* hide dock while scrolling down, show on scroll up or at the end */
  var lastY=window.pageYOffset,tick=false;
  window.addEventListener('scroll',function(){
    if(tick) return;
    tick=true;
    requestAnimationFrame(function(){
      var y=window.pageYOffset,d=y-lastY;
      if(Math.abs(d)>8){ dock.classList.toggle('hide',d>0&&y>160); lastY=y; }
      if((window.innerHeight+y)>=document.documentElement.scrollHeight-4) dock.classList.remove('hide');
      tick=false;
    });
  },{passive:true});
})();
