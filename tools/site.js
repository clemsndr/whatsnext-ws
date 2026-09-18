(() => {
  const d = document, h = d.documentElement;
  const $ = (s, c = d) => c.querySelector(s);
  const $$ = (s, c = d) => [...c.querySelectorAll(s)];

  // En-tête transparent sur le héros, voilé au défilement
  const hd = $(".site-header");
  if (hd && hd.classList.contains("is-over")) {
    const f = () => hd.classList.toggle("is-scrolled", scrollY > 24);
    f();
    addEventListener("scroll", f, { passive: true });
  }

  // Menu mobile
  const t = $(".nav-toggle");
  if (t) {
    const set = o => { h.classList.toggle("menu-open", o); t.setAttribute("aria-expanded", o); };
    t.addEventListener("click", () => set(!h.classList.contains("menu-open")));
    $$(".site-nav a").forEach(a => a.addEventListener("click", () => set(false)));
    addEventListener("keydown", e => { if (e.key === "Escape" && h.classList.contains("menu-open")) { set(false); t.focus(); } });
    matchMedia("(min-width:900px)").addEventListener("change", () => set(false));
  }

  // Onglets des expertises (fonctionne aussi sans JS : ancres)
  const tabs = $$("[role=tab]");
  if (tabs.length) {
    const sel = (id, keep) => {
      const tab = tabs.find(x => x.hash === "#" + id);
      if (!tab) return false;
      tabs.forEach(x => {
        const on = x === tab;
        x.setAttribute("aria-selected", on);
        x.tabIndex = on ? 0 : -1;
        $(x.hash).classList.toggle("is-active", on);
      });
      tab.scrollIntoView({ block: "nearest", inline: "nearest" });
      if (!keep) history.replaceState(null, "", "#" + id);
      return true;
    };
    tabs.forEach((x, i) => {
      x.addEventListener("click", e => { e.preventDefault(); sel(x.hash.slice(1)); });
      x.addEventListener("keydown", e => {
        const n = tabs.length, k = e.key;
        const j = k === "ArrowDown" || k === "ArrowRight" ? (i + 1) % n : k === "ArrowUp" || k === "ArrowLeft" ? (i - 1 + n) % n : null;
        if (j !== null) { e.preventDefault(); tabs[j].focus(); sel(tabs[j].hash.slice(1)); }
      });
    });
    const fromHash = () => { const id = location.hash.slice(1); if (id) sel(id, true); };
    fromHash();
    addEventListener("hashchange", fromHash);
  }

  // Apparitions discrètes
  const rv = $$(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
    }), { rootMargin: "0px 0px -6% 0px" });
    rv.forEach(el => io.observe(el));
  } else rv.forEach(el => el.classList.add("is-in"));

  // Formulaire de contact -> Google Forms
  const f = $("form[data-gform]");
  if (f) {
    const ok = $("#form-ok"), err = $(".form-error", f), b = $("button[type=submit]", f), lbl = $("span", b);
    f.addEventListener("submit", async e => {
      e.preventDefault();
      if ($(".hp input", f).value) { f.hidden = true; ok.hidden = false; return; }
      const data = new URLSearchParams();
      $$("[name^='entry.']", f).forEach(i => data.append(i.name, i.value.trim()));
      b.disabled = true; err.hidden = true;
      const old = lbl.textContent; lbl.textContent = "Envoi…";
      try {
        await fetch(f.action, { method: "POST", mode: "no-cors", body: data });
        f.reset(); f.hidden = true; ok.hidden = false; ok.focus();
      } catch (_) { err.hidden = false; }
      finally { b.disabled = false; lbl.textContent = old; }
    });
    $("#form-reset").addEventListener("click", () => { ok.hidden = true; f.hidden = false; $("input", f).focus(); });
  }
})();
