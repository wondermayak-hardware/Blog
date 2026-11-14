/* Sidebar (1024px and up): scroll spy, fades out over the footer. Below 1024px the dock is shown instead. */
(function(){
  var side=document.getElementById('sideNav'); if(!side) return;
  var links=[].slice.call(side.querySelectorAll('.side-link'));
  function mark(id){ links.forEach(function(a){ if(a.getAttribute('href')==='#'+id) a.setAttribute('aria-current','true'); else a.removeAttribute('aria-current'); }); }
  var io=new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting) mark(e.target.id); }); },{rootMargin:'-25% 0px -65% 0px'});
  links.forEach(function(a){ var el=document.getElementById(a.getAttribute('href').slice(1)); if(el) io.observe(el); });
  mark('top');
  var tg=document.getElementById('sideToggle');
  links.forEach(function(a,i){ a.style.setProperty('--i',i); var t=a.querySelector('.side-text'); if(t) a.title=t.textContent; });
  var ST=['min','rail','open'],LBL={min:'Show sidebar icons',rail:'Show sidebar labels',open:'Hide sidebar'};
  function state(){ return side.classList.contains('open')?'open':side.classList.contains('min')?'min':'rail'; }
  function setState(n){ side.classList.toggle('min',n==='min'); side.classList.toggle('open',n==='open'); tg.setAttribute('aria-expanded',n==='min'?'false':'true'); tg.setAttribute('aria-label',LBL[n]); tg.title=LBL[n]; }
  setState('min');
  tg.addEventListener('click',function(e){ e.stopPropagation(); setState(ST[(ST.indexOf(state())+1)%3]); });
  document.addEventListener('click',function(e){ if(state()==='open'&&!side.contains(e.target)) setState('rail'); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&state()==='open'){ setState('rail'); tg.focus(); } });
  var ft=document.querySelector('footer.wmf');
  if(ft) new IntersectionObserver(function(es){ side.classList.toggle('gone',es[0].isIntersecting); }).observe(ft);
  /* back to top (mobile): appears after scrolling */
  var tt=document.getElementById('toTop');
  if(tt){ var tk=false; function chk(){ tt.classList.toggle('show',window.pageYOffset>400); tk=false; }
    window.addEventListener('scroll',function(){ if(!tk){ tk=true; requestAnimationFrame(chk); } },{passive:true}); chk(); }
})();
