class GitHubCopilotPricingPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    const signature = this.entities.map((state) => `${state.entity_id}:${state.state}`).join("|");
    if (signature !== this._signature) {
      this._signature = signature;
      this.render();
    }
  }

  connectedCallback() {
    this.innerHTML = `
      <style>
        :host { display: block; min-height: 100%; background: var(--primary-background-color); color: var(--primary-text-color); }
        main { max-width: 1500px; margin: auto; padding: 24px; }
        header { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin-bottom: 18px; }
        h1 { margin: 0; font-size: clamp(28px, 3vw, 42px); letter-spacing: -0.04em; }
        p { color: var(--secondary-text-color); margin: 4px 0 0; }
        select { color: inherit; background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 8px; padding: 7px 10px; }
        #models { display: grid; gap: 18px; }
        .provider-group h2 { font-size: 14px; margin: 0 0 7px 2px; text-transform: capitalize; }
        .provider-models { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px; }
        article { background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 10px; box-shadow: var(--ha-card-box-shadow); overflow: hidden; }
        .title { display: flex; justify-content: space-between; align-items: start; gap: 8px; }
        .card-header { padding: 8px 10px; }
        article h3 { margin: 0; font-size: 14px; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .indicator { border-radius: 999px; flex: none; font-size: 10px; font-weight: 600; padding: 3px 7px; }
        .tags { display: flex; gap: 4px; }
        .promo { background: color-mix(in srgb, var(--accent-color, #7e57c2) 18%, transparent); color: var(--accent-color, #6a1b9a); }
        .cheap { background: color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); color: var(--success-color, #2e7d32); }
        .average { background: color-mix(in srgb, var(--warning-color, #f9a825) 20%, transparent); color: var(--warning-color, #9a6700); }
        .expensive { background: color-mix(in srgb, var(--error-color, #db4437) 16%, transparent); color: var(--error-color, #c62828); }
        .prices { border-top: 1px solid var(--divider-color); }
        .price { align-items: center; cursor: pointer; display: grid; grid-template-columns: max-content minmax(16px, 1fr) 62px 58px; column-gap: 8px; min-height: 29px; padding: 2px 10px; }
        .price:hover, .price:focus-visible { background: color-mix(in srgb, var(--primary-color) 7%, transparent); outline: none; }
        .price + .price { border-top: 1px solid color-mix(in srgb, var(--divider-color) 55%, transparent); }
        .label { color: var(--secondary-text-color); font-size: 10px; white-space: nowrap; }
        .value { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; text-align: right; }
        .price .indicator { box-sizing: border-box; font-size: 9px; padding: 2px 5px; text-align: center; width: 58px; }
        svg { width: 100%; height: 18px; overflow: visible; }
        polyline { fill: none; stroke: var(--primary-color); stroke-width: 2; vector-effect: non-scaling-stroke; }
        .empty { grid-column: 1 / -1; padding: 64px; text-align: center; color: var(--secondary-text-color); }
        @media (max-width: 600px) { main { padding: 16px 10px; } header { align-items: start; flex-direction: column; } }
      </style>
      <main>
        <header><div><h1>Copilot Pricing</h1><p>USD per million tokens</p></div><select id="range"><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option></select></header>
        <section id="models"></section>
      </main>`;
    this.querySelector("#range").addEventListener("change", () => this.loadHistory());
    this.querySelector("#models").addEventListener("click", (event) => this.openEntity(event));
    this.querySelector("#models").addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") this.openEntity(event);
    });
    this.render();
  }

  get entities() {
    return Object.values(this._hass?.states || {}).filter(
      (state) => state.attributes.source === "GitHub Copilot"
    );
  }

  render() {
    const target = this.querySelector("#models");
    if (!target || !this._hass) return;
    const models = this.entities.reduce((result, state) => {
      const key = `${state.attributes.provider}|${state.attributes.model}`;
      result.set(key, [...(result.get(key) || []), state]);
      return result;
    }, new Map());
    const { overall, prices } = this.priceIndicators(models);
    const providers = [...models].reduce((result, [key, states]) => {
      const provider = key.split("|")[0];
      result.set(provider, [...(result.get(provider) || []), [key, states]]);
      return result;
    }, new Map());
    target.innerHTML = [...providers].map(([provider, providerModels]) => `<section class="provider-group"><h2>${this.escape(provider)}</h2><div class="provider-models">${providerModels.map(([key, states]) => {
      const model = key.split("|")[1], indicator = overall.get(key);
      const promo = states.some((state) => state.attributes.promotion);
      return `<article><div class="card-header title"><h3 title="${this.escape(model)}">${this.escape(model)}</h3><span class="tags">${promo ? '<span class="indicator promo">Promo</span>' : ""}<span class="indicator ${indicator.toLowerCase()}">${indicator}</span></span></div><div class="prices">${states.map((state) => { const priceIndicator = prices.get(state.entity_id); return `<div class="price" data-entity="${state.entity_id}" role="button" tabindex="0"><span class="label">${this.escape(this.priceField(state))}</span><svg viewBox="0 0 100 18" preserveAspectRatio="none"><polyline></polyline></svg><span class="value">$${this.escape(state.state)}</span><span class="indicator ${priceIndicator.toLowerCase()}">${priceIndicator}</span></div>`; }).join("")}</div></article>`;
    }).join("")}</div></section>`).join("") || '<div class="empty">No pricing sensors found.</div>';
    this.loadHistory();
  }

  priceField(state) {
    return state.attributes.friendly_name.split(" — ").at(-1);
  }

  openEntity(event) {
    const row = event.target.closest(".price[data-entity]");
    if (!row) return;
    event.preventDefault();
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId: row.dataset.entity },
      bubbles: true,
      composed: true,
    }));
  }

  priceIndicators(models) {
    const averages = new Map([...models].map(([key, states]) => {
      const fields = states.reduce((result, state) => {
        const field = this.priceField(state), price = Number(state.state);
        if (Number.isFinite(price)) result.set(field, [...(result.get(field) || []), price]);
        return result;
      }, new Map());
      return [key, new Map([...fields].map(([field, prices]) => [field, prices.reduce((sum, price) => sum + price, 0) / prices.length]))];
    }));
    const fields = new Set([...averages.values()].flatMap((prices) => [...prices.keys()]));
    const benchmarks = new Map([...fields].map((field) => [field, [...averages.values()].map((prices) => prices.get(field)).filter(Number.isFinite).sort((a, b) => a - b)]));
    const rank = (field, price) => {
        const values = benchmarks.get(field);
        const lower = values.filter((value) => value < price).length;
        const equal = values.filter((value) => value === price).length;
        return values.length < 2 ? 0.5 : (lower + (equal - 1) / 2) / (values.length - 1);
    };
    const label = (score) => score < 1 / 3 ? "Cheap" : score > 2 / 3 ? "Expensive" : "Average";
    const overall = new Map([...averages].map(([key, prices]) => {
      const ranks = [...prices].map(([field, price]) => rank(field, price));
      const score = ranks.reduce((sum, rank) => sum + rank, 0) / ranks.length;
      return [key, label(score)];
    }));
    const prices = new Map([...models.values()].flatMap((states) => states.map((state) => [state.entity_id, label(rank(this.priceField(state), Number(state.state)))])));
    return { overall, prices };
  }

  async loadHistory() {
    const charts = [...this.querySelectorAll(".price[data-entity] svg")];
    if (!charts.length) return;
    const days = Number(this.querySelector("#range")?.value || 7);
    const start = new Date(Date.now() - days * 86400000).toISOString();
    const ids = charts.map((chart) => chart.closest(".price").dataset.entity).join(",");
    try {
      const history = await this._hass.callApi("GET", `history/period/${start}?filter_entity_id=${ids}&minimal_response&no_attributes`);
      const byId = new Map(history.map((series) => [series[0]?.entity_id, series]));
      for (const chart of charts) this.draw(chart, byId.get(chart.closest(".price").dataset.entity) || []);
    } catch (_) {
      // Recorder/history may be disabled; current prices remain useful.
    }
  }

  draw(chart, series) {
    const values = series.map((point) => Number(point.state)).filter(Number.isFinite);
    if (values.length < 2) return;
    const min = Math.min(...values), span = Math.max(...values) - min || 1;
    chart.querySelector("polyline").setAttribute("points", values.map((value, index) => `${index * 100 / (values.length - 1)},${17 - (value - min) * 16 / span}`).join(" "));
  }

  escape(value) {
    const node = document.createElement("span");
    node.textContent = value ?? "";
    return node.innerHTML;
  }
}

customElements.define("github-copilot-pricing-panel", GitHubCopilotPricingPanel);
