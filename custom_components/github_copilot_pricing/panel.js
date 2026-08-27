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
        main { max-width: 1400px; margin: auto; padding: 32px; }
        header { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 28px; }
        h1 { margin: 0; font-size: clamp(30px, 4vw, 52px); letter-spacing: -0.04em; }
        p { color: var(--secondary-text-color); margin: 8px 0 0; }
        select { color: inherit; background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 10px; padding: 10px 14px; }
        #models { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; }
        article { background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 16px; padding: 20px; box-shadow: var(--ha-card-box-shadow); }
        article h2 { margin: 0; font-size: 20px; }
        .provider { color: var(--secondary-text-color); font-size: 12px; text-transform: uppercase; letter-spacing: .12em; }
        .prices { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 12px; margin-top: 22px; }
        .label { color: var(--secondary-text-color); font-size: 12px; }
        .value { font-size: 24px; font-variant-numeric: tabular-nums; margin-top: 4px; }
        svg { width: 100%; height: 36px; margin-top: 8px; overflow: visible; }
        polyline { fill: none; stroke: var(--primary-color); stroke-width: 2; vector-effect: non-scaling-stroke; }
        .empty { grid-column: 1 / -1; padding: 64px; text-align: center; color: var(--secondary-text-color); }
        @media (max-width: 600px) { main { padding: 20px 12px; } header { align-items: start; flex-direction: column; } }
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
    target.innerHTML = [...models.entries()].map(([key, states]) => {
      const [provider, model] = key.split("|");
      return `<article><span class="provider">${this.escape(provider)}</span><h2>${this.escape(model)}</h2><div class="prices">${states.map((state) => `<div><div class="label">${this.escape(state.attributes.friendly_name.split(" — ").at(-1))}</div><div class="value">$${this.escape(state.state)}</div><svg viewBox="0 0 100 36" preserveAspectRatio="none" data-entity="${state.entity_id}"><polyline></polyline></svg></div>`).join("")}</div></article>`;
    }).join("") || '<div class="empty">No pricing sensors found.</div>';
    this.loadHistory();
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
    chart.querySelector("polyline").setAttribute("points", values.map((value, index) => `${index * 100 / (values.length - 1)},${34 - (value - min) * 32 / span}`).join(" "));
  }

  escape(value) {
    const node = document.createElement("span");
    node.textContent = value ?? "";
    return node.innerHTML;
  }
}

customElements.define("github-copilot-pricing-panel", GitHubCopilotPricingPanel);
