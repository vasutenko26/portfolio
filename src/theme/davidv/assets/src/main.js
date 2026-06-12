import './main.css';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

const html = document.documentElement;
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---- Живые часы в панели мониторинга ---- */
const clockEl = document.querySelector('[data-clock]');
function tick() {
	if (!clockEl) return;
	const d = new Date();
	clockEl.textContent = [d.getHours(), d.getMinutes(), d.getSeconds()]
		.map((n) => String(n).padStart(2, '0')).join(':');
}
if (clockEl) { tick(); setInterval(tick, 1000); }

/* ---- Прилипающий хедер ---- */
const header = document.querySelector('[data-header]');
if (header) {
	const onScroll = () => header.classList.toggle('is-stuck', window.scrollY > 8);
	onScroll();
	window.addEventListener('scroll', onScroll, { passive: true });
}

/* ---- Контактная форма → webhook n8n ---- */
const cform = document.querySelector('[data-cform]');
if (cform) {
	const status = cform.querySelector('[data-cform-status]');
	const btn = cform.querySelector('button[type="submit"]');
	cform.addEventListener('submit', async (e) => {
		e.preventDefault();
		const data = Object.fromEntries(new FormData(cform).entries());
		btn.disabled = true;
		status.className = 'cform__status';
		status.textContent = cform.dataset.sending || 'Sending…';
		try {
			const r = await fetch(cform.action, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(data),
			});
			const j = await r.json().catch(() => ({ ok: false }));
			if (r.ok && j.ok) {
				cform.reset();
				status.textContent = cform.dataset.ok;
				status.classList.add('is-ok');
			} else {
				status.textContent = cform.dataset.err;
				status.classList.add('is-err');
			}
		} catch (_) {
			status.textContent = cform.dataset.err;
			status.classList.add('is-err');
		} finally {
			btn.disabled = false;
		}
	});
}

/* ---- Текст команды ---- */
const typed = document.querySelector('[data-typed]');
const typedText = typed ? (typed.dataset.text || typed.textContent.trim()) : '';

/* =========================================================================
   Без анимаций (reduced-motion): показываем финальное состояние сразу
   ========================================================================= */
if (reduce) {
	if (typed) typed.textContent = typedText;
	document.querySelectorAll('[data-svc]').forEach((s) => s.classList.add('is-up'));
} else {
	html.classList.add('anim-on');
	gsap.registerPlugin(ScrollTrigger);

	// Фолбэк: если интро не отработало за 5с — снимаем скрытие, чтобы контент не пропал
	const failsafe = setTimeout(() => {
		if (!html.classList.contains('intro-done')) html.classList.remove('anim-on');
	}, 5000);

	const start = () => {
		try { runIntro(); } catch (e) { html.classList.remove('anim-on'); }
		clearTimeout(failsafe);
	};
	(document.fonts ? document.fonts.ready : Promise.resolve()).then(start);
	// на всякий случай — и по load
	window.addEventListener('load', () => { if (!html.classList.contains('intro-started')) start(); });

	initScrollReveals();
	initSmoothScroll();
}

/* ---- Печать строки ---- */
function typeLine(el, text, speed = 36) {
	return new Promise((res) => {
		el.textContent = '';
		let i = 0;
		const id = setInterval(() => {
			el.textContent += text[i++] || '';
			if (i >= text.length) { clearInterval(id); res(); }
		}, speed);
	});
}

/* ---- Сигнатурная загрузка героя ---- */
function runIntro() {
	if (html.classList.contains('intro-started')) return;
	html.classList.add('intro-started');

	gsap.from('.monitor', { opacity: 0, y: 26, duration: .8, ease: 'power3.out' });

	const tl = gsap.timeline({ onComplete: () => html.classList.add('intro-done') });
	tl.to('.hero__title [data-word]', { y: '0%', opacity: 1, duration: .85, stagger: .045, ease: 'power3.out' }, .15)
	  .to('.hero .reveal', { y: 0, opacity: 1, duration: .6, stagger: .09, ease: 'power2.out' }, .35);

	// печать команды
	if (typed) tl.add(() => typeLine(typed, typedText), .55);

	// сервисы загораются по очереди
	const svcs = gsap.utils.toArray('[data-svc]');
	svcs.forEach((s, i) => {
		gsap.delayedCall(1.25 + i * 0.16, () => s.classList.add('is-up'));
	});

	// рисуем спарклайн
	const spark = document.querySelector('[data-spark]');
	if (spark && spark.getTotalLength) {
		const len = spark.getTotalLength();
		gsap.set(spark, { strokeDasharray: len, strokeDashoffset: len });
		gsap.to(spark, { strokeDashoffset: 0, duration: 1.5, ease: 'power2.inOut', delay: 1.0 });
	}
}

/* ---- Появление секций по скроллу ---- */
function initScrollReveals() {
	const items = gsap.utils.toArray('[data-reveal]').filter((el) => !el.closest('.hero'));
	items.forEach((el) => {
		gsap.to(el, {
			y: 0, opacity: 1, duration: .7, ease: 'power2.out',
			scrollTrigger: { trigger: el, start: 'top 86%', once: true },
		});
	});
}

/* ---- Плавный скролл (Lenis) ---- */
function initSmoothScroll() {
	const lenis = new Lenis({ duration: 1.1, smoothWheel: true, wheelMultiplier: 1 });
	html.classList.add('is-lenis');
	lenis.on('scroll', ScrollTrigger.update);
	gsap.ticker.add((t) => lenis.raf(t * 1000));
	gsap.ticker.lagSmoothing(0);

	// якорные ссылки через Lenis
	document.querySelectorAll('a[href^="#"], a[href*="/#"]').forEach((a) => {
		a.addEventListener('click', (e) => {
			const url = new URL(a.getAttribute('href'), location.href);
			if (url.pathname.replace(/\/$/, '') === location.pathname.replace(/\/$/, '') && url.hash) {
				const target = document.querySelector(url.hash);
				if (target) { e.preventDefault(); lenis.scrollTo(target, { offset: -70 }); }
			}
		});
	});
}
