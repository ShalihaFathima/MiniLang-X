/**
 * MiniLang-X — Parser Lab Foundation (Phase 2: Top-Down Parsing)
 * Client-side Controller for Grammar Editing, FIRST/FOLLOW Sets,
 * LL(1) Predictive Parsing Table & Trace, Parse Tree Visualizer,
 * and Recursive Descent Parser with Left Recursion Guard.
 */

(function () {
    // DOM Elements - Workspaces
    const navPipelineTab = document.getElementById("nav-pipeline-tab");
    const navParserLabTab = document.getElementById("nav-parser-lab-tab");
    const pipelineWorkspace = document.getElementById("pipeline-workspace");
    const parserLabWorkspace = document.getElementById("parser-lab-workspace");

    // DOM Elements - Parser Lab Controls
    const grammarEditor = document.getElementById("grammar-editor");
    const grammarLineNumbers = document.getElementById("grammar-line-numbers");
    const grammarPresetSelect = document.getElementById("grammar-preset-select");
    const grammarStartSymbol = document.getElementById("grammar-start-symbol");
    const parserInputString = document.getElementById("parser-input-string");
    const parserEngineSelect = document.getElementById("parser-engine-select");

    // Buttons
    const btnValidateGrammar = document.getElementById("btn-validate-grammar");
    const btnComputeFirstFollow = document.getElementById("btn-compute-first-follow");
    const btnGenerateLL1Table = document.getElementById("btn-generate-ll1-table");
    const btnParseInput = document.getElementById("btn-parse-input");

    // Views & Status
    const grammarStatusPill = document.getElementById("grammar-status-pill");
    const grammarStatusText = document.getElementById("grammar-status-text");
    const parserLabViewTitle = document.getElementById("parser-lab-view-title");
    const parserLabContent = document.getElementById("parser-lab-content");
    const tabNav = document.querySelector("#parser-lab-workspace .parser-lab-tab-nav");

    // Built-in Grammar Presets
    const grammarPresets = {
        ll1_expr: {
            start: "E",
            grammar: "E -> T EPrime\nEPrime -> + T EPrime | ε\nT -> id",
            input: "id + id",
            engine: "ll1"
        },
        left_rec: {
            start: "E",
            grammar: "E -> E + T | T\nT -> id",
            input: "id + id",
            engine: "ll1"
        },
        expr: {
            start: "E",
            grammar: "E -> T EPrime\nEPrime -> + T EPrime | ε\nT -> F TPrime\nTPrime -> * F TPrime | ε\nF -> ( E ) | id",
            input: "id + id * id",
            engine: "ll1"
        },
        nullable: {
            start: "S",
            grammar: "S -> A B C\nA -> a | eps\nB -> b | eps\nC -> c | eps",
            input: "a b c",
            engine: "ll1"
        },
        simple: {
            start: "S",
            grammar: "S -> a A\nA -> b | eps",
            input: "a b",
            engine: "ll1"
        },
        invalid: {
            start: "S",
            grammar: "S -> a B\nMalformedLineWithoutArrow\nC -> c eps d",
            input: "a",
            engine: "ll1"
        }
    };

    // State Store
    const state = {
        activeTab: "grammar",
        lastValidation: null,
        lastFirstFollow: null,
        lastLL1Table: null,
        lastLL1Parse: null,
        lastRDParse: null,
        lastParseTree: null
    };

    function escapeHTML(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Workspace Switching (Pipeline vs Top-Down Lab vs Bottom-Up Lab)
    const navBottomUpTab = document.getElementById("nav-bottom-up-tab");
    const bottomUpWorkspace = document.getElementById("bottom-up-workspace");

    function switchWorkspace(target) {
        if (navPipelineTab) {
            navPipelineTab.classList.toggle("active", target === "pipeline");
            navPipelineTab.setAttribute("aria-selected", target === "pipeline");
        }
        if (navParserLabTab) {
            navParserLabTab.classList.toggle("active", target === "top-down");
            navParserLabTab.setAttribute("aria-selected", target === "top-down");
        }
        if (navBottomUpTab) {
            navBottomUpTab.classList.toggle("active", target === "bottom-up");
            navBottomUpTab.setAttribute("aria-selected", target === "bottom-up");
        }

        if (pipelineWorkspace) pipelineWorkspace.style.display = target === "pipeline" ? "block" : "none";
        if (parserLabWorkspace) parserLabWorkspace.style.display = target === "top-down" ? "block" : "none";
        if (bottomUpWorkspace) bottomUpWorkspace.style.display = target === "bottom-up" ? "block" : "none";
    }

    if (navPipelineTab) navPipelineTab.addEventListener("click", () => switchWorkspace("pipeline"));
    if (navParserLabTab) navParserLabTab.addEventListener("click", () => switchWorkspace("top-down"));
    if (navBottomUpTab) navBottomUpTab.addEventListener("click", () => switchWorkspace("bottom-up"));

    // Line Number Synchronization
    function updateGrammarLineNumbers() {
        if (!grammarEditor || !grammarLineNumbers) return;
        const lines = grammarEditor.value.split("\n").length;
        grammarLineNumbers.textContent = Array.from(
            { length: lines },
            (_, index) => index + 1
        ).join("\n");
    }

    if (grammarEditor) {
        grammarEditor.addEventListener("input", function () {
            updateGrammarLineNumbers();
            if (grammarPresetSelect) {
                grammarPresetSelect.value = "custom";
            }
        });

        grammarEditor.addEventListener("scroll", function () {
            if (grammarLineNumbers) {
                grammarLineNumbers.scrollTop = grammarEditor.scrollTop;
            }
        });
    }

    // Preset Selection
    if (grammarPresetSelect) {
        grammarPresetSelect.addEventListener("change", function () {
            const presetKey = grammarPresetSelect.value;
            if (presetKey in grammarPresets) {
                const preset = grammarPresets[presetKey];
                grammarEditor.value = preset.grammar;
                if (grammarStartSymbol) {
                    grammarStartSymbol.value = preset.start;
                }
                if (parserInputString && preset.input) {
                    parserInputString.value = preset.input;
                }
                if (parserEngineSelect && preset.engine) {
                    parserEngineSelect.value = preset.engine;
                }
                updateGrammarLineNumbers();
                setGrammarStatus(null, "Preset Loaded");
            }
        });
    }

    // Status Helper
    function setGrammarStatus(status, text) {
        if (!grammarStatusPill || !grammarStatusText) return;
        grammarStatusPill.classList.remove("is-running", "is-success", "is-error");
        if (status) {
            grammarStatusPill.classList.add(`is-${status}`);
        }
        grammarStatusText.textContent = text;
    }

    // Tab Switching
    function setActiveTab(tabKey) {
        state.activeTab = tabKey;
        const tabBtns = document.querySelectorAll("#parser-lab-workspace .lab-tab-btn");
        tabBtns.forEach(btn => {
            if (btn.getAttribute("data-view") === tabKey) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });

        const titles = {
            "grammar": "Grammar Specification & Validation",
            "first-follow": "FIRST and FOLLOW Sets",
            "ll1-table": "LL(1) Predictive Parsing Table",
            "trace": "Parsing Execution Trace",
            "parse-tree": "Parse Tree Derivation",
            "recursive-descent": "Recursive Descent Analysis"
        };

        if (parserLabViewTitle) {
            parserLabViewTitle.textContent = titles[tabKey] || "Top-Down Parsing";
        }

        renderActiveTab();
    }

    if (tabNav) {
        tabNav.addEventListener("click", function (e) {
            const btn = e.target.closest(".lab-tab-btn");
            if (btn) {
                const tabKey = btn.getAttribute("data-view");
                if (tabKey) {
                    setActiveTab(tabKey);
                }
            }
        });
    }

    // API Call Helper
    async function callParserLabAPI(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error("Invalid response received from parser lab service.");
        }

        if (!response.ok) {
            throw new Error(data && data.error ? data.error : `Request failed with status ${response.status}`);
        }

        if (data && data.success === false && data.error) {
            throw new Error(data.error);
        }

        return data;
    }

    // ==========================================
    // Rendering Helpers
    // ==========================================

    function renderDiagnostics(diagnostics) {
        if (!diagnostics || diagnostics.length === 0) {
            return `
                <div class="semantic-status success">
                    ✓ Grammar syntax and symbol definitions validated successfully with zero errors.
                </div>
            `;
        }

        const hasErrors = diagnostics.some(d => d.severity === "error");
        const statusClass = hasErrors ? "error" : "success";
        const statusMsg = hasErrors ? "✕ Grammar Validation Failed" : "✓ Grammar Valid (with warnings)";

        const items = diagnostics.map(d => {
            const isErr = d.severity === "error";
            const badgeClass = isErr ? "diag-pill-error" : "diag-pill-warning";
            const locText = d.line ? `Line ${d.line}` : "Grammar-level";
            return `
                <div class="grammar-diagnostic-item ${d.severity}">
                    <div class="diag-header">
                        <span class="diag-badge ${badgeClass}">${escapeHTML(d.severity.toUpperCase())}</span>
                        <span class="diag-loc">${escapeHTML(locText)}</span>
                        ${d.symbol ? `<span class="diag-sym">Symbol: <code>${escapeHTML(d.symbol)}</code></span>` : ""}
                    </div>
                    <div class="diag-msg">${escapeHTML(d.message)}</div>
                </div>
            `;
        }).join("");

        return `
            <div class="semantic-status ${statusClass}">${statusMsg}</div>
            <div class="grammar-diagnostics-container">${items}</div>
        `;
    }

    function renderSummaryCards(data) {
        const nonterminals = data.nonterminals || [];
        const terminals = data.terminals || [];
        const productions = data.productions || [];
        const startSymbol = data.start_symbol || "—";
        const nullableMap = data.nullable || {};
        const nullableCount = Object.values(nullableMap).filter(Boolean).length;

        return `
            <div class="parser-lab-metrics-grid">
                <div class="metric-card">
                    <span class="metric-label">Start Symbol</span>
                    <span class="metric-val"><code>${escapeHTML(startSymbol)}</code></span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Productions</span>
                    <span class="metric-val">${productions.length}</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Nonterminals</span>
                    <span class="metric-val">${nonterminals.length}</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Terminals</span>
                    <span class="metric-val">${terminals.length}</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Nullable Nonterminals</span>
                    <span class="metric-val">${nullableCount}</span>
                </div>
            </div>
        `;
    }

    function renderProductions(productions) {
        if (!productions || productions.length === 0) return "";

        const rows = productions.map((prod, idx) => {
            const rhsFormatted = (prod.rhs || []).map(sym => {
                if (sym === "ε") {
                    return `<span class="symbol-pill symbol-pill-epsilon">ε</span>`;
                }
                return `<code class="grammar-sym">${escapeHTML(sym)}</code>`;
            }).join(" ");

            return `
                <tr>
                    <td style="width: 50px;">${idx + 1}</td>
                    <td style="width: 140px;"><strong><code>${escapeHTML(prod.lhs)}</code></strong></td>
                    <td style="width: 30px; text-align: center; color: var(--text-subtle);">➔</td>
                    <td>${rhsFormatted}</td>
                </tr>
            `;
        }).join("");

        return `
            <div class="tac-table-wrapper" style="margin-top: 18px;">
                <div class="tac-title">Normalized Production Rules (${productions.length})</div>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>LHS</th>
                            <th></th>
                            <th>RHS Derivation</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderVocabulary(data) {
        const nonterminals = data.nonterminals || [];
        const terminals = data.terminals || [];

        const ntPills = nonterminals.map(nt =>
            `<span class="symbol-pill symbol-pill-nonterminal">${escapeHTML(nt)}</span>`
        ).join(" ") || "None";

        const termPills = terminals.map(t =>
            `<span class="symbol-pill symbol-pill-terminal">${escapeHTML(t)}</span>`
        ).join(" ") || "None";

        return `
            <div class="grammar-vocab-panel" style="margin-top: 18px;">
                <div class="vocab-row">
                    <strong>Nonterminals (V_N):</strong>
                    <div class="vocab-pills">${ntPills}</div>
                </div>
                <div class="vocab-row" style="margin-top: 10px;">
                    <strong>Terminals (V_T):</strong>
                    <div class="vocab-pills">${termPills}</div>
                </div>
            </div>
        `;
    }

    function renderFirstFollowTable(data) {
        const nonterminals = data.nonterminals || [];
        const firstMap = data.first || {};
        const followMap = data.follow || {};
        const nullableMap = data.nullable || {};

        if (!data.first || Object.keys(firstMap).length === 0) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No FIRST / FOLLOW Sets Available</h3>
                    <p>Click <strong>FIRST / FOLLOW</strong> on the left to compute iterative fixed-point sets.</p>
                </div>
            `;
        }

        const rows = nonterminals.map(nt => {
            const firstSet = firstMap[nt] || [];
            const followSet = followMap[nt] || [];
            const isNullable = Boolean(nullableMap[nt]);

            const firstPills = firstSet.length
                ? firstSet.map(sym => {
                    const cls = sym === "ε" ? "symbol-pill-epsilon" : "symbol-pill-terminal";
                    return `<span class="symbol-pill ${cls}">${escapeHTML(sym)}</span>`;
                }).join(" ")
                : `<span class="text-muted">∅</span>`;

            const followPills = followSet.length
                ? followSet.map(sym => {
                    const cls = sym === "$" ? "symbol-pill-end" : "symbol-pill-terminal";
                    return `<span class="symbol-pill ${cls}">${escapeHTML(sym)}</span>`;
                }).join(" ")
                : `<span class="text-muted">∅</span>`;

            const nullableBadge = isNullable
                ? `<span class="nullable-tag nullable-yes">✓ True (ε ∈ FIRST)</span>`
                : `<span class="nullable-tag nullable-no">False</span>`;

            return `
                <tr>
                    <td><strong><code>${escapeHTML(nt)}</code></strong></td>
                    <td>${nullableBadge}</td>
                    <td><div class="set-symbols-wrap">${firstPills}</div></td>
                    <td><div class="set-symbols-wrap">${followPills}</div></td>
                </tr>
            `;
        }).join("");

        return `
            <div class="tac-table-wrapper" style="margin-top: 10px;">
                <div class="tac-title">FIRST and FOLLOW Sets</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 140px;">Nonterminal</th>
                            <th style="width: 170px;">Nullable?</th>
                            <th>FIRST(X)</th>
                            <th>FOLLOW(X)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderLL1TableView(data) {
        if (!data) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No LL(1) Table Generated Yet</h3>
                    <p>Click <strong>Generate Table</strong> on the left to compute the predictive parsing table M[A, a] and detect cell conflicts.</p>
                </div>
            `;
        }

        const isLL1 = data.is_ll1;
        const conflicts = data.conflicts || [];
        const nonterminals = data.nonterminals || [];
        const terminals = data.terminals || [];
        const table = data.table || {};

        let statusHtml = isLL1
            ? `<div class="semantic-status success">✓ Valid LL(1) Grammar — Zero conflicts detected in parsing table M[A, a].</div>`
            : `<div class="semantic-status error">✕ Grammar is NOT LL(1) — ${conflicts.length} conflict(s) detected in parsing table.</div>`;

        // Conflict Explanations
        let conflictHtml = "";
        if (conflicts.length > 0) {
            const cards = conflicts.map(c => {
                const prodPills = (c.productions || []).map(p =>
                    `<span class="prod-cell-pill conflict-pill">${escapeHTML(p.lhs)} ➔ ${escapeHTML((p.rhs || []).join(" "))}</span>`
                ).join(" ");

                return `
                    <div class="ll1-conflict-card">
                        <div class="ll1-conflict-card-header">
                            <span class="conflict-badge">${escapeHTML(c.conflict_type)} CONFLICT</span>
                            <span>Cell M[<strong>${escapeHTML(c.nonterminal)}</strong>, <code>${escapeHTML(c.terminal)}</code>]</span>
                        </div>
                        <div class="diag-msg">${escapeHTML(c.message)}</div>
                        <div class="ll1-conflict-prods">
                            <strong>Competing rules:</strong> ${prodPills}
                        </div>
                    </div>
                `;
            }).join("");

            conflictHtml = `
                <div class="ll1-conflicts-container">
                    <h3 style="margin: 0; font-size: 13px; font-weight: 700; color: var(--error-text);">
                        Table Conflicts (${conflicts.length})
                    </h3>
                    ${cards}
                </div>
            `;
        }

        // 2D Table Generation
        const thCols = terminals.map(t =>
            `<th><code>${escapeHTML(t)}</code></th>`
        ).join("");

        const bodyRows = nonterminals.map(nt => {
            const rowData = table[nt] || {};
            const cellTds = terminals.map(t => {
                const prods = rowData[t] || [];
                if (prods.length === 0) {
                    return `<td class="cell-empty">—</td>`;
                }
                const hasConflict = prods.length > 1;
                const cellClass = hasConflict ? "cell-conflict" : "cell-rule";

                const prodsHtml = prods.map(p => {
                    const rhs = (p.rhs || []).map(s => s === "ε" ? "ε" : s).join(" ");
                    const pillClass = hasConflict ? "prod-cell-pill conflict-pill" : "prod-cell-pill";
                    return `<div class="${pillClass}"><strong>${escapeHTML(p.lhs)}</strong> ➔ ${escapeHTML(rhs)}</div>`;
                }).join("");

                return `
                    <td class="${cellClass}">
                        ${hasConflict ? `<span class="conflict-badge">CONFLICT (${prods.length})</span><br>` : ""}
                        ${prodsHtml}
                    </td>
                `;
            }).join("");

            return `
                <tr>
                    <td class="nt-row-header"><strong><code>${escapeHTML(nt)}</code></strong></td>
                    ${cellTds}
                </tr>
            `;
        }).join("");

        return `
            ${statusHtml}
            ${conflictHtml}
            <div class="ll1-table-wrapper">
                <table class="ll1-table">
                    <thead>
                        <tr>
                            <th class="nt-col-header">Nonterminal</th>
                            ${thCols}
                        </tr>
                    </thead>
                    <tbody>
                        ${bodyRows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderTraceView(parseData, parseType = "ll1") {
        if (!parseData) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No Parsing Execution Trace Available</h3>
                    <p>Enter an input string on the left (e.g. <code>id + id</code>) and click <strong>Parse Input</strong>.</p>
                </div>
            `;
        }

        const accepted = parseData.accepted;
        const tokens = parseData.tokens || [];
        const trace = parseData.trace || [];
        const error = parseData.error;

        const tokenPills = tokens.map(t =>
            `<span class="symbol-pill symbol-pill-terminal">${escapeHTML(t)}</span>`
        ).join(" ") + ` <span class="symbol-pill symbol-pill-end">$</span>`;

        let statusBanner = accepted
            ? `<div class="semantic-status success">✓ Input Tokens Accepted — Derivation completed successfully!</div>`
            : `<div class="semantic-status error">✕ Parsing Rejected — ${escapeHTML(error || "Syntax error during parsing.")}</div>`;

        if (parseType === "rd" && parseData.has_left_recursion) {
            const lr = parseData.left_recursion || {};
            statusBanner = `
                <div class="left-recursion-box">
                    <div class="left-recursion-header">
                        <span>⚠️ Left Recursion Detected</span>
                    </div>
                    <div class="left-recursion-body">
                        ${escapeHTML(lr.explanation || "Conventional predictive top-down recursive descent cannot directly parse left-recursive grammars.")}
                    </div>
                </div>
                ${statusBanner}
            `;
        }

        let traceRows = "";
        if (parseType === "ll1") {
            traceRows = trace.map(s => {
                const stackStr = (s.stack || []).map(x => escapeHTML(x)).join(" ");
                const remStr = (s.remaining_input || []).map(x => escapeHTML(x)).join(" ");
                const actionBadgeClass = `trace-action-${s.status || "expand"}`;
                const rowClass = `trace-step-${s.status || "expand"}`;

                return `
                    <tr class="${rowClass}">
                        <td style="width: 50px;">${s.step}</td>
                        <td style="font-weight: 600;"><code>${stackStr}</code></td>
                        <td><code>${remStr}</code></td>
                        <td>
                            <span class="trace-action-badge ${actionBadgeClass}">${escapeHTML(s.action)}</span>
                            ${s.production ? `<span style="margin-left: 6px; font-weight: 600;">(${escapeHTML(s.production)})</span>` : ""}
                        </td>
                    </tr>
                `;
            }).join("");

            return `
                ${statusBanner}
                <div style="margin: 12px 0; font-size: 12px;">
                    <strong>Tokenized Input Stream:</strong> ${tokenPills}
                </div>
                <div class="trace-table-wrapper">
                    <table class="trace-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Stack (Top ➔ Bottom)</th>
                                <th>Remaining Input</th>
                                <th>Action &amp; Rule Applied</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${traceRows}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            // Recursive Descent Trace
            traceRows = trace.map(s => {
                const actionBadgeClass = `trace-action-${s.status || "expand"}`;
                const rowClass = `trace-step-${s.status || "expand"}`;
                const indent = "&nbsp;&nbsp;".repeat(Math.max(0, (s.depth || 1) - 1));

                return `
                    <tr class="${rowClass}">
                        <td style="width: 50px;">${s.step}</td>
                        <td style="width: 60px;">${s.depth}</td>
                        <td>${indent}<span class="trace-action-badge ${actionBadgeClass}">${escapeHTML(s.action)}</span></td>
                        <td><code>${escapeHTML(s.lookahead || "—")}</code></td>
                        <td><strong>${escapeHTML(s.status || "")}</strong></td>
                    </tr>
                `;
            }).join("");

            return `
                ${statusBanner}
                <div style="margin: 12px 0; font-size: 12px;">
                    <strong>Tokenized Input Stream:</strong> ${tokenPills}
                </div>
                <div class="trace-table-wrapper">
                    <table class="trace-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Depth</th>
                                <th>Procedure / Action</th>
                                <th>Lookahead</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${traceRows}
                        </tbody>
                    </table>
                </div>
            `;
        }
    }

    function renderParseTreeNode(node, prefix = "", isLast = true) {
        if (!node) return "";

        const connector = isLast ? "└── " : "├── ";
        const childPrefix = prefix + (isLast ? "    " : "│   ");

        let badgeClass = "tree-node-nonterminal";
        if (node.is_terminal) {
            badgeClass = node.label === "ε" ? "tree-node-epsilon" : "tree-node-terminal";
        }

        let html = `
            <div class="tree-row">
                <span class="tree-indent-guide">${prefix}${connector}</span>
                <span class="tree-node-chip ${badgeClass}">
                    ${node.is_terminal ? "Leaf: " : "Node: "}
                    <strong>${escapeHTML(node.label)}</strong>
                </span>
            </div>
        `;

        const children = node.children || [];
        for (let i = 0; i < children.length; i++) {
            const isChildLast = i === children.length - 1;
            html += renderParseTreeNode(children[i], childPrefix, isChildLast);
        }

        return html;
    }

    function renderParseTreeView(parseTree) {
        if (!parseTree) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No Parse Tree Generated</h3>
                    <p>Parse trees are constructed when an input sequence is successfully parsed by the LL(1) or Recursive Descent parser.</p>
                </div>
            `;
        }

        return `
            <div class="parse-tree-container">
                <div class="parse-tree-title">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                        <polygon points="12 2 2 22 22 22"></polygon>
                    </svg>
                    <span>Concrete Syntax Derivation Tree</span>
                </div>
                <div class="tree-view">
                    ${renderParseTreeNode(parseTree, "", true)}
                </div>
            </div>
        `;
    }

    function renderRecursiveDescentView(rdData) {
        if (!rdData) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>Recursive Descent Parser Not Run Yet</h3>
                    <p>Select <strong>Recursive Descent Parser</strong> as the engine and click <strong>Parse Input</strong> on the left.</p>
                </div>
            `;
        }

        return renderTraceView(rdData, "rd");
    }

    function renderActiveTab() {
        if (!parserLabContent) return;

        switch (state.activeTab) {
            case "grammar":
                if (state.lastValidation) {
                    parserLabContent.innerHTML = `
                        ${renderDiagnostics(state.lastValidation.diagnostics)}
                        ${state.lastValidation.valid ? renderSummaryCards(state.lastValidation) : ""}
                        ${state.lastValidation.valid ? renderVocabulary(state.lastValidation) : ""}
                        ${state.lastValidation.valid ? renderProductions(state.lastValidation.productions) : ""}
                    `;
                } else {
                    parserLabContent.innerHTML = `
                        <div class="parser-lab-empty-state">
                            <h3>Ready for Grammar Analysis</h3>
                            <p>Click <strong>Validate</strong> or <strong>FIRST / FOLLOW</strong> on the left to analyze grammar rules.</p>
                        </div>
                    `;
                }
                break;

            case "first-follow":
                if (state.lastFirstFollow) {
                    parserLabContent.innerHTML = `
                        ${renderDiagnostics(state.lastFirstFollow.diagnostics)}
                        ${state.lastFirstFollow.valid ? renderSummaryCards(state.lastFirstFollow) : ""}
                        ${state.lastFirstFollow.valid ? renderFirstFollowTable(state.lastFirstFollow) : ""}
                    `;
                } else {
                    parserLabContent.innerHTML = `
                        <div class="parser-lab-empty-state">
                            <h3>No FIRST / FOLLOW Sets Computed</h3>
                            <p>Click <strong>FIRST / FOLLOW</strong> on the left to compute iterative fixed-point sets.</p>
                        </div>
                    `;
                }
                break;

            case "ll1-table":
                parserLabContent.innerHTML = renderLL1TableView(state.lastLL1Table);
                break;

            case "trace":
                parserLabContent.innerHTML = renderTraceView(state.lastLL1Parse, "ll1");
                break;

            case "parse-tree":
                parserLabContent.innerHTML = renderParseTreeView(state.lastParseTree);
                break;

            case "recursive-descent":
                parserLabContent.innerHTML = renderRecursiveDescentView(state.lastRDParse);
                break;

            default:
                break;
        }
    }

    // ==========================================
    // Action Handlers
    // ==========================================

    async function handleValidateGrammar() {
        if (!grammarEditor || !parserLabContent) return;
        const grammarText = grammarEditor.value;
        const startSymbol = grammarStartSymbol ? grammarStartSymbol.value.trim() : null;

        setGrammarStatus("running", "Validating...");
        parserLabContent.innerHTML = `
            <div class="parser-lab-loading">
                <span class="status-dot" aria-hidden="true"></span>
                <span>Validating grammar structure and symbol conventions...</span>
            </div>
        `;

        try {
            const data = await callParserLabAPI("/api/parser-lab/validate", {
                grammar: grammarText,
                start_symbol: startSymbol || null
            });

            state.lastValidation = data;

            if (data.valid) {
                setGrammarStatus("success", "Grammar Valid");
            } else {
                setGrammarStatus("error", "Validation Errors");
            }

            setActiveTab("grammar");
        } catch (error) {
            setGrammarStatus("error", "Failed");
            parserLabContent.innerHTML = `
                <div class="semantic-status error">✕ Validation Request Failed</div>
                <div class="semantic-error">
                    <strong>Error:</strong>
                    <p>${escapeHTML(error.message)}</p>
                </div>
            `;
        }
    }

    async function handleComputeFirstFollow() {
        if (!grammarEditor || !parserLabContent) return;
        const grammarText = grammarEditor.value;
        const startSymbol = grammarStartSymbol ? grammarStartSymbol.value.trim() : null;

        setGrammarStatus("running", "Computing Sets...");
        parserLabContent.innerHTML = `
            <div class="parser-lab-loading">
                <span class="status-dot" aria-hidden="true"></span>
                <span>Validating grammar and computing iterative fixed-point FIRST &amp; FOLLOW sets...</span>
            </div>
        `;

        try {
            const data = await callParserLabAPI("/api/parser-lab/first-follow", {
                grammar: grammarText,
                start_symbol: startSymbol || null
            });

            state.lastFirstFollow = data;
            state.lastValidation = data;

            if (data.valid) {
                setGrammarStatus("success", "Sets Computed");
            } else {
                setGrammarStatus("error", "Validation Errors");
            }

            setActiveTab("first-follow");
        } catch (error) {
            setGrammarStatus("error", "Failed");
            parserLabContent.innerHTML = `
                <div class="semantic-status error">✕ Computation Request Failed</div>
                <div class="semantic-error">
                    <strong>Error:</strong>
                    <p>${escapeHTML(error.message)}</p>
                </div>
            `;
        }
    }

    async function handleGenerateLL1Table() {
        if (!grammarEditor || !parserLabContent) return;
        const grammarText = grammarEditor.value;
        const startSymbol = grammarStartSymbol ? grammarStartSymbol.value.trim() : null;

        setGrammarStatus("running", "Generating LL(1) Table...");
        parserLabContent.innerHTML = `
            <div class="parser-lab-loading">
                <span class="status-dot" aria-hidden="true"></span>
                <span>Computing FIRST/FOLLOW and populating predictive table M[A, a]...</span>
            </div>
        `;

        try {
            const data = await callParserLabAPI("/api/parser-lab/ll1/table", {
                grammar: grammarText,
                start_symbol: startSymbol || null
            });

            state.lastLL1Table = data;

            if (data.is_ll1) {
                setGrammarStatus("success", "LL(1) Table Ready");
            } else {
                setGrammarStatus("error", "Non-LL(1) Conflicts");
            }

            setActiveTab("ll1-table");
        } catch (error) {
            setGrammarStatus("error", "Failed");
            parserLabContent.innerHTML = `
                <div class="semantic-status error">✕ LL(1) Table Generation Failed</div>
                <div class="semantic-error">
                    <strong>Error:</strong>
                    <p>${escapeHTML(error.message)}</p>
                </div>
            `;
        }
    }

    async function handleParseInput() {
        if (!grammarEditor || !parserLabContent) return;
        const grammarText = grammarEditor.value;
        const startSymbol = grammarStartSymbol ? grammarStartSymbol.value.trim() : null;
        const inputText = parserInputString ? parserInputString.value.trim() : "";
        const engine = parserEngineSelect ? parserEngineSelect.value : "ll1";

        setGrammarStatus("running", "Parsing input tokens...");
        parserLabContent.innerHTML = `
            <div class="parser-lab-loading">
                <span class="status-dot" aria-hidden="true"></span>
                <span>Executing ${engine === "ll1" ? "LL(1) predictive" : "recursive descent"} parse on input tokens...</span>
            </div>
        `;

        try {
            if (engine === "ll1") {
                const data = await callParserLabAPI("/api/parser-lab/ll1/parse", {
                    grammar: grammarText,
                    start_symbol: startSymbol || null,
                    input: inputText
                });

                state.lastLL1Parse = data;
                state.lastParseTree = data.parse_tree || null;

                if (data.accepted) {
                    setGrammarStatus("success", "Accepted");
                } else {
                    setGrammarStatus("error", "Rejected");
                }

                setActiveTab("trace");
            } else {
                // Recursive descent
                const data = await callParserLabAPI("/api/parser-lab/recursive-descent/parse", {
                    grammar: grammarText,
                    start_symbol: startSymbol || null,
                    input: inputText
                });

                state.lastRDParse = data;
                state.lastParseTree = data.parse_tree || null;

                if (data.accepted) {
                    setGrammarStatus("success", "Accepted");
                } else {
                    setGrammarStatus("error", "Rejected");
                }

                setActiveTab("recursive-descent");
            }
        } catch (error) {
            setGrammarStatus("error", "Failed");
            parserLabContent.innerHTML = `
                <div class="semantic-status error">✕ Parse Request Failed</div>
                <div class="semantic-error">
                    <strong>Error:</strong>
                    <p>${escapeHTML(error.message)}</p>
                </div>
            `;
        }
    }

    if (btnValidateGrammar) {
        btnValidateGrammar.addEventListener("click", handleValidateGrammar);
    }
    if (btnComputeFirstFollow) {
        btnComputeFirstFollow.addEventListener("click", handleComputeFirstFollow);
    }
    if (btnGenerateLL1Table) {
        btnGenerateLL1Table.addEventListener("click", handleGenerateLL1Table);
    }
    if (btnParseInput) {
        btnParseInput.addEventListener("click", handleParseInput);
    }

    // ========================================================================
    // Phase 3: Bottom-Up Parsing Controller (SLR(1), CLR(1), LALR(1))
    // ========================================================================

    const buGrammarEditor = document.getElementById("bu-grammar-editor");
    const buGrammarLineNumbers = document.getElementById("bu-grammar-line-numbers");
    const buGrammarPresetSelect = document.getElementById("bu-grammar-preset-select");
    const buGrammarStartSymbol = document.getElementById("bu-grammar-start-symbol");
    const buParserInputString = document.getElementById("bu-parser-input-string");
    const buParserEngineSelect = document.getElementById("bu-parser-engine-select");

    const buBtnValidate = document.getElementById("bu-btn-validate-grammar");
    const buBtnGenerateItems = document.getElementById("bu-btn-generate-items");
    const buBtnGenerateTable = document.getElementById("bu-btn-generate-table");
    const buBtnParseInput = document.getElementById("bu-btn-parse-input");

    const buStatusPill = document.getElementById("bu-status-pill");
    const buStatusText = document.getElementById("bu-status-text");
    const buViewTitle = document.getElementById("bu-view-title");
    const buContent = document.getElementById("bu-content");
    const buTabNav = document.querySelector('#bottom-up-workspace .parser-lab-tab-nav');
    const buTabMerged = document.getElementById("bu-tab-merged");

    const buPresets = {
        bu_expr: {
            start: "E",
            grammar: "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id",
            input: "id + id * id",
            engine: "slr1"
        },
        bu_classic_lalr: {
            start: "S",
            grammar: "S -> a A d | b A e | a B e | b B d\nA -> c\nB -> c",
            input: "a c d",
            engine: "clr1"
        },
        bu_slr_conflict: {
            start: "S",
            grammar: "S -> L = R | R\nL -> * R | id\nR -> L",
            input: "id = id",
            engine: "slr1"
        },
        bu_simple_epsilon: {
            start: "S",
            grammar: "S -> a A b\nA -> eps",
            input: "a b",
            engine: "slr1"
        }
    };

    const buState = {
        activeTab: "grammar",
        lastValidation: null,
        lastItems: null,
        lastTable: null,
        lastParse: null,
        lastEngine: "slr1"
    };

    function setBUStatus(type, text) {
        if (!buStatusPill || !buStatusText) return;
        buStatusPill.className = "compiler-status";
        if (type === "busy") buStatusPill.classList.add("busy");
        if (type === "error") buStatusPill.classList.add("error");
        if (type === "success") buStatusPill.classList.add("success");
        buStatusText.textContent = text;
    }

    function updateBULineNumbers() {
        if (!buGrammarEditor || !buGrammarLineNumbers) return;
        const lines = buGrammarEditor.value.split("\n").length;
        buGrammarLineNumbers.textContent = Array.from(
            { length: lines },
            (_, i) => i + 1
        ).join("\n");
    }

    if (buGrammarEditor) {
        buGrammarEditor.addEventListener("input", function () {
            updateBULineNumbers();
            if (buGrammarPresetSelect) {
                buGrammarPresetSelect.value = "bu_custom";
            }
        });

        buGrammarEditor.addEventListener("scroll", function () {
            if (buGrammarLineNumbers) {
                buGrammarLineNumbers.scrollTop = buGrammarEditor.scrollTop;
            }
        });
    }

    if (buGrammarPresetSelect) {
        buGrammarPresetSelect.addEventListener("change", function () {
            const key = buGrammarPresetSelect.value;
            const preset = buPresets[key];
            if (!preset) return;

            if (buGrammarEditor) buGrammarEditor.value = preset.grammar;
            if (buGrammarStartSymbol) buGrammarStartSymbol.value = preset.start;
            if (buParserInputString) buParserInputString.value = preset.input;
            if (buParserEngineSelect) {
                buParserEngineSelect.value = preset.engine;
                updateBUEngineTab();
            }

            updateBULineNumbers();
            setBUStatus("ready", "Preset Loaded");
        });
    }

    function updateBUEngineTab() {
        const engine = buParserEngineSelect ? buParserEngineSelect.value : "slr1";
        if (buTabMerged) {
            buTabMerged.style.display = engine === "lalr1" ? "inline-flex" : "none";
        }
    }

    if (buParserEngineSelect) {
        buParserEngineSelect.addEventListener("change", updateBUEngineTab);
    }

    function setBUActiveTab(tabName) {
        buState.activeTab = tabName;
        if (buTabNav) {
            const btns = buTabNav.querySelectorAll(".lab-tab-btn");
            btns.forEach(b => {
                const isCurrent = b.getAttribute("data-bu-view") === tabName;
                b.classList.toggle("active", isCurrent);
            });
        }

        const titleMap = {
            grammar: "Grammar Specification & Productions",
            items: "Canonical LR Item Sets",
            graph: "State Transition Diagram",
            "action-table": "ACTION Parsing Table",
            "goto-table": "GOTO Parsing Table",
            conflicts: "Parsing Conflict Diagnostics",
            trace: "Shift-Reduce Parsing Trace",
            tree: "Concrete Syntax Parse Tree",
            merged: "LALR(1) Merged States & Rationale"
        };
        if (buViewTitle) {
            buViewTitle.textContent = titleMap[tabName] || "Bottom-Up LR Parsing";
        }

        renderBUViewContent();
    }

    if (buTabNav) {
        buTabNav.addEventListener("click", function (evt) {
            const btn = evt.target.closest(".lab-tab-btn");
            if (!btn) return;
            const view = btn.getAttribute("data-bu-view");
            if (view) {
                setBUActiveTab(view);
            }
        });
    }

    function renderBUViewContent() {
        if (!buContent) return;

        switch (buState.activeTab) {
            case "grammar":
                buContent.innerHTML = renderBUGrammarView(buState.lastValidation || buState.lastTable || buState.lastItems);
                break;
            case "items":
                buContent.innerHTML = renderBUItemsView(buState.lastItems || buState.lastTable);
                break;
            case "graph":
                buContent.innerHTML = renderBUTransitionDiagramView(buState.lastItems || buState.lastTable);
                break;
            case "action-table":
                buContent.innerHTML = renderBUActionTableView(buState.lastTable);
                break;
            case "goto-table":
                buContent.innerHTML = renderBUGotoTableView(buState.lastTable);
                break;
            case "conflicts":
                buContent.innerHTML = renderBUConflictsView(buState.lastTable);
                break;
            case "trace":
                buContent.innerHTML = renderBUTraceView(buState.lastParse);
                break;
            case "tree":
                buContent.innerHTML = renderParseTreeView(buState.lastParse ? buState.lastParse.parse_tree : null);
                break;
            case "merged":
                buContent.innerHTML = renderBUMergedView(buState.lastTable || buState.lastItems);
                break;
            default:
                buContent.innerHTML = renderBUGrammarView(buState.lastValidation);
        }
    }

    function renderBUGrammarView(data) {
        if (!data) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No Grammar Analysis Data Available</h3>
                    <p>Click <strong>Validate</strong>, <strong>Item Sets</strong>, or <strong>Generate Table</strong> on the left.</p>
                </div>
            `;
        }

        const productions = data.productions || [];
        const terminals = data.terminals || [];
        const nonterminals = data.nonterminals || [];
        const diagnostics = data.diagnostics || [];

        const diagHtml = diagnostics.map(d => `
            <div class="semantic-diagnostic ${escapeHTML(d.severity)}">
                <span class="diagnostic-severity-pill">${escapeHTML(d.severity.toUpperCase())}</span>
                <span class="diagnostic-line">Line ${d.line || 1}:</span>
                <span class="diagnostic-msg">${escapeHTML(d.message)}</span>
            </div>
        `).join("");

        const prodsHtml = productions.map((p, idx) => {
            const rhs = (p.rhs || []).join(" ") || "ε";
            return `
                <div class="rule-card">
                    <span class="rule-index">(${p.id !== undefined ? p.id : idx})</span>
                    <strong class="rule-lhs">${escapeHTML(p.lhs)}</strong>
                    <span class="rule-arrow">➔</span>
                    <span class="rule-rhs">${escapeHTML(rhs)}</span>
                </div>
            `;
        }).join("");

        const termPills = terminals.map(t =>
            `<span class="symbol-pill symbol-pill-terminal">${escapeHTML(t)}</span>`
        ).join(" ") || "<em>None</em>";

        const nontermPills = nonterminals.map(nt =>
            `<span class="symbol-pill symbol-pill-nonterminal">${escapeHTML(nt)}</span>`
        ).join(" ") || "<em>None</em>";

        return `
            <div class="parser-lab-metrics-grid">
                <div class="metric-card">
                    <span class="metric-num">${escapeHTML(data.start_symbol || "—")}</span>
                    <span class="metric-label">Start Symbol</span>
                </div>
                <div class="metric-card">
                    <span class="metric-num">${nonterminals.length}</span>
                    <span class="metric-label">Nonterminals</span>
                </div>
                <div class="metric-card">
                    <span class="metric-num">${terminals.length}</span>
                    <span class="metric-label">Terminals</span>
                </div>
                <div class="metric-card">
                    <span class="metric-num">${productions.length}</span>
                    <span class="metric-label">Productions</span>
                </div>
            </div>

            ${diagnostics.length > 0 ? `<div class="diagnostics-container" style="margin-top: 14px;">${diagHtml}</div>` : ""}

            <div class="grammar-summary-card" style="margin-top: 16px;">
                <h4 style="margin: 0 0 10px 0; font-size: 13px; color: var(--text-primary);">Augmented &amp; Numbered Grammar Productions</h4>
                <div class="rules-container">${prodsHtml}</div>
            </div>

            <div class="grammar-summary-card" style="margin-top: 14px;">
                <h4 style="margin: 0 0 10px 0; font-size: 13px; color: var(--text-primary);">Grammar Vocabulary Symbols</h4>
                <div style="margin-bottom: 8px; font-size: 12px;"><strong>Terminals (V_T):</strong> ${termPills}</div>
                <div style="font-size: 12px;"><strong>Nonterminals (V_N):</strong> ${nontermPills}</div>
            </div>
        `;
    }

    function renderBUItemsView(data) {
        if (!data || !data.item_sets || data.item_sets.length === 0) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No Canonical LR Item Sets Generated</h3>
                    <p>Click <strong>Generate Item Sets</strong> on the left to compute the canonical collection of LR item sets.</p>
                </div>
            `;
        }

        const itemSets = data.item_sets;
        const algo = data.algorithm || buParserEngineSelect.value.toUpperCase();

        const cardsHtml = itemSets.map(itSet => {
            const sid = itSet.state_id;
            const items = itSet.items || [];
            const trans = itSet.transitions || {};
            const mergedInfo = itSet.merged_info;
            const isMerged = mergedInfo && mergedInfo.was_merged;

            const itemsListHtml = items.map(line => {
                // Style dot and lookahead
                let formatted = escapeHTML(line)
                    .replace(/•/g, '<span class="lr-dot">•</span>')
                    .replace(/\[(.*),\s*(.*)\]/g, (match, body, lh) => {
                        return `${body} <span class="lr-lookahead-badge">${lh}</span>`;
                    });
                return `<li class="lr-item-row">${formatted}</li>`;
            }).join("");

            const transPills = Object.keys(trans).sort().map(sym => {
                const target = trans[sym];
                const isNt = sym[0] === sym[0].toUpperCase() && sym !== "$";
                return `<span class="lr-trans-pill ${isNt ? 'trans-nt' : 'trans-term'}">${escapeHTML(sym)} ➔ I${target}</span>`;
            }).join(" ") || "<em>No outgoing transitions (Accepting / Reduction State)</em>";

            return `
                <div class="lr-item-set-card">
                    <div class="lr-item-set-header">
                        <span class="lr-state-badge ${isMerged ? 'is-merged' : ''}">
                            State I${sid} ${isMerged ? `[Merged: ${mergedInfo.merged_from_clr_states.join(', ')}]` : ''}
                        </span>
                        <span style="font-size: 11px; color: var(--text-muted);">${items.length} item(s)</span>
                    </div>
                    <ul class="lr-items-list">${itemsListHtml}</ul>
                    <div class="lr-transitions-wrap">
                        <div class="lr-trans-title">Outgoing Transitions</div>
                        <div class="lr-trans-list">${transPills}</div>
                    </div>
                </div>
            `;
        }).join("");

        return `
            <div class="semantic-status success" style="margin-bottom: 14px;">
                ✓ Canonical Collection of ${itemSets.length} ${escapeHTML(algo)} Item Sets Generated Successfully
            </div>
            <div class="lr-items-grid">${cardsHtml}</div>
        `;
    }

    function renderBUTransitionDiagramView(data) {
        if (!data || !data.item_sets || data.item_sets.length === 0) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No State Transition Data Available</h3>
                    <p>Click <strong>Generate Item Sets</strong> or <strong>Generate Table</strong> to view the transition graph.</p>
                </div>
            `;
        }

        const itemSets = data.item_sets;
        const totalTransitions = (data.transitions || []).length;

        const nodesHtml = itemSets.map(itSet => {
            const sid = itSet.state_id;
            const trans = itSet.transitions || {};
            const keys = Object.keys(trans).sort();

            if (keys.length === 0) {
                return `
                    <div class="lr-diagram-node">
                        <div class="lr-diagram-node-header">
                            <span>State I${sid}</span>
                            <span class="badge-accept" style="font-size: 10px;">End / Reduce</span>
                        </div>
                        <div style="font-size: 11.5px; color: var(--text-muted);">No outgoing transitions</div>
                    </div>
                `;
            }

            const arrowsHtml = keys.map(sym => {
                const target = trans[sym];
                const isNt = sym[0] === sym[0].toUpperCase() && sym !== "$";
                return `
                    <div class="lr-arrow-row">
                        <span class="${isNt ? 'trans-nt' : 'trans-term'}" style="font-weight: 700;">${escapeHTML(sym)}</span>
                        <span>➔ <strong>State I${target}</strong></span>
                    </div>
                `;
            }).join("");

            return `
                <div class="lr-diagram-node">
                    <div class="lr-diagram-node-header">
                        <span>State I${sid}</span>
                        <span style="font-size: 11px; color: var(--text-muted);">${keys.length} transition(s)</span>
                    </div>
                    <div class="lr-diagram-arrows">${arrowsHtml}</div>
                </div>
            `;
        }).join("");

        return `
            <div class="parser-lab-metrics-grid" style="margin-bottom: 16px;">
                <div class="metric-card">
                    <span class="metric-num">${itemSets.length}</span>
                    <span class="metric-label">Total States</span>
                </div>
                <div class="metric-card">
                    <span class="metric-num">${totalTransitions}</span>
                    <span class="metric-label">Directed Transitions</span>
                </div>
            </div>
            <div class="lr-diagram-grid">${nodesHtml}</div>
        `;
    }

    function renderBUActionTableView(data) {
        if (!data || !data.action_table) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No ACTION Table Generated</h3>
                    <p>Click <strong>Generate Table</strong> on the left to compute the LR ACTION table with conflict diagnostics.</p>
                </div>
            `;
        }

        const terminals = data.terminals || [];
        const actionTable = data.action_table || {};
        const statesCount = data.states_count || Object.keys(actionTable).length;
        const conflicts = data.conflicts || [];
        const isValid = data.is_valid !== undefined ? data.is_valid : conflicts.length === 0;
        const algo = data.algorithm || buParserEngineSelect.value.toUpperCase();

        const banner = isValid
            ? `<div class="semantic-status success">✓ Valid ${escapeHTML(algo)}: ACTION Table contains 0 conflicts.</div>`
            : `<div class="semantic-status error">✕ Conflict Alert: ${conflicts.length} unresolved conflict(s) detected in ${escapeHTML(algo)} ACTION table.</div>`;

        const thCols = terminals.map(t =>
            `<th><code>${escapeHTML(t)}</code></th>`
        ).join("");

        let bodyRows = "";
        for (let i = 0; i < statesCount; i++) {
            const rowData = actionTable[String(i)] || {};
            const cellTds = terminals.map(term => {
                const actions = rowData[term] || [];
                if (actions.length === 0) {
                    return `<td class="cell-empty">—</td>`;
                }
                const hasConflict = actions.length > 1;
                const cellClass = hasConflict ? "cell-conflict" : "cell-rule";

                const badgesHtml = actions.map(act => {
                    if (act.type === "shift") {
                        return `<span class="badge-shift">s${act.target}</span>`;
                    } else if (act.type === "reduce") {
                        const title = act.production ? ` title="${escapeHTML(act.production)}"` : "";
                        return `<span class="badge-reduce"${title}>r${act.target}</span>`;
                    } else if (act.type === "accept") {
                        return `<span class="badge-accept">acc</span>`;
                    }
                    return `<span class="badge-shift">${escapeHTML(act.display || "")}</span>`;
                }).join(" ");

                return `
                    <td class="${cellClass}">
                        ${hasConflict ? `<span class="conflict-badge">CONFLICT</span><br>` : ""}
                        ${badgesHtml}
                    </td>
                `;
            }).join("");

            bodyRows += `
                <tr>
                    <td class="nt-row-header"><strong><code>I${i}</code></strong></td>
                    ${cellTds}
                </tr>
            `;
        }

        return `
            ${banner}
            <div class="ll1-table-wrapper" style="margin-top: 14px;">
                <table class="ll1-table">
                    <thead>
                        <tr>
                            <th class="nt-col-header" style="width: 80px;">State</th>
                            ${thCols}
                        </tr>
                    </thead>
                    <tbody>
                        ${bodyRows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderBUGotoTableView(data) {
        if (!data || !data.goto_table) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No GOTO Table Generated</h3>
                    <p>Click <strong>Generate Table</strong> on the left to compute the LR GOTO table.</p>
                </div>
            `;
        }

        const nonterminals = data.nonterminals || [];
        const gotoTable = data.goto_table || {};
        const statesCount = data.states_count || Object.keys(gotoTable).length;

        const thCols = nonterminals.map(nt =>
            `<th><code>${escapeHTML(nt)}</code></th>`
        ).join("");

        let bodyRows = "";
        for (let i = 0; i < statesCount; i++) {
            const rowData = gotoTable[String(i)] || {};
            const cellTds = nonterminals.map(nt => {
                const target = rowData[nt];
                if (target !== undefined && target !== null) {
                    return `<td class="cell-rule"><span class="badge-goto-target">${target}</span></td>`;
                }
                return `<td class="cell-empty">—</td>`;
            }).join("");

            bodyRows += `
                <tr>
                    <td class="nt-row-header"><strong><code>I${i}</code></strong></td>
                    ${cellTds}
                </tr>
            `;
        }

        return `
            <div class="semantic-status success" style="margin-bottom: 14px;">
                ✓ GOTO Table for Nonterminals across ${statesCount} States
            </div>
            <div class="ll1-table-wrapper">
                <table class="ll1-table">
                    <thead>
                        <tr>
                            <th class="nt-col-header" style="width: 80px;">State</th>
                            ${thCols}
                        </tr>
                    </thead>
                    <tbody>
                        ${bodyRows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderBUConflictsView(data) {
        if (!data || !data.conflicts) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No Conflict Analysis Run</h3>
                    <p>Click <strong>Generate Table</strong> to inspect whether the grammar is SLR(1), CLR(1), or LALR(1) conflict-free.</p>
                </div>
            `;
        }

        const conflicts = data.conflicts;
        const algo = data.algorithm || buParserEngineSelect.value.toUpperCase();

        if (conflicts.length === 0) {
            return `
                <div class="semantic-status success">
                    ✓ Clean Grammar: 0 Shift/Reduce and 0 Reduce/Reduce conflicts detected! Grammar is valid ${escapeHTML(algo)}.
                </div>
            `;
        }

        const cardsHtml = conflicts.map(c => `
            <div class="lr-conflict-card">
                <div class="lr-conflict-header">
                    <span>⚠️ ${escapeHTML(c.conflict_type)} Conflict</span>
                    <span>State I${c.state_id} on symbol '${escapeHTML(c.symbol)}'</span>
                </div>
                <div class="lr-conflict-body">${escapeHTML(c.message)}</div>
                ${c.items && c.items.length > 0 ? `
                    <div class="lr-conflict-items-box">
                        <strong>Items in State I${c.state_id}:</strong><br>
                        ${c.items.map(it => escapeHTML(it)).join("<br>")}
                    </div>
                ` : ""}
            </div>
        `).join("");

        return `
            <div class="semantic-status error" style="margin-bottom: 14px;">
                ✕ ${conflicts.length} Unresolved ${escapeHTML(algo)} Conflict(s) Detected
            </div>
            ${cardsHtml}
        `;
    }

    function renderBUTraceView(data) {
        if (!data) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No Parsing Execution Trace Available</h3>
                    <p>Enter an input string on the left (e.g. <code>id + id * id</code>) and click <strong>Parse Input</strong>.</p>
                </div>
            `;
        }

        const accepted = data.accepted;
        const tokens = data.tokens || [];
        const trace = data.trace || [];
        const error = data.error;

        const tokenPills = tokens.map(t =>
            `<span class="symbol-pill symbol-pill-terminal">${escapeHTML(t)}</span>`
        ).join(" ") + ` <span class="symbol-pill symbol-pill-end">$</span>`;

        const statusBanner = accepted
            ? `<div class="semantic-status success">✓ Input Accepted — Bottom-Up Shift-Reduce Derivation Completed!</div>`
            : `<div class="semantic-status error">✕ Parsing Rejected — ${escapeHTML(error || "Syntax error during parsing.")}</div>`;

        const traceRows = trace.map(s => {
            const stateStr = (s.state_stack || []).map(x => `I${x}`).join(" ");
            const symStr = (s.symbol_stack || []).map(x => escapeHTML(x)).join(" ") || "—";
            const remStr = (s.remaining_input || []).map(x => escapeHTML(x)).join(" ");
            const actionBadgeClass = `trace-action-${s.status || "shift"}`;
            const rowClass = `trace-step-${s.status || "shift"}`;

            return `
                <tr class="${rowClass}">
                    <td style="width: 50px;">${s.step}</td>
                    <td style="font-weight: 600;"><code>${stateStr}</code></td>
                    <td><code>${symStr}</code></td>
                    <td><code>${remStr}</code></td>
                    <td>
                        <span class="trace-action-badge ${actionBadgeClass}">${escapeHTML(s.action)}</span>
                    </td>
                </tr>
            `;
        }).join("");

        return `
            ${statusBanner}
            <div style="margin: 12px 0; font-size: 12px;">
                <strong>Tokenized Input Stream:</strong> ${tokenPills}
            </div>
            <div class="trace-table-wrapper">
                <table class="trace-table">
                    <thead>
                        <tr>
                            <th style="width: 45px;">#</th>
                            <th>State Stack</th>
                            <th>Symbol Stack</th>
                            <th>Remaining Input</th>
                            <th>Action &amp; Rule Applied</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${traceRows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderBUMergedView(data) {
        if (!data || !data.merged_states_info) {
            return `
                <div class="parser-lab-empty-state">
                    <h3>No LALR State Merging Data Available</h3>
                    <p>Select <strong>LALR(1)</strong> as the LR engine and click <strong>Generate Table</strong> or <strong>Item Sets</strong>.</p>
                </div>
            `;
        }

        const mergedInfo = data.merged_states_info;
        const cardsHtml = mergedInfo.map(info => {
            const wasMerged = info.was_merged;
            return `
                <div class="lr-merged-card ${wasMerged ? 'is-multi-merged' : ''}">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span class="lr-state-badge ${wasMerged ? 'is-merged' : ''}">
                            LALR State I${info.lalr_state_id}
                        </span>
                        <span style="font-size: 11px; font-weight: 700; color: ${wasMerged ? '#d97706' : 'var(--text-muted)'};">
                            ${wasMerged ? `Merged from ${info.merged_from_clr_states.length} CLR states` : 'Single CLR State'}
                        </span>
                    </div>
                    <div style="font-size: 12.5px; color: var(--text-primary); margin-bottom: 8px;">
                        ${escapeHTML(info.explanation)}
                    </div>
                    <div class="lr-conflict-items-box">
                        <strong>Shared LR(0) Core Items:</strong><br>
                        ${(info.core_items || []).map(it => escapeHTML(it)).join("<br>")}
                    </div>
                </div>
            `;
        }).join("");

        return `
            <div class="semantic-status success" style="margin-bottom: 14px;">
                ✓ LALR(1) State Merging Breakdown (${mergedInfo.length} Merged States)
            </div>
            <div class="lr-merged-grid">${cardsHtml}</div>
        `;
    }

    // Bottom-Up Action Handlers
    async function handleBUValidateGrammar() {
        const text = buGrammarEditor ? buGrammarEditor.value : "";
        const start = buGrammarStartSymbol ? buGrammarStartSymbol.value.trim() : "";

        setBUStatus("busy", "Validating...");
        try {
            const data = await callParserLabAPI("/api/parser-lab/validate", {
                grammar: text,
                start_symbol: start || null
            });

            buState.lastValidation = data;
            if (data.valid) {
                setBUStatus("success", "Valid Grammar");
            } else {
                setBUStatus("error", "Invalid Grammar");
            }

            setBUActiveTab("grammar");
        } catch (error) {
            setBUStatus("error", "Validation Failed");
            if (buContent) {
                buContent.innerHTML = `
                    <div class="semantic-status error">✕ Validation Error</div>
                    <div class="semantic-error">
                        <strong>Error:</strong>
                        <p>${escapeHTML(error.message)}</p>
                    </div>
                `;
            }
        }
    }

    async function handleBUGenerateItems() {
        const text = buGrammarEditor ? buGrammarEditor.value : "";
        const start = buGrammarStartSymbol ? buGrammarStartSymbol.value.trim() : "";
        const engine = buParserEngineSelect ? buParserEngineSelect.value : "slr1";

        setBUStatus("busy", `Generating ${engine.toUpperCase()} Items...`);
        try {
            const data = await callParserLabAPI(`/api/parser-lab/${engine}/items`, {
                grammar: text,
                start_symbol: start || null
            });

            buState.lastItems = data;
            setBUStatus("success", `${data.states_count} States`);
            setBUActiveTab("items");
        } catch (error) {
            setBUStatus("error", "Item Sets Failed");
            if (buContent) {
                buContent.innerHTML = `
                    <div class="semantic-status error">✕ Item Sets Generation Failed</div>
                    <div class="semantic-error">
                        <strong>Error:</strong>
                        <p>${escapeHTML(error.message)}</p>
                    </div>
                `;
            }
        }
    }

    async function handleBUGenerateTable() {
        const text = buGrammarEditor ? buGrammarEditor.value : "";
        const start = buGrammarStartSymbol ? buGrammarStartSymbol.value.trim() : "";
        const engine = buParserEngineSelect ? buParserEngineSelect.value : "slr1";

        setBUStatus("busy", `Generating ${engine.toUpperCase()} Table...`);
        try {
            const data = await callParserLabAPI(`/api/parser-lab/${engine}/table`, {
                grammar: text,
                start_symbol: start || null
            });

            buState.lastTable = data;
            if (data.is_valid) {
                setBUStatus("success", `${engine.toUpperCase()} Table Ready`);
            } else {
                setBUStatus("error", `${data.conflicts.length} Conflicts`);
            }

            setBUActiveTab("action-table");
        } catch (error) {
            setBUStatus("error", "Table Failed");
            if (buContent) {
                buContent.innerHTML = `
                    <div class="semantic-status error">✕ Table Generation Failed</div>
                    <div class="semantic-error">
                        <strong>Error:</strong>
                        <p>${escapeHTML(error.message)}</p>
                    </div>
                `;
            }
        }
    }

    async function handleBUParseInput() {
        const text = buGrammarEditor ? buGrammarEditor.value : "";
        const start = buGrammarStartSymbol ? buGrammarStartSymbol.value.trim() : "";
        const inputStr = buParserInputString ? buParserInputString.value : "";
        const engine = buParserEngineSelect ? buParserEngineSelect.value : "slr1";

        setBUStatus("busy", `Parsing with ${engine.toUpperCase()}...`);
        try {
            const data = await callParserLabAPI(`/api/parser-lab/${engine}/parse`, {
                grammar: text,
                start_symbol: start || null,
                input: inputStr
            });

            buState.lastParse = data;
            if (data.accepted) {
                setBUStatus("success", "Accepted");
            } else {
                setBUStatus("error", "Rejected");
            }

            setBUActiveTab("trace");
        } catch (error) {
            setBUStatus("error", "Parse Failed");
            if (buContent) {
                buContent.innerHTML = `
                    <div class="semantic-status error">✕ Parse Request Failed</div>
                    <div class="semantic-error">
                        <strong>Error:</strong>
                        <p>${escapeHTML(error.message)}</p>
                    </div>
                `;
            }
        }
    }

    if (buBtnValidate) buBtnValidate.addEventListener("click", handleBUValidateGrammar);
    if (buBtnGenerateItems) buBtnGenerateItems.addEventListener("click", handleBUGenerateItems);
    if (buBtnGenerateTable) buBtnGenerateTable.addEventListener("click", handleBUGenerateTable);
    if (buBtnParseInput) buBtnParseInput.addEventListener("click", handleBUParseInput);

    updateBULineNumbers();
    updateBUEngineTab();

    // Initialize line numbers on load
    updateGrammarLineNumbers();
})();
