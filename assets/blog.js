/* ThunderStudy Blog: dock, count-up, copy link, search */
(function(){
  var dock=document.querySelector('.dock');
  if(dock){
    var ind=dock.querySelector('.dock-indicator'),btns=[].slice.call(dock.querySelectorAll('.dock-btn'));
    var active=btns.filter(function(b){return b.getAttribute('aria-current')==='page';})[0]||btns[0];
    function place(){ind.style.setProperty('--dx',(active.offsetLeft+(active.offsetWidth-ind.offsetWidth)/2)+'px');}
    ind.classList.add('no-anim');place();void ind.offsetWidth;ind.classList.remove('no-anim');
    requestAnimationFrame(function(){requestAnimationFrame(place);});
    addEventListener('resize',place);if(document.fonts&&document.fonts.ready)document.fonts.ready.then(place);
    btns.forEach(function(b){b.addEventListener('pointerdown',function(){var r=document.createElement('span');r.className='dock-ripple';b.appendChild(r);setTimeout(function(){r.remove();},600);});});
    var lastY=pageYOffset,tick=false;
    addEventListener('scroll',function(){if(tick)return;tick=true;requestAnimationFrame(function(){var y=pageYOffset,d=y-lastY;if(Math.abs(d)>8){dock.classList.toggle('hide',d>0&&y>160);lastY=y;}
      if(innerHeight+y>=document.documentElement.scrollHeight-4)dock.classList.remove('hide');tick=false;});},{passive:true});
  }
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  [].slice.call(document.querySelectorAll('[data-to]')).forEach(function(el){
    var to=+el.getAttribute('data-to');if(reduce||!to)return;el.textContent='0';
    new IntersectionObserver(function(es,o){if(!es[0].isIntersecting)return;o.disconnect();var t0=performance.now();
      (function s(t){var p=Math.min(1,(t-t0)/900);el.textContent=Math.round(to*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(s);})(t0);}).observe(el);});
  [].slice.call(document.querySelectorAll('[data-copy]')).forEach(function(b){b.addEventListener('click',function(){
    var u=b.getAttribute('data-copy');function ok(){var t=b.textContent;b.textContent='Copied';setTimeout(function(){b.textContent=t;},1600);}
    if(navigator.clipboard)navigator.clipboard.writeText(u).then(ok,function(){});else{var i=document.createElement('input');i.value=u;document.body.appendChild(i);i.select();try{document.execCommand('copy');ok();}catch(e){}i.remove();}});});
  var f=document.getElementById('sq');
  if(f){
    var out=document.getElementById('sres'),st=document.getElementById('sstat'),data=null;
    function norm(s){return s.toLowerCase().replace(/[^a-z0-9 ]+/g,' ');}
    function run(){
      var raw=f.value.trim(),q=norm(raw).trim();
      try{history.replaceState(null,'',raw?'?q='+encodeURIComponent(raw):location.pathname);}catch(e){}
      out.textContent='';
      if(!q){st.textContent='Type a word to search all posts.';return;}
      var terms=q.split(/\s+/),res=[];
      data.forEach(function(d){var t=norm(d[0]+' '+d[2]),sc=0;for(var i=0;i<terms.length;i++){if(t.indexOf(terms[i])<0){sc=-1;break;}sc+=norm(d[0]).indexOf(terms[i])>=0?2:1;}if(sc>0)res.push([sc,d]);});
      res.sort(function(a,b){return b[0]-a[0]||(a[1][3]<b[1][3]?1:-1);});
      st.textContent=res.length?res.length+' post'+(res.length>1?'s':'')+' found.':'No posts found. Try a shorter word.';
      res.slice(0,30).forEach(function(r){var a=document.createElement('a');a.className='sitem';a.href=r[1][1];var b=document.createElement('b');b.textContent=r[1][0];var s=document.createElement('small');s.textContent=r[1][2]+' · '+r[1][3];a.appendChild(b);a.appendChild(s);out.appendChild(a);});
    }
    fetch('/search.json').then(function(r){return r.json();}).then(function(d){data=d;var p=new URLSearchParams(location.search).get('q');if(p){f.value=p;}run();f.addEventListener('input',run);}).catch(function(){st.textContent='Search is unavailable right now.';});
  }
})();
