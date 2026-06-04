from html import escape
from textwrap import dedent

from services.api.core.flow_builder.flow_schema import FlowDefinition
from services.api.core.flow_builder.templates import starter_templates


def landing_page() -> str:
    return dedent(
        f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Tellus FlowBuilder API</title>
        {_front_end_styles()}
      </head>
      <body>
        <header class="site-header">
          <a class="brand" href="/" aria-label="Tellus FlowBuilder home">
            <span class="brand-mark">T</span>
            <span>
              <strong>Tellus Digital</strong>
              <small>FlowBuilder API</small>
            </span>
          </a>
          <nav aria-label="Primary navigation">
            <a href="/flow-builder/demo">Demo</a>
            <a href="/docs">API Docs</a>
            <a href="/health">Health</a>
          </nav>
        </header>

        <main>
          <section class="hero">
            <div class="hero-copy">
              <p class="eyebrow">Regulated Workflow Infrastructure</p>
              <h1>AI-assisted onboarding and origination flows for modern banks.</h1>
              <p class="hero-text">
                Tellus FlowBuilder turns natural language requests into portable JSON workflow
                definitions with conditional logic, validation, API orchestration, audit trails,
                versioning, and human review controls.
              </p>
              <div class="hero-actions" aria-label="Primary actions">
                <a class="button button-primary" href="/flow-builder/demo">Open FlowBuilder Demo</a>
                <a class="button button-secondary" href="/docs">Explore API Docs</a>
              </div>
            </div>
            <aside class="hero-panel" aria-label="FlowBuilder API status">
              <div class="panel-label">Production-minded MVP</div>
              <ol class="signal-list">
                <li><span>1</span>Generate draft workflows</li>
                <li><span>2</span>Validate against strict schema</li>
                <li><span>3</span>Simulate answers and API calls</li>
                <li><span>4</span>Publish after human approval</li>
              </ol>
            </aside>
          </section>

          <section class="section intro-grid" aria-label="FlowBuilder capabilities">
            <article>
              <p class="eyebrow">What It Does</p>
              <h2>Simple flows. Clear controls.</h2>
              <p>
                Build account opening, loan prequalification, KYC/KYB intake, consent capture,
                document upload, and internal review workflows without custom front-end code for
                every new process.
              </p>
            </article>
            <article>
              <p class="eyebrow">Who It Serves</p>
              <h2>Designed for real-world institutions.</h2>
              <p>
                FlowBuilder is aimed at banks, fintechs, and regulated operators that need
                configurable onboarding with reviewable rules, evidence, and integration points.
              </p>
            </article>
          </section>

          <section class="section">
            <div class="section-heading">
              <p class="eyebrow">API Surface</p>
              <h2>Protected endpoints for workflow generation and governance.</h2>
            </div>
            <div class="endpoint-grid">
              {_endpoint_card("GET", "/flow-builder/templates", "Review starter banking templates.")}
              {_endpoint_card("POST", "/flow-builder/generate", "Create draft workflow JSON from natural language.")}
              {_endpoint_card("POST", "/flow-builder/simulate", "Test visibility, routing, actions, and validation.")}
              {_endpoint_card("POST", "/flow-builder/publish", "Publish only after human approval is recorded.")}
              {_endpoint_card("GET", "/flow-builder/schema", "Export strict JSON Schema for builder clients.")}
              {_endpoint_card("GET", "/flow-builder/renderer-contract", "Align future Tellus frontends on rendering rules.")}
            </div>
          </section>

          <section class="section code-band">
            <div>
              <p class="eyebrow">Quick Test</p>
              <h2>Call protected APIs from your server or terminal.</h2>
              <p>
                Public pages are open, but API endpoints require an <code>X-API-Key</code> header.
                Keep this key server-side for website demos and product integrations.
              </p>
            </div>
            <pre><code>curl.exe -H "X-API-Key: $TELLUS_AI_API_KEY" \\
  https://tellus-ai-model-platform.vercel.app/flow-builder/templates</code></pre>
          </section>

          <section class="section">
            <div class="section-heading">
              <p class="eyebrow">Demo</p>
              <h2>Preview the portable workflow definitions.</h2>
            </div>
            <p class="wide-copy">
              The demo page renders starter banking templates without exposing API keys or vendor
              credentials. It is safe to link from the Tellus website as a product documentation
              entry point.
            </p>
            <a class="button button-primary" href="/flow-builder/demo">Launch the FlowBuilder Demo</a>
          </section>
        </main>

        <footer class="site-footer">
          <span>Tellus Digital, LLC</span>
          <span>New Orleans, Louisiana</span>
        </footer>
      </body>
    </html>
    """
    )


def flow_builder_demo_page() -> str:
    template_cards = "\n".join(_template_demo_card(template) for template in starter_templates())
    return dedent(
        f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Tellus FlowBuilder Demo</title>
        {_front_end_styles()}
      </head>
      <body>
        <header class="site-header">
          <a class="brand" href="/" aria-label="Tellus FlowBuilder home">
            <span class="brand-mark">T</span>
            <span>
              <strong>Tellus Digital</strong>
              <small>FlowBuilder Demo</small>
            </span>
          </a>
          <nav aria-label="Primary navigation">
            <a href="/">Overview</a>
            <a href="/docs">API Docs</a>
            <a href="/health">Health</a>
          </nav>
        </header>

        <main>
          <section class="hero compact-hero">
            <div class="hero-copy">
              <p class="eyebrow">Banking Modernization Demo</p>
              <h1>Build a demo workflow from a prompt.</h1>
              <p class="hero-text">
                Type a banking onboarding or origination request. The public demo will generate a
                website-safe draft from Tellus FlowBuilder templates and show the resulting steps,
                API placeholders, compliance signals, and JSON contract.
              </p>
              <div class="hero-actions" aria-label="Demo actions">
                <a class="button button-primary" href="/docs">Open Interactive API Docs</a>
                <a class="button button-secondary" href="/">Back to Overview</a>
              </div>
            </div>
            <aside class="hero-panel">
              <div class="panel-label">Demo safety posture</div>
              <ul class="check-list">
                <li>No API keys in browser code</li>
                <li>No real vendor credentials</li>
                <li>Draft-only AI generation</li>
                <li>Human approval before publish</li>
              </ul>
            </aside>
          </section>

          <section class="section demo-workbench" aria-labelledby="interactive-demo-title">
            <div class="section-heading">
              <p class="eyebrow">Interactive Demo</p>
              <h2 id="interactive-demo-title">Describe a flow. Review the generated draft.</h2>
              <p>
                This demo is intentionally mock-only. It does not call a live model, store your
                prompt, publish flows, or expose the protected Tellus API key. Production generation
                still happens through <code>POST /flow-builder/generate</code>.
              </p>
            </div>

            <div class="workbench-grid">
              <form class="demo-form" id="demo-form">
                <label for="demo-prompt">Workflow prompt</label>
                <textarea id="demo-prompt" name="prompt" rows="9" maxlength="2000">Create a consumer checking account onboarding flow. Ask for identity, address, contact details, employment, funding source, disclosures, and upload ID. If the customer is under 18, route to manual review. Connect to our KYC API before final submission.</textarea>

                <label for="target-flow-type">Target flow type</label>
                <select id="target-flow-type" name="target_flow_type">
                  <option value="">Auto-select from prompt</option>
                  <option value="consumer_deposit_account_opening">Consumer deposit account opening</option>
                  <option value="small_business_deposit_account_opening">Small business deposit onboarding</option>
                  <option value="loan_prequalification">Loan prequalification</option>
                </select>

                <div class="prompt-examples" aria-label="Example prompts">
                  <button type="button" data-example="Create a small business deposit onboarding flow. Collect business information, entity details, EIN, authorized signer, beneficial owners for LLCs, expected account activity, formation documents, disclosures, KYB, OFAC, and manual review.">Small business onboarding</button>
                  <button type="button" data-example="Create a loan prequalification flow. Ask for product selection, applicant information, income, housing, requested amount, credit consent, and connect to a soft-pull credit bureau placeholder. Include adverse action review notes.">Loan prequalification</button>
                  <button type="button" data-example="Create a consumer checking account flow with identity, address, contact details, employment, funding source, disclosures, document upload, KYC check, and manual review for minors.">Consumer checking</button>
                </div>

                <button class="button button-primary" type="submit">Generate Demo Draft</button>
                <p class="form-note">
                  Demo output is draft-only and must be reviewed before any production use.
                </p>
              </form>

              <div class="demo-results" aria-live="polite">
                <div class="status-line" id="demo-status">Ready for a prompt.</div>

                <article class="result-panel">
                  <p class="eyebrow">Generated Structure</p>
                  <h3 id="result-title">No draft generated yet</h3>
                  <p id="result-message">Use the form to generate a demo workflow.</p>
                  <div class="metric-row compact-metrics" id="result-metrics"></div>
                </article>

                <article class="result-panel">
                  <p class="eyebrow">Detected Signals</p>
                  <div class="pill-row" id="detected-signals"></div>
                </article>

                <article class="result-panel">
                  <p class="eyebrow">Step Preview</p>
                  <ol class="step-list" id="generated-steps"></ol>
                </article>

                <article class="result-panel">
                  <p class="eyebrow">Review Items</p>
                  <ul class="risk-list" id="generated-risks"></ul>
                </article>
              </div>
            </div>
          </section>

          <section class="section">
            <div class="section-heading">
              <p class="eyebrow">Starter Templates</p>
              <h2>Banking workflows that can be extended without custom coding.</h2>
            </div>
            <div class="template-grid">
              {template_cards}
            </div>
          </section>

          <section class="section code-band">
            <div>
              <p class="eyebrow">Website Integration Pattern</p>
              <h2>Use a server route for live demos.</h2>
              <p>
                For public website demos, call protected FlowBuilder APIs from a server-side route
                and return sanitized output to the browser. Never place the API key in front-end
                JavaScript.
              </p>
            </div>
            <pre><code>GET /flow-builder/demo       public documentation page
GET /flow-builder/templates  protected API endpoint
POST /flow-builder/simulate  protected API endpoint</code></pre>
          </section>
        </main>

        <footer class="site-footer">
          <span>Tellus Digital, LLC</span>
          <span>FlowBuilder for banking modernization products</span>
        </footer>
        {_demo_script()}
      </body>
    </html>
    """
    )


def _template_demo_card(template: FlowDefinition) -> str:
    steps = sorted(template.steps, key=lambda step: step.order)
    field_count = sum(len(step.fields) for step in steps)
    connector_count = len(template.connectors)
    sensitive_count = sum(
        1
        for step in steps
        for field in step.fields
        if field.pii_classification in {"high", "restricted"}
    )
    step_items = "\n".join(
        f"<li><span>{step.order}</span>{escape(step.title)}</li>"
        for step in steps[:6]
    )
    remaining = len(steps) - 6
    if remaining > 0:
        step_items += f"<li><span>+</span>{remaining} additional steps</li>"
    risk_items = "\n".join(
        f"<li>{escape(risk.replace('_', ' '))}</li>" for risk in template.risk_flags[:4]
    )
    return dedent(
        f"""
        <article class="template-card" id="{escape(template.flow_type)}">
          <div class="template-card-header">
            <p class="eyebrow">{escape(template.flow_type.replace('_', ' '))}</p>
            <h3>{escape(template.name)}</h3>
            <p>{escape(template.description or "")}</p>
          </div>
          <div class="metric-row" aria-label="{escape(template.name)} metrics">
            <span><strong>{len(steps)}</strong> steps</span>
            <span><strong>{field_count}</strong> fields</span>
            <span><strong>{connector_count}</strong> connectors</span>
            <span><strong>{sensitive_count}</strong> sensitive fields</span>
          </div>
          <div class="template-details">
            <div>
              <h4>Rendered Step Preview</h4>
              <ol class="step-list">{step_items}</ol>
            </div>
            <div>
              <h4>Review Signals</h4>
              <ul class="risk-list">{risk_items}</ul>
            </div>
          </div>
        </article>
        """
    )


def _endpoint_card(method: str, path: str, description: str) -> str:
    return dedent(
        f"""
        <article class="endpoint-card">
          <div><span class="method">{escape(method)}</span><code>{escape(path)}</code></div>
          <p>{escape(description)}</p>
        </article>
        """
    )


def _demo_script() -> str:
    return """
        <script>
          const form = document.querySelector("#demo-form");
          const promptInput = document.querySelector("#demo-prompt");
          const flowTypeInput = document.querySelector("#target-flow-type");
          const statusLine = document.querySelector("#demo-status");
          const title = document.querySelector("#result-title");
          const message = document.querySelector("#result-message");
          const metrics = document.querySelector("#result-metrics");
          const signals = document.querySelector("#detected-signals");
          const steps = document.querySelector("#generated-steps");
          const risks = document.querySelector("#generated-risks");

          function setStatus(text, isError = false) {
            statusLine.textContent = text;
            statusLine.classList.toggle("error", isError);
          }

          function clearNode(node) {
            while (node.firstChild) {
              node.removeChild(node.firstChild);
            }
          }

          function appendMetric(label, value) {
            const item = document.createElement("span");
            const strong = document.createElement("strong");
            strong.textContent = value;
            item.appendChild(strong);
            item.appendChild(document.createTextNode(label));
            metrics.appendChild(item);
          }

          function renderPills(node, items) {
            clearNode(node);
            items.forEach((item) => {
              const pill = document.createElement("span");
              pill.textContent = item.replaceAll("_", " ");
              node.appendChild(pill);
            });
          }

          function renderRisks(items) {
            clearNode(risks);
            items.slice(0, 8).forEach((item) => {
              const risk = document.createElement("li");
              risk.textContent = item.replaceAll("_", " ");
              risks.appendChild(risk);
            });
          }

          function renderSteps(flow) {
            clearNode(steps);
            flow.steps.slice(0, 8).forEach((step) => {
              const item = document.createElement("li");
              const badge = document.createElement("span");
              badge.textContent = step.order;
              item.appendChild(badge);
              item.appendChild(
                document.createTextNode(`${step.title} (${step.fields.length} fields)`)
              );
              steps.appendChild(item);
            });
            if (flow.steps.length > 8) {
              const item = document.createElement("li");
              const badge = document.createElement("span");
              badge.textContent = "+";
              item.appendChild(badge);
              item.appendChild(document.createTextNode(`${flow.steps.length - 8} additional steps`));
              steps.appendChild(item);
            }
          }

          function renderResult(data) {
            clearNode(metrics);
            if (data.blocked) {
              title.textContent = "Demo request blocked";
              message.textContent = data.message;
              renderPills(signals, data.safety_flags || []);
              clearNode(steps);
              renderRisks(data.safety_flags || []);
              setStatus("Safety review required before a flow can be generated.", true);
              return;
            }

            title.textContent = data.selected_template.name;
            message.textContent = data.message + " " + data.selected_template.reason;
            appendMetric(" steps", data.summary.step_count);
            appendMetric(" fields", data.summary.field_count);
            appendMetric(" connectors", data.summary.connector_count);
            appendMetric(" sensitive fields", data.summary.sensitive_field_count);
            renderPills(signals, data.interpreted_request.detected_workflow_signals);
            renderSteps(data.flow_json);
            renderRisks(data.risk_flags);
            setStatus("Demo draft generated. Review the structure before using protected APIs.");
          }

          document.querySelectorAll("[data-example]").forEach((button) => {
            button.addEventListener("click", () => {
              promptInput.value = button.dataset.example;
              promptInput.focus();
            });
          });

          form.addEventListener("submit", async (event) => {
            event.preventDefault();
            setStatus("Generating demo draft...");
            try {
              const response = await fetch("/flow-builder/demo/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  prompt: promptInput.value,
                  target_flow_type: flowTypeInput.value || null,
                }),
              });
              if (!response.ok) {
                throw new Error(`Demo endpoint returned ${response.status}`);
              }
              renderResult(await response.json());
            } catch (error) {
              setStatus(
                "The demo could not generate a draft. Refresh and try again, or open API docs.",
                true
              );
            }
          });
        </script>
    """


def _front_end_styles() -> str:
    return """
        <style>
          :root {
            --ink: #0c1713;
            --muted: #52615b;
            --line: #d9e3dd;
            --surface: #f5f8f4;
            --panel: #ffffff;
            --accent: #166c5a;
            --accent-strong: #0f4d40;
            --blue: #2459a6;
            --gold: #a8792f;
            --shadow: 0 18px 48px rgba(12, 23, 19, 0.10);
          }

          * { box-sizing: border-box; }

          body {
            margin: 0;
            color: var(--ink);
            background: var(--surface);
            font-family:
              Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
              "Segoe UI", sans-serif;
            line-height: 1.55;
          }

          a { color: inherit; }

          code {
            border: 1px solid var(--line);
            border-radius: 6px;
            background: #eef4f0;
            padding: 2px 6px;
            font-size: 0.92em;
          }

          pre {
            margin: 0;
            overflow-x: auto;
            border-radius: 8px;
            background: #0c1713;
            color: #f4fbf7;
            padding: 22px;
            box-shadow: var(--shadow);
          }

          pre code {
            border: 0;
            background: transparent;
            color: inherit;
            padding: 0;
          }

          .site-header,
          main,
          .site-footer {
            width: min(1160px, calc(100% - 40px));
            margin: 0 auto;
          }

          .site-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            padding: 24px 0;
          }

          .brand {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            color: var(--ink);
            text-decoration: none;
          }

          .brand-mark {
            display: grid;
            width: 42px;
            height: 42px;
            place-items: center;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
            color: var(--accent);
            font-weight: 800;
          }

          .brand strong,
          .brand small {
            display: block;
          }

          .brand small {
            color: var(--muted);
            font-size: 0.82rem;
          }

          nav {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
          }

          nav a {
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.72);
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 650;
            padding: 9px 14px;
            text-decoration: none;
          }

          .hero {
            display: grid;
            grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
            gap: 28px;
            align-items: stretch;
            padding: 72px 0 48px;
          }

          .compact-hero {
            padding-top: 48px;
          }

          .hero-copy {
            display: flex;
            flex-direction: column;
            justify-content: center;
          }

          .eyebrow {
            margin: 0 0 10px;
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }

          h1,
          h2,
          h3,
          h4,
          p {
            margin-top: 0;
          }

          h1 {
            max-width: 900px;
            margin-bottom: 20px;
            font-size: clamp(2.55rem, 6vw, 5.6rem);
            line-height: 0.96;
            letter-spacing: 0;
          }

          h2 {
            margin-bottom: 14px;
            font-size: clamp(1.85rem, 3vw, 3.35rem);
            line-height: 1.04;
            letter-spacing: 0;
          }

          h3 {
            margin-bottom: 10px;
            font-size: 1.35rem;
            line-height: 1.16;
          }

          h4 {
            margin-bottom: 12px;
            font-size: 0.9rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--muted);
          }

          .hero-text,
          .wide-copy,
          .section p {
            color: var(--muted);
            font-size: 1.02rem;
          }

          .hero-text {
            max-width: 720px;
            font-size: 1.16rem;
          }

          .hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 18px;
          }

          .button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            border-radius: 8px;
            font-weight: 750;
            padding: 12px 18px;
            text-decoration: none;
          }

          .button-primary {
            background: var(--accent);
            color: #ffffff;
          }

          .button-secondary {
            border: 1px solid var(--line);
            background: var(--panel);
            color: var(--ink);
          }

          .hero-panel,
          .endpoint-card,
          .template-card,
          .intro-grid article,
          .demo-form,
          .result-panel {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.88);
            box-shadow: var(--shadow);
          }

          .hero-panel {
            align-self: center;
            padding: 24px;
          }

          .panel-label {
            margin-bottom: 18px;
            color: var(--gold);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }

          .signal-list,
          .check-list,
          .step-list,
          .risk-list {
            margin: 0;
            padding: 0;
            list-style: none;
          }

          .signal-list li,
          .check-list li,
          .step-list li {
            display: flex;
            gap: 12px;
            align-items: flex-start;
            border-top: 1px solid var(--line);
            padding: 14px 0;
          }

          .signal-list li:first-child,
          .check-list li:first-child,
          .step-list li:first-child {
            border-top: 0;
          }

          .signal-list span,
          .step-list span {
            display: grid;
            flex: 0 0 28px;
            width: 28px;
            height: 28px;
            place-items: center;
            border-radius: 50%;
            background: #e6f0eb;
            color: var(--accent-strong);
            font-weight: 800;
          }

          .section {
            padding: 46px 0;
          }

          .section-heading {
            max-width: 780px;
            margin-bottom: 22px;
          }

          .intro-grid,
          .endpoint-grid,
          .template-grid,
          .template-details,
          .metric-row,
          .workbench-grid {
            display: grid;
            gap: 18px;
          }

          .intro-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .intro-grid article,
          .endpoint-card,
          .template-card,
          .demo-form,
          .result-panel {
            padding: 22px;
          }

          .endpoint-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .endpoint-card div {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            margin-bottom: 10px;
          }

          .method {
            border-radius: 999px;
            background: #e8f1ef;
            color: var(--accent-strong);
            font-size: 0.75rem;
            font-weight: 850;
            padding: 4px 8px;
          }

          .code-band {
            display: grid;
            grid-template-columns: minmax(0, 0.9fr) minmax(340px, 1.1fr);
            gap: 24px;
            align-items: center;
            border-top: 1px solid var(--line);
            border-bottom: 1px solid var(--line);
          }

          .template-grid {
            grid-template-columns: 1fr;
          }

          .demo-workbench {
            border-top: 1px solid var(--line);
            border-bottom: 1px solid var(--line);
          }

          .workbench-grid {
            grid-template-columns: minmax(320px, 0.86fr) minmax(0, 1.14fr);
            align-items: start;
          }

          .demo-form {
            display: grid;
            gap: 14px;
            background: var(--panel);
          }

          .demo-form label {
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 800;
          }

          .demo-form textarea,
          .demo-form select {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #fbfdfb;
            color: var(--ink);
            font: inherit;
            padding: 13px;
          }

          .demo-form textarea {
            min-height: 210px;
            resize: vertical;
          }

          .prompt-examples,
          .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          .prompt-examples button,
          .pill-row span {
            border: 1px solid var(--line);
            border-radius: 999px;
            background: #eef4f0;
            color: var(--accent-strong);
            font: inherit;
            font-size: 0.86rem;
            font-weight: 750;
            padding: 8px 10px;
          }

          .prompt-examples button {
            cursor: pointer;
          }

          .form-note {
            margin: 0;
            color: var(--muted);
            font-size: 0.92rem;
          }

          .demo-results {
            display: grid;
            gap: 14px;
          }

          .status-line {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #eef4f0;
            color: var(--accent-strong);
            font-weight: 750;
            padding: 12px 14px;
          }

          .status-line.error {
            border-color: #e3b8b8;
            background: #fff1f1;
            color: #8a2929;
          }

          .compact-metrics {
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-bottom: 0;
          }

          .template-card {
            background: var(--panel);
          }

          .template-card-header {
            max-width: 780px;
          }

          .metric-row {
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin: 20px 0;
          }

          .metric-row span {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--surface);
            color: var(--muted);
            padding: 12px;
          }

          .metric-row strong {
            display: block;
            color: var(--ink);
            font-size: 1.35rem;
          }

          .template-details {
            grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
            border-top: 1px solid var(--line);
            padding-top: 20px;
          }

          .risk-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          .risk-list li {
            border: 1px solid #e3d6bd;
            border-radius: 999px;
            background: #fbf6ec;
            color: #73521f;
            font-size: 0.86rem;
            font-weight: 700;
            padding: 7px 10px;
          }

          .site-footer {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            border-top: 1px solid var(--line);
            color: var(--muted);
            padding: 28px 0 36px;
          }

          @media (max-width: 900px) {
            .hero,
            .intro-grid,
            .endpoint-grid,
            .code-band,
            .template-details,
            .workbench-grid {
              grid-template-columns: 1fr;
            }

            .hero {
              padding-top: 42px;
            }

            .metric-row {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }

          @media (max-width: 640px) {
            .site-header {
              align-items: flex-start;
              flex-direction: column;
            }

            nav {
              justify-content: flex-start;
            }

            h1 {
              font-size: 2.45rem;
            }

            .metric-row {
              grid-template-columns: 1fr;
            }
          }
        </style>
    """
