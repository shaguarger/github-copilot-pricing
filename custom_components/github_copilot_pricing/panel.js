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
        #models { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; }
        article { background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 12px; padding: 14px; box-shadow: var(--ha-card-box-shadow); }
        .title { display: flex; justify-content: space-between; align-items: start; gap: 8px; }
        article h2 { margin: 0; font-size: 17px; line-height: 1.2; }
        .provider { color: var(--secondary-text-color); font-size: 10px; text-transform: uppercase; letter-spacing: .1em; }
        .indicator { border-radius: 999px; flex: none; font-size: 10px; font-weight: 600; padding: 3px 7px; }
        .cheap { background: color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); color: var(--success-color, #2e7d32); }
        .average { background: color-mix(in srgb, var(--warning-color, #f9a825) 20%, transparent); color: var(--warning-color, #9a6700); }
        .expensive { background: color-mix(in srgb, var(--error-color, #db4437) 16%, transparent); color: var(--error-color, #c62828); }
        .prices { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px; }
        .label { color: var(--secondary-text-color); font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .value { font-size: 18px; font-variant-numeric: tabular-nums; margin-top: 1px; }
        svg { width: 100%; height: 24px; margin-top: 3px; overflow: visible; }
        polyline { fill: none; stroke: var(--primary-color); stroke-width: 2; vector-effect: non-scaling-stroke; }
        .empty { grid-column: 1 / -1; padding: 64px; text-align: center; color: var(--secondary-text-color); }
        @media (max-width: 600px) { main { padding: 16px 10px; } header { align-items: start; flex-direction: column; } }
      </style>
      <main>
        <header><div><h1>Copilot Pricing</h1><p>USD per million tokens</p></div><select id="range"><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option></select></header>
        <section id="models"></section>
      </main>`;
    this.querySelector("#range").addEventListener("change", () => this.loadHistory());
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
    const indicators = this.priceIndicators(models);
    target.innerHTML = [...models.entries()].map(([key, states]) => {
      const [provider, model] = key.split("|");
      const indicator = indicators.get(key);
      return `<article><span class="provider">${this.escape(provider)}</span><div class="title"><h2>${this.escape(model)}</h2><span class="indicator ${indicator.toLowerCase()}">${indicator}</span></div><div class="prices">${states.map((state) => `<div><div class="label">${this.escape(this.priceField(state))}</div><div class="value">$${this.escape(state.state)}</div><svg viewBox="0 0 100 24" preserveAspectRatio="none" data-entity="${state.entity_id}"><polyline></polyline></svg></div>`).join("")}</div></article>`;
    }).join("") || '<div class="empty">No pricing sensors found.</div>';
    this.loadHistory();
  }

  priceField(state) {
    return state.attributes.friendly_name.split(" — ").at(-1);
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
    return new Map([...averages].map(([key, prices]) => {
      const ranks = [...prices].map(([field, price]) => {
        const values = benchmarks.get(field);
        const lower = values.filter((value) => value < price).length;
        const equal = values.filter((value) => value === price).length;
        return values.length < 2 ? 0.5 : (lower + (equal - 1) / 2) / (values.length - 1);
      });
      const score = ranks.reduce((sum, rank) => sum + rank, 0) / ranks.length;
      return [key, score < 1 / 3 ? "Cheap" : score > 2 / 3 ? "Expensive" : "Average"];
    }));
  }

  async loadHistory() {
    const charts = [...this.querySelectorAll("svg[data-entity]")];
    if (!charts.length) return;
    const days = Number(this.querySelector("#range")?.value || 7);
    const start = new Date(Date.now() - days * 86400000).toISOString();
    const ids = charts.map((chart) => chart.dataset.entity).join(",");
    try {
      const history = await this._hass.callApi("GET", `history/period/${start}?filter_entity_id=${ids}&minimal_response&no_attributes`);
      const byId = new Map(history.map((series) => [series[0]?.entity_id, series]));
      for (const chart of charts) this.draw(chart, byId.get(chart.dataset.entity) || []);
    } catch (_) {
      // Recorder/history may be disabled; current prices remain useful.
    }
  }

  draw(chart, series) {
    const values = series.map((point) => Number(point.state)).filter(Number.isFinite);
    if (values.length < 2) return;
    const min = Math.min(...values), span = Math.max(...values) - min || 1;
    chart.querySelector("polyline").setAttribute("points", values.map((value, index) => `${index * 100 / (values.length - 1)},${23 - (value - min) * 22 / span}`).join(" "));
  }

  escape(value) {
    const node = document.createElement("span");
    node.textContent = value ?? "";
    return node.innerHTML;
  }
}

customElements.define("github-copilot-pricing-panel", GitHubCopilotPricingPanel);
