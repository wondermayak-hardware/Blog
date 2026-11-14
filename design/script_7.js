/* header hides on scroll down, returns on scroll up */
(function(){var n=document.querySelector('.nav');if(!n)return;var l=window.scrollY,t=false;
function f(){var y=window.scrollY,d=y-l;if(Math.abs(d)>6){n.classList.toggle('up',d>0&&y>120);l=y;if(n.classList.contains('up')){var m=document.getElementById('mobileMenu'),h=document.getElementById('hamBtn');if(m&&m.classList.contains('open')&&h)h.click()}}
if(y<40)n.classList.remove('up');t=false}
window.addEventListener('scroll',function(){if(!t){t=true;requestAnimationFrame(f)}},{passive:true})})();
