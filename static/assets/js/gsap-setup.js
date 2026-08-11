(function () {
  'use strict';

  var CDN_GSAP = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js';
  var CDN_SCROLLTRIGGER = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js';
  var CDN_LENIS = 'https://unpkg.com/lenis@1.1.20/dist/lenis.min.js';

  var _gsap = null;
  var _ScrollTrigger = null;
  var _lenis = null;
  var _initialized = false;
  var _cleanupFns = [];

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (document.querySelector('script[src="' + src + '"]')) {
        resolve();
        return;
      }
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function () {
        reject(new Error('Failed to load script: ' + src));
      };
      document.head.appendChild(script);
    });
  }

  function initLenis(config) {
    if (typeof Lenis === 'undefined') {
      console.warn('Lenis not loaded');
      return null;
    }
    var lenis = new Lenis({
      duration: (config && config.duration) || 1.2,
      easing: (config && config.easing) || function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
      orientation: (config && config.orientation) || 'vertical',
      gestureOrientation: (config && config.gestureOrientation) || 'vertical',
      smoothWheel: (config && config.smoothWheel !== undefined) ? config.smoothWheel : true,
      wheelMultiplier: (config && config.wheelMultiplier) || 1,
      touchMultiplier: (config && config.touchMultiplier) || 1,
      infinite: (config && config.infinite) || false,
    });

    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      lenis.on('scroll', ScrollTrigger.update);
      _cleanupFns.push(function () {
        lenis.destroy();
        if (typeof ScrollTrigger !== 'undefined') {
          ScrollTrigger.getAll().forEach(function (t) { return t.kill(); });
        }
      });
    } else {
      _cleanupFns.push(function () { return lenis.destroy(); });
    }

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    return lenis;
  }

  function parallaxSection(element, speed) {
    if (!element) return null;
    var s = speed || 0.5;
    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: element,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true,
      },
    });
    tl.fromTo(element, { y: function () { return 100 * s; } }, { y: function () { return -100 * s; } });
    _cleanupFns.push(function () { return tl.kill(); });
    return tl;
  }

  function fadeInUp(element, delay, duration) {
    if (!element) return null;
    var d = delay || 0;
    var dur = duration || 0.8;
    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: element,
        start: 'top 90%',
        toggleActions: 'play none none none',
      },
    });
    tl.fromTo(element, { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: dur, delay: d, ease: 'power2.out' });
    _cleanupFns.push(function () { return tl.kill(); });
    return tl;
  }

  function revealText(element) {
    if (!element) return null;
    var text = element.textContent || '';
    var chars = text.split('');
    element.textContent = '';
    var wrapper = document.createElement('span');
    wrapper.style.display = 'inline-block';
    chars.forEach(function (char) {
      var span = document.createElement('span');
      span.textContent = char === ' ' ? '\u00A0' : char;
      span.style.display = 'inline-block';
      span.style.opacity = '0';
      wrapper.appendChild(span);
    });
    element.appendChild(wrapper);

    var spans = wrapper.querySelectorAll('span');
    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: element,
        start: 'top 85%',
        toggleActions: 'play none none none',
      },
    });
    tl.to(spans, {
      opacity: 1,
      duration: 0.03,
      stagger: 0.03,
      ease: 'power2.in',
    });
    _cleanupFns.push(function () { return tl.kill(); });
    return tl;
  }

  function animateCounter(element, target, suffix) {
    if (!element) return null;
    var obj = { val: 0 };
    var suff = suffix || '';
    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: element,
        start: 'top 90%',
        toggleActions: 'play none none none',
      },
    });
    tl.to(obj, {
      val: target,
      duration: 2,
      ease: 'power2.out',
      onUpdate: function () {
        element.textContent = Math.round(obj.val) + suff;
      },
    });
    _cleanupFns.push(function () { return tl.kill(); });
    return tl;
  }

  function tiltCard(element) {
    if (!element) return null;
    function onMove(e) {
      var rect = element.getBoundingClientRect();
      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      var centerX = rect.width / 2;
      var centerY = rect.height / 2;
      var rotateX = ((y - centerY) / centerY) * -10;
      var rotateY = ((x - centerX) / centerX) * 10;
      gsap.to(element, {
        rotationX: rotateX,
        rotationY: rotateY,
        transformPerspective: 800,
        duration: 0.3,
        ease: 'power2.out',
      });
    }
    function onLeave() {
      gsap.to(element, {
        rotationX: 0,
        rotationY: 0,
        duration: 0.5,
        ease: 'power2.out',
      });
    }
    element.addEventListener('mousemove', onMove);
    element.addEventListener('mouseleave', onLeave);
    var cleanup = function () {
      element.removeEventListener('mousemove', onMove);
      element.removeEventListener('mouseleave', onLeave);
    };
    _cleanupFns.push(cleanup);
    return { destroy: cleanup };
  }

  function magneticButton(element) {
    if (!element) return null;
    function onMove(e) {
      var rect = element.getBoundingClientRect();
      var x = e.clientX - rect.left - rect.width / 2;
      var y = e.clientY - rect.top - rect.height / 2;
      gsap.to(element, {
        x: x * 0.3,
        y: y * 0.3,
        duration: 0.3,
        ease: 'power2.out',
      });
    }
    function onLeave() {
      gsap.to(element, {
        x: 0,
        y: 0,
        duration: 0.5,
        ease: 'power2.out',
      });
    }
    element.addEventListener('mousemove', onMove);
    element.addEventListener('mouseleave', onLeave);
    var cleanup = function () {
      element.removeEventListener('mousemove', onMove);
      element.removeEventListener('mouseleave', onLeave);
    };
    _cleanupFns.push(cleanup);
    return { destroy: cleanup };
  }

  function customCursor() {
    var existing = document.querySelector('.advance-custom-cursor');
    if (existing) return existing;

    var cursor = document.createElement('div');
    cursor.className = 'advance-custom-cursor';
    cursor.style.cssText =
      'position:fixed;pointer-events:none;z-index:99999;width:24px;height:24px;border-radius:50%;' +
      'background:rgba(204,0,0,0.4);border:2px solid #CC0000;transform:translate(-50%,-50%);' +
      'transition:width 0.2s,height 0.2s,background 0.2s;left:0;top:0;opacity:0;';

    var dot = document.createElement('div');
    dot.style.cssText =
      'position:absolute;top:50%;left:50%;width:4px;height:4px;border-radius:50%;' +
      'background:#CC0000;transform:translate(-50%,-50%);';
    cursor.appendChild(dot);
    document.body.appendChild(cursor);

    var pos = { x: -100, y: -100 };
    var mouseX = -100;
    var mouseY = -100;

    function onMove(e) {
      mouseX = e.clientX;
      mouseY = e.clientY;
      cursor.style.opacity = '1';
    }
    function onLeaveDoc() {
      cursor.style.opacity = '0';
    }
    function onEnterDoc() {
      cursor.style.opacity = '1';
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseleave', onLeaveDoc);
    document.addEventListener('mouseenter', onEnterDoc);

    function updateCursor() {
      pos.x += (mouseX - pos.x) * 0.15;
      pos.y += (mouseY - pos.y) * 0.15;
      cursor.style.left = pos.x + 'px';
      cursor.style.top = pos.y + 'px';
      requestAnimationFrame(updateCursor);
    }
    requestAnimationFrame(updateCursor);

    var hoverables = document.querySelectorAll('a, button, [data-cursor-hover]');
    function enlarge() {
      cursor.style.width = '48px';
      cursor.style.height = '48px';
      cursor.style.background = 'rgba(204,0,0,0.15)';
    }
    function shrink() {
      cursor.style.width = '24px';
      cursor.style.height = '24px';
      cursor.style.background = 'rgba(204,0,0,0.4)';
    }
    hoverables.forEach(function (el) {
      el.addEventListener('mouseenter', enlarge);
      el.addEventListener('mouseleave', shrink);
    });

    var observer = new MutationObserver(function () {
      document.querySelectorAll('a, button, [data-cursor-hover]').forEach(function (el) {
        el.removeEventListener('mouseenter', enlarge);
        el.removeEventListener('mouseleave', shrink);
        el.addEventListener('mouseenter', enlarge);
        el.addEventListener('mouseleave', shrink);
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });

    var cleanup = function () {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseleave', onLeaveDoc);
      document.removeEventListener('mouseenter', onEnterDoc);
      observer.disconnect();
      if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
    };
    _cleanupFns.push(cleanup);

    return cursor;
  }

  function init(config) {
    if (_initialized) return;
    _initialized = true;

    var loadGSAP = loadScript(CDN_GSAP);
    var loadLenis = loadScript(CDN_LENIS);

    Promise.all([loadGSAP, loadLenis])
      .then(function () {
        return loadScript(CDN_SCROLLTRIGGER);
      })
      .then(function () {
        _gsap = window.gsap;
        _ScrollTrigger = window.ScrollTrigger;

        if (_gsap && _ScrollTrigger) {
          _ScrollTrigger.config({ ignoreMobileResize: true });
        }

        _lenis = initLenis(config);

        console.log('[GSAP Setup] Initialized');
      })
      .catch(function (err) {
        console.error('[GSAP Setup] Failed to load dependencies:', err);
      });
  }

  function destroy() {
    _cleanupFns.forEach(function (fn) {
      try { fn(); } catch (e) { /* silent */ }
    });
    _cleanupFns = [];
    _lenis = null;
    _gsap = null;
    _ScrollTrigger = null;
    _initialized = false;
    console.log('[GSAP Setup] Destroyed');
  }

  window.GSAPSetup = {
    init: init,
    destroy: destroy,
    parallaxSection: parallaxSection,
    fadeInUp: fadeInUp,
    revealText: revealText,
    animateCounter: animateCounter,
    tiltCard: tiltCard,
    magneticButton: magneticButton,
    customCursor: customCursor,
    get lenis() { return _lenis; },
    get gsap() { return _gsap; },
    get ScrollTrigger() { return _ScrollTrigger; },
  };
})();
