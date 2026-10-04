const sourceBox = document.getElementById("source-code");
const compileButton = document.getElementById("compile-button");
const visualization = document.getElementById("visualization");

let nextButton = document.getElementById("next-step-button");
const stageButtons = document.querySelectorAll(".stage[data-stage]");

if (!nextButton) {
    nextButton = document.createElement("button");
    nextButton.id = "next-step-button";
    nextButton.textContent = "Next Step →";
    visualization.parentElement.appendChild(nextButton);
}

let state = {
    step: 0,
    tokens: null,
    ast: null,
    astStatistics: null,
    tac: null,
    cfg: null,
    run: null
};


function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


async function api(endpoint) {

    const response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            source: sourceBox.value
        })
    });

    const data = await response.json();

    if (!response.ok || data.success === false) {
        const error = new Error(data.error || "Compiler stage failed");
        error.details = data.details || null;
        throw error;
    }

    return data;
}


/* =========================================================
   API
   ========================================================= */

async function getTokens() {
    return await api("/api/tokens");
}

async function getAST() {
    return await api("/api/parse");
}

async function getSemantic() {
    return await api("/api/semantic");
}

async function getTAC() {
    return await api("/api/tac");
}

async function getCFG() {
    return await api("/api/cfg");
}

async function getOptimized() {
    return await api("/api/optimize");
}

async function getRun() {
    return await api("/api/run");
}


/* =========================================================
   NORMALIZE AST
   ========================================================= */

function normalizeAST(data) {

    if (data && data.ast) {
        return data.ast;
    }

    return data;
}

function showSyntaxError(error) {
    const details = error.details || {};
    const context = details.source_context;

    visualization.innerHTML = `
        <div class="panel">
            <h2>Syntax Error</h2>
            <div class="semantic-status error">✗ Parser failed</div>
            <dl class="syntax-error-details">
                <dt>Unexpected token</dt>
                <dd>${escapeHTML(details.unexpected || "Unavailable")}</dd>
                <dt>Expected</dt>
                <dd>${escapeHTML(details.expected || "Unavailable")}</dd>
                <dt>Line</dt>
                <dd>${escapeHTML(details.line ?? "Unavailable")}</dd>
                <dt>Column</dt>
                <dd>${escapeHTML(details.column ?? "Unavailable")}</dd>
            </dl>
            ${context ? `<pre class="syntax-source">${escapeHTML(context)}</pre>` : ""}
        </div>
    `;
}

async function loadAST() {
    const result = await getAST();
    state.ast = normalizeAST(result);
    state.astStatistics = result.statistics || {};
    return result;
}


/* =========================================================
   SOURCE
   ========================================================= */

function showSource() {

    visualization.innerHTML = `
        <div class="panel">

            <h2>Source Program</h2>

            <p>
                MiniLang-X source code enters the compiler pipeline
                and is transformed through each compiler stage.
            </p>

            <pre class="source-preview">${escapeHTML(
                sourceBox.value
            )}</pre>

            <div class="semantic-status success">
                ✓ Source loaded successfully
            </div>

            <p>
                Click <strong>Next Step →</strong> to begin lexical
                analysis.
            </p>

        </div>
    `;
}


/* =========================================================
   LEXER
   ========================================================= */

function showLexer(data) {

    const tokens = Array.isArray(data)
        ? data
        : (data.tokens || []);
    const statistics = Array.isArray(data)
        ? {}
        : (data.statistics || {});
    const keywordTypes = new Set([
        "INT", "FLOAT", "BOOL", "STRING", "IF", "ELSE", "WHILE", "PRINT"
    ]);
    const literalTypes = new Set([
        "INTEGER", "FLOAT_LITERAL", "STRING_LITERAL", "TRUE", "FALSE"
    ]);
    const operatorTypes = new Set([
        "PLUS", "MINUS", "MULTIPLY", "DIVIDE", "ASSIGN", "EQUAL",
        "NOT_EQUAL", "LESS", "GREATER", "LESS_EQUAL", "GREATER_EQUAL", "NOT"
    ]);

    let rows = "";

    tokens.forEach(function(token, index) {

        const type =
            token.type?.name ||
            token.type ||
            "";

        const value =
            token.value ??
            token.lexeme ??
            "";
        const category = keywordTypes.has(type)
            ? "keywords"
            : type === "IDENTIFIER"
                ? "identifiers"
                : literalTypes.has(type)
                    ? "literals"
                    : operatorTypes.has(type)
                        ? "operators"
                        : "other";

        rows += `
            <tr data-token-category="${category}">
                <td>${index}</td>
                <td><code>${escapeHTML(type)}</code></td>
                <td><code>${escapeHTML(value)}</code></td>
                <td>${token.line ?? "-"}</td>
                <td>${token.column ?? "-"}</td>
            </tr>
        `;
    });

    visualization.innerHTML = `
        <div class="panel">

            <h2>LEXICAL ANALYSIS</h2>

            <p>
                The lexer converts source characters into tokens.
            </p>

            <div class="semantic-status success">
                ✓ Lexical analysis completed
            </div>

            <div class="lexer-statistics">
                <strong>Total Tokens: ${statistics.total_tokens ?? 0}</strong>
                <span>Identifiers: ${statistics.identifiers ?? 0}</span>
                <span>Keywords: ${statistics.keywords ?? 0}</span>
                <span>Literals: ${statistics.literals ?? 0}</span>
                <span>Operators: ${statistics.operators ?? 0}</span>
                <span>Separators: ${statistics.separators ?? 0}</span>
                <span>Comments: ${statistics.comments ?? 0}</span>
            </div>

            <div class="token-filters" aria-label="Filter tokens">
                <button type="button" class="token-filter active" data-filter="all">All</button>
                <button type="button" class="token-filter" data-filter="keywords">Keywords</button>
                <button type="button" class="token-filter" data-filter="identifiers">Identifiers</button>
                <button type="button" class="token-filter" data-filter="literals">Literals</button>
                <button type="button" class="token-filter" data-filter="operators">Operators</button>
            </div>

            <table class="token-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Type</th>
                        <th>Value</th>
                        <th>Line</th>
                        <th>Column</th>
                    </tr>
                </thead>

                <tbody>
                    ${rows}
                </tbody>
            </table>

        </div>
    `;

    visualization.querySelectorAll(".token-filter").forEach(function(button) {
        button.addEventListener("click", function() {
            const filter = button.dataset.filter;

            visualization.querySelectorAll(".token-filter").forEach(function(item) {
                item.classList.toggle("active", item === button);
            });

            visualization.querySelectorAll("[data-token-category]").forEach(function(row) {
                row.hidden = filter !== "all" &&
                    row.dataset.tokenCategory !== filter;
            });
        });
    });
}


/* =========================================================
   PARSER
   ========================================================= */

function showParser(parseResult) {
    const statistics = parseResult.statistics || {};

    visualization.innerHTML = `
        <div class="panel">

            <h2>Syntax Analysis</h2>

            <p>
                The parser checks the token sequence against the
                MiniLang-X grammar and builds a structured tree.
            </p>

            <div class="semantic-status success parser-status">
                ✓ Lexer completed &nbsp; ✓ Parser completed &nbsp; ✓ AST generated
            </div>

            <div class="parser-flow">

                <div class="parser-item">
                    Tokens
                    <small>${statistics.token_count ?? 0} source tokens</small>
                </div>

                <div class="parser-arrow">→</div>

                <div class="parser-item">Grammar</div>

                <div class="parser-arrow">→</div>

                <div class="parser-item">
                    AST
                    <small>${statistics.total_nodes ?? 0} nodes</small>
                </div>

            </div>

            <div class="ast-statistics">
                <strong>AST Statistics</strong>
                <span>Total nodes: ${statistics.total_nodes ?? 0}</span>
                <span>Maximum depth: ${statistics.max_depth ?? 0}</span>
                <span>Statements: ${statistics.statement_count ?? 0}</span>
                <span>Expressions: ${statistics.expression_count ?? 0}</span>
                <span>Identifiers: ${statistics.identifier_count ?? 0}</span>
                <span>Literals: ${statistics.literal_count ?? 0}</span>
                <span>Operators: ${statistics.operator_count ?? 0}</span>
            </div>

            <p>
                Continue to Operator Precedence to see how the parser grouped
                expressions, or select AST to inspect the complete syntax tree.
            </p>

        </div>
    `;
}


/* =========================================================
   PRECEDENCE
   ========================================================= */

function findExpression(node) {

    if (!node) {
        return null;
    }

    /*
     * Find the first actual expression in the AST.
     * For:
     *
     * int x = 10 + 20 * 3;
     *
     * this returns:
     *
     *        +
     *       / \
     *     10   *
     *         / \
     *        20  3
     */

    if (
        node.type === "BinaryExpression" ||
        node.type === "UnaryExpression"
    ) {
        return node;
    }

    const children = node.children || [];

    for (const child of children) {

        const expression =
            findExpression(child);

        if (expression) {
            return expression;
        }
    }

    return null;
}


function precedenceNodeLabel(node) {

    if (!node) {
        return "";
    }

    if (node.type === "BinaryExpression") {
        return node.operator;
    }

    if (node.type === "UnaryExpression") {
        return node.operator;
    }

    if (node.type === "Literal") {
        return String(node.value);
    }

    if (node.type === "Identifier") {
        return node.name;
    }

    return node.label ||
           node.name ||
           node.value ||
           node.type;
}


function precedenceNodeClass(node) {

    if (
        node.type === "BinaryExpression" ||
        node.type === "UnaryExpression"
    ) {
        return "precedence-svg-operator";
    }

    return "precedence-svg-leaf";
}


function drawPrecedenceTree(root) {

    /*
     * Fixed canvas.
     *
     * This makes the tree behave like a proper
     * compiler expression tree rather than a
     * collection of independently positioned boxes.
     */

    const width = 760;

    const nodeWidth = 105;
    const nodeHeight = 58;

    const verticalGap = 120;


    /*
     * Layout follows the parent/child structure:
     *
     *  - leaves are placed left to right in order,
     *  - each operator is centred above its own children,
     *  - depth determines the vertical position.
     *
     * So in  2 + 3 * 4  the nodes 3 and 4 sit under *,
     * and * sits under + next to 2.
     */

    const leaves = [];
    let maxDepth = 0;


    function collectLeaves(node, depth = 0) {

        maxDepth = Math.max(maxDepth, depth);

        const children =
            node.children || [];

        if (!children.length) {
            leaves.push(node);
            return;
        }

        children.forEach(child => {
            collectLeaves(child, depth + 1);
        });
    }


    collectLeaves(root);


    const height =
        110 + maxDepth * verticalGap;

    const leafSpacing =
        width / (leaves.length + 1);

    const positions = new Map();


    function place(node, depth = 0) {

        const children =
            node.children || [];

        let x;

        if (!children.length) {

            x = leafSpacing * (leaves.indexOf(node) + 1);

        } else {

            children.forEach(child => {
                place(child, depth + 1);
            });

            const childX =
                children.map(child => positions.get(child).x);

            x = (Math.min(...childX) + Math.max(...childX)) / 2;
        }

        positions.set(node, {
            x: x,
            y: 55 + depth * verticalGap
        });
    }


    place(root);


    let edges = "";
    let nodes = "";


    /*
     * Draw edges first so nodes appear above them.
     */

    function renderEdges(node) {

        const parent =
            positions.get(node);

        const children =
            node.children || [];


        children.forEach(function(child) {

            const childPosition =
                positions.get(child);

            if (!childPosition) {
                return;
            }


            edges += `
                <line
                    x1="${parent.x}"
                    y1="${parent.y + nodeHeight / 2}"
                    x2="${childPosition.x}"
                    y2="${childPosition.y - nodeHeight / 2}"
                    class="precedence-edge"
                    marker-end="url(#precedence-arrow)"
                />
            `;


            renderEdges(child);
        });
    }


    renderEdges(root);


    /*
     * Draw nodes.
     */

    positions.forEach(function(position, node) {

        const label =
            precedenceNodeLabel(node);

        const className =
            precedenceNodeClass(node);


        nodes += `
            <g>

                <rect
                    x="${position.x - nodeWidth / 2}"
                    y="${position.y - nodeHeight / 2}"
                    width="${nodeWidth}"
                    height="${nodeHeight}"
                    rx="10"
                    class="${className}"
                />

                <text
                    x="${position.x}"
                    y="${position.y + 7}"
                    text-anchor="middle"
                    class="precedence-svg-text"
                >
                    ${escapeHTML(label)}
                </text>

            </g>
        `;
    });


    return `
        <svg
            class="precedence-svg"
            viewBox="0 0 ${width} ${height}"
            preserveAspectRatio="xMidYMid meet"
        >

            <defs>

                <marker
                    id="precedence-arrow"
                    markerWidth="8"
                    markerHeight="8"
                    refX="7"
                    refY="4"
                    orient="auto"
                >

                    <path
                        d="M0,0 L8,4 L0,8 Z"
                        class="precedence-arrow-head"
                    />

                </marker>

            </defs>

            ${edges}

            ${nodes}

        </svg>
    `;
}


function showPrecedence(ast) {

    const expression =
        findExpression(ast);


    if (!expression) {

        visualization.innerHTML = `
            <div class="panel">

                <h2>Operator Precedence</h2>

                <div class="semantic-status error">
                    ✕ No expression found
                </div>

            </div>
        `;

        return;
    }


    const expressionLabel =
        buildExpressionText(expression);


    visualization.innerHTML = `
        <div class="panel">

            <h2>Operator Precedence</h2>

            <p>
                The precedence tree shows the order in which
                operators are grouped by the parser.
            </p>

            <div class="precedence-expression">

                <code>
                    ${escapeHTML(expressionLabel)}
                </code>

            </div>

            <div class="semantic-status success">

                ✓ Expression tree built by the parser

            </div>

            <div class="precedence-visual">

                ${drawPrecedenceTree(expression)}

            </div>

            <div class="precedence-result">

                <strong>Parsed structure:</strong>

                <code>
                    ${escapeHTML(expressionLabel)}
                </code>

            </div>

        </div>
    `;
}


function buildExpressionText(node) {

    if (!node) {
        return "";
    }


    if (node.type === "Literal") {
        return String(node.value);
    }


    if (node.type === "Identifier") {
        return node.name;
    }


    if (node.type === "UnaryExpression") {

        return (
            node.operator +
            buildExpressionText(node.operand || node.children?.[0])
        );
    }


    if (node.type === "BinaryExpression") {

        const children =
            node.children || [];

        /*
         * Parenthesise every binary node so the text shows
         * exactly how the parser grouped the operands:
         *
         *   2 + 3 * 4   ->  (2 + (3 * 4))
         *   10 - 2 - 3  ->  ((10 - 2) - 3)
         */

        if (children.length >= 2) {

            return (
                "(" +
                buildExpressionText(children[0]) +
                " " +
                node.operator +
                " " +
                buildExpressionText(children[1]) +
                ")"
            );
        }
    }


    return node.label || "";
}


/* =========================================================
   AST
   ========================================================= */

function astTreeHTML(node) {

    if (!node) {
        return "";
    }

    const children = node.children || [];

    const label = astNodeLabel(node);

    const detail = node.type || "";

    let html = `
        <div class="ast-node">

            <div class="ast-box ${escapeHTML(node.type || "")}" title="${escapeHTML(detail)}">
                <span>${escapeHTML(label)}</span>
                ${detail ? `<small>${escapeHTML(detail)}</small>` : ""}
            </div>
    `;


    if (children.length) {

        html += `
            <div class="ast-children">

                ${children.map(function(child) {
                    return `
                        <div class="ast-child">
                            ${astTreeHTML(child)}
                        </div>
                    `;
                }).join("")}

            </div>
        `;
    }

    function astNodeLabel(node) {
        switch (node.type) {
            case "VarDeclaration":
                return `Declaration: ${node.name} : ${node.data_type}`;
            case "Assignment":
                return `Assignment: ${node.name}`;
            case "PrintStatement":
                return "Print";
            case "IfStatement":
                return "If";
            case "WhileStatement":
                return "While";
            case "BinaryExpression":
                return `Binary: ${node.operator}`;
            case "UnaryExpression":
                return `Unary: ${node.operator}`;
            case "Literal":
                return `Literal: ${node.value} (${node.data_type})`;
            case "Identifier":
                return `Identifier: ${node.name}`;
            default:
                return node.label || node.type || "";
        }
    }


    html += `
        </div>
    `;

    return html;
}


function showAST(ast, statistics = {}) {

    visualization.innerHTML = `
        <div class="panel">

            <h2>Abstract Syntax Tree (AST)</h2>

            <p>
                The AST shows the hierarchical structure produced
                by the parser.
            </p>

            <div class="semantic-status success">
                ✓ AST generated successfully
            </div>

            <div class="ast-statistics">
                <strong>AST Statistics</strong>
                <span>Total nodes: ${statistics.total_nodes ?? 0}</span>
                <span>Maximum depth: ${statistics.max_depth ?? 0}</span>
                <span>Statements: ${statistics.statement_count ?? 0}</span>
                <span>Expressions: ${statistics.expression_count ?? 0}</span>
                <span>Identifiers: ${statistics.identifier_count ?? 0}</span>
                <span>Literals: ${statistics.literal_count ?? 0}</span>
                <span>Operators: ${statistics.operator_count ?? 0}</span>
            </div>

            <div class="ast-container" role="tree" aria-label="Abstract syntax tree">
                ${astTreeHTML(ast)}
            </div>

        </div>
    `;
}


/* =========================================================
   SEMANTIC
   ========================================================= */

function showSemantic(result) {
    const statistics = result.statistics || {};
    const symbols = result.symbols || [];
    const errors = result.errors || [];

    let rows = "";

    symbols.forEach(function(symbol) {
        const location = symbol.line && symbol.column
            ? `${symbol.line}:${symbol.column}`
            : "—";

        rows += `
            <tr>
                <td>${escapeHTML(symbol.name)}</td>
                <td>${escapeHTML(symbol.data_type)}</td>
                <td>${escapeHTML(symbol.scope || `scope ${symbol.scope_level}`)}</td>
                <td>${symbol.initialized ? "Yes" : "No"}</td>
                <td>${location}</td>
            </tr>
        `;
    });

    const errorDetails = result.error_details || errors[0] || {};
    const errorPanel = result.valid
        ? `
            <div class="semantic-status success">
                ✓ Semantic analysis completed
            </div>
            <p class="semantic-message">✓ No semantic errors · ✓ Symbol table generated</p>
        `
        : `
            <div class="semantic-status error">✕ Semantic analysis failed</div>
            <div class="semantic-error">
                <strong>${escapeHTML(errorDetails.type || "Semantic Error")}</strong>
                <p>${escapeHTML(errorDetails.message || result.error || "Semantic analysis failed.")}</p>
                ${errorDetails.line != null
                    ? `<p>Line: ${escapeHTML(errorDetails.line)}${errorDetails.column != null
                        ? `, Column: ${escapeHTML(errorDetails.column)}`
                        : ""}</p>`
                    : ""}
                ${errorDetails.source_context
                    ? `<pre class="semantic-source">${escapeHTML(errorDetails.source_context)}</pre>`
                    : ""}
            </div>
        `;

    visualization.innerHTML = `
        <div class="panel">

            <h2>Semantic Analysis</h2>

            <p>
                The semantic analyzer verifies declarations,
                scopes, types, and valid operations.
            </p>

            <div class="semantic-flow" aria-label="Semantic analysis flow">
                <span>AST</span><b>↓</b>
                <span>Symbol Table</span><b>↓</b>
                <span>Semantic Checks</span><b>↓</b>
                <span>Result</span>
            </div>

            ${errorPanel}

            <div class="semantic-statistics">
                <strong>Semantic Statistics</strong>
                <span>Symbols: ${statistics.symbol_count ?? symbols.length}</span>
                <span>Declarations: ${statistics.declaration_count ?? symbols.length}</span>
                <span>Identifier Uses: ${statistics.identifier_use_count ?? 0}</span>
                <span>Scopes: ${statistics.scope_count ?? 0}</span>
                <span>Errors: ${statistics.error_count ?? errors.length}</span>
                <span>Initialized: ${statistics.initialized_count ?? 0}</span>
            </div>

            <h3>Symbol Table</h3>
            <table class="token-table">

                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Scope</th>
                        <th>Initialized</th>
                        <th>Location</th>
                    </tr>
                </thead>

                <tbody>
                    ${rows || `<tr><td colspan="5">No symbols declared.</td></tr>`}
                </tbody>

            </table>

        </div>
    `;
}


/* =========================================================
   TAC
   ========================================================= */

function tacInstructionText(instruction) {

    /*
     * Format one TAC instruction from its structured fields,
     * using the real operation sent by the backend (op).
     */

    const op = instruction.op;
    const arg1 = instruction.arg1;
    const arg2 = instruction.arg2;
    const result = instruction.result;

    if (op === "LABEL") {
        return result + ":";
    }

    if (op === "GOTO") {
        return "goto " + result;
    }

    if (op === "IF_FALSE") {
        return "ifFalse " + arg1 + " goto " + result;
    }

    if (op === "IF_TRUE") {
        return "ifTrue " + arg1 + " goto " + result;
    }

    if (op === "PRINT") {
        return "print " + arg1;
    }

    if (op === "ASSIGN" || op === "UNARY") {
        return result + " = " + arg1;
    }

    if (arg2 !== null) {
        return result + " = " + arg1 + " " + op + " " + arg2;
    }

    return [op, arg1, arg2, result]
        .filter(part => part !== null)
        .join(" ");
}


function showTAC(result) {

    let rows = "";

    result.instructions.forEach(
        function(instruction, index) {
            rows += `
                <tr>
                    <td>
                        ${index}
                    </td>
                    <td><code>${escapeHTML(instruction.op)}</code></td>
                    <td><code>${escapeHTML(instruction.result ?? "—")}</code></td>
                    <td><code>${escapeHTML(instruction.arg1 ?? "—")}</code></td>
                    <td><code>${escapeHTML(instruction.arg2 ?? "—")}</code></td>
                </tr>
            `;
        }
    );

    const statistics = result.statistics || {};
    const temporaries = result.temporaries || [];
    const labels = result.labels || [];

    visualization.innerHTML = `
        <div class="panel">

            <h2>Three Address Code (TAC)</h2>

            <p>
                Three Address Code lowers expressions into simple
                instructions using a result and up to two operands.
            </p>

            <div class="semantic-status success">
                ✓ TAC generation completed
            </div>

            <div class="tac-statistics">
                <strong>TAC Statistics</strong>
                <span>Instructions: ${statistics.instruction_count ?? result.instructions.length}</span>
                <span>Temporaries: ${statistics.temporary_count ?? temporaries.length}</span>
                <span>Labels: ${statistics.label_count ?? labels.length}</span>
                <span>Arithmetic: ${statistics.arithmetic_count ?? 0}</span>
                <span>Assignments: ${statistics.assignment_count ?? 0}</span>
                <span>Comparisons: ${statistics.comparison_count ?? 0}</span>
                <span>Branches: ${statistics.branch_count ?? 0}</span>
                <span>Jumps: ${statistics.jump_count ?? 0}</span>
                <span>Print: ${statistics.print_count ?? 0}</span>
            </div>

            <div class="tac-names">
                <strong>Temporaries:</strong>
                ${temporaries.length
                    ? temporaries.map(name => `<code>${escapeHTML(name)}</code>`).join(" ")
                    : "<span>None</span>"}
            </div>

            ${labels.length ? `
                <div class="tac-names">
                    <strong>Labels:</strong>
                    ${labels.map(name => `<code>${escapeHTML(name)}:</code>`).join(" ")}
                </div>
            ` : ""}

            <div class="tac-table-wrapper">

                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Operation</th>
                            <th>Result</th>
                            <th>Arg 1</th>
                            <th>Arg 2</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>

            </div>


            <div class="tac-container">

                <div class="tac-title">
                    Generated TAC
                </div>

                <pre class="tac-code">${escapeHTML(
                    result.text
                )}</pre>

            </div>

        </div>
    `;
}

function showTACUnavailable(error) {
    visualization.innerHTML = `
        <div class="panel">
            <h2>Three Address Code (TAC)</h2>
            <div class="semantic-status error">✕ TAC generation unavailable</div>
            <div class="semantic-error">
                <strong>Reason: Semantic analysis failed.</strong>
                <p>${escapeHTML(error.message || error)}</p>
            </div>
        </div>
    `;
}


/* =========================================================
   CFG GRAPH
   ========================================================= */

function cfgInstructionLines(instructions) {
    return (instructions || []).flatMap(function(instruction) {
        const text = String(instruction);
        const lines = [];
        for (let index = 0; index < text.length; index += 36) {
            lines.push(text.slice(index, index + 36));
        }
        return lines.length ? lines : [""];
    });
}


function cfgNodeHeight(block) {
    const lineCount = Math.max(1, cfgInstructionLines(block.instructions).length);
    return 130 + lineCount * 25;
}


function cfgGraphLayout(blocks, edges, nodeWidth) {
    const blockById = new Map(blocks.map(block => [String(block.id), block]));
    const entry = blocks.find(block => !(block.predecessors || []).length) || blocks[0];
    const ranks = new Map([[String(entry.id), 0]]);
    const queue = [entry];

    while (queue.length) {
        const block = queue.shift();
        const nextRank = ranks.get(String(block.id)) + 1;
        edges.filter(edge => String(edge.source) === String(block.id)).forEach(function(edge) {
            const targetId = String(edge.target);
            if (blockById.has(targetId) && !ranks.has(targetId)) {
                ranks.set(targetId, nextRank);
                queue.push(blockById.get(targetId));
            }
        });
    }

    let nextRank = Math.max(...ranks.values()) + 1;
    blocks.forEach(function(block) {
        if (!ranks.has(String(block.id))) {
            ranks.set(String(block.id), nextRank++);
        }
    });

    const layers = new Map();
    blocks.forEach(function(block) {
        const rank = ranks.get(String(block.id));
        if (!layers.has(rank)) layers.set(rank, []);
        layers.get(rank).push(block);
    });

    const maxLayerSize = Math.max(...[...layers.values()].map(layer => layer.length));
    const columnGap = 90;
    const rowGap = 105;
    const margin = 35;
    const width = Math.max(420, margin * 2 + maxLayerSize * nodeWidth + (maxLayerSize - 1) * columnGap) + 85;
    const positions = new Map();
    let y = margin;

    [...layers.keys()].sort((left, right) => left - right).forEach(function(rank) {
        const layer = layers.get(rank);
        const startX = margin;
        let layerHeight = 0;

        layer.forEach(function(block, index) {
            const height = cfgNodeHeight(block);
            positions.set(String(block.id), {
                x: startX + index * (nodeWidth + columnGap),
                y,
                width: nodeWidth,
                height,
            });
            layerHeight = Math.max(layerHeight, height);
        });
        y += layerHeight + rowGap;
    });

    return {positions, width, height: y + margin};
}


function showCFG(result) {
    const blocks = result.blocks || [];
    if (!blocks.length) {
        visualization.innerHTML = `
            <div class="panel">
                <h2>Control Flow Graph (CFG)</h2>
                <div class="semantic-status error">✕ No basic blocks generated</div>
            </div>
        `;
        return;
    }

    const edges = result.edges || blocks.flatMap(
        block => (block.successors || []).map(target => ({source: block.id, target, type: "flow"}))
    );
    const nodeWidth = 340;
    const layout = cfgGraphLayout(blocks, edges, nodeWidth);
    let edgeMarkup = "";

    edges.forEach(function(edge) {
        const source = layout.positions.get(String(edge.source));
        const target = layout.positions.get(String(edge.target));
        if (!source || !target) return;

        const isLoop = target.y <= source.y;
        const startX = isLoop ? source.x + source.width : source.x + source.width / 2;
        const startY = isLoop ? source.y + source.height / 2 : source.y + source.height;
        const endX = isLoop ? target.x + target.width : target.x + target.width / 2;
        const endY = isLoop ? target.y + target.height / 2 : target.y;
        const path = isLoop
            ? `M ${startX} ${startY} C ${layout.width - 24} ${startY}, ${layout.width - 24} ${endY}, ${endX} ${endY}`
            : `M ${startX} ${startY} C ${startX} ${startY + 55}, ${endX} ${endY - 55}, ${endX} ${endY}`;

        edgeMarkup += `
            <path class="cfg-edge${isLoop ? " cfg-loop-edge" : ""}" d="${path}" marker-end="url(#cfg-arrow)" />
        `;
        if (["true", "false", "true/false"].includes(edge.type)) {
            edgeMarkup += `
                <text class="cfg-edge-label" x="${(startX + endX) / 2}" y="${(startY + endY) / 2 - 5}" text-anchor="middle">${escapeHTML(edge.type)}</text>
            `;
        }
    });

    const nodes = blocks.map(function(block) {
        const position = layout.positions.get(String(block.id));
        const instructionLines = cfgInstructionLines(block.instructions);
        const instructionRows = instructionLines.map(function(line, index) {
            return `<text x="${position.x + 15}" y="${position.y + 78 + index * 25}" class="cfg-instruction-text">${escapeHTML(line)}</text>`;
        }).join("");
        const instructionCount = Math.max(1, instructionLines.length);
        const predecessors = (block.predecessors || []).map(id => `B${id}`).join(", ") || "None";
        const successors = (block.successors || []).map(id => `B${id}`).join(", ") || "None";
        const detailY = position.y + 78 + instructionCount * 25;

        return `
            <g>
                <rect x="${position.x}" y="${position.y}" width="${nodeWidth}" height="${position.height}" rx="10" class="cfg-node-box" />
                <rect x="${position.x}" y="${position.y}" width="${nodeWidth}" height="48" rx="10" class="cfg-node-header" />
                <rect x="${position.x}" y="${position.y + 38}" width="${nodeWidth}" height="10" class="cfg-node-header" />
                <text x="${position.x + nodeWidth / 2}" y="${position.y + 31}" text-anchor="middle" class="cfg-block-title">Block B${escapeHTML(block.id)}</text>
                ${instructionRows || `<text x="${position.x + 15}" y="${position.y + 78}" class="cfg-instruction-text">No instructions</text>`}
                <text x="${position.x + 15}" y="${detailY + 8}" class="cfg-detail-text">Predecessors: ${escapeHTML(predecessors)}</text>
                <text x="${position.x + 15}" y="${detailY + 29}" class="cfg-detail-text">Successors: ${escapeHTML(successors)}</text>
            </g>
        `;
    }).join("");

    const statistics = result.statistics || {};
    const statisticItems = [
        ["Basic blocks", statistics.block_count],
        ["Edges", statistics.edge_count],
        ["Entry blocks", statistics.entry_block_count],
        ["Exit blocks", statistics.exit_block_count],
        ["Conditional branches", statistics.conditional_branch_count],
        ["Labels", statistics.label_count],
        ["Maximum block size", statistics.maximum_block_size],
    ].filter(([, value]) => value !== undefined);

    visualization.innerHTML = `
        <div class="panel">
            <h2>Control Flow Graph (CFG)</h2>
            <p>Actual basic blocks and control-flow edges generated from this program's TAC.</p>
            <div class="semantic-status success">✓ Control Flow Graph generated successfully</div>
            <div class="cfg-statistics">
                <strong>CFG Statistics</strong>
                ${statisticItems.map(([label, value]) => `<span>${label}: ${escapeHTML(value)}</span>`).join("")}
            </div>
            <div class="cfg-graph-container">
                <svg class="cfg-graph-svg" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}" aria-label="Control flow graph">
                    <defs>
                        <marker id="cfg-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
                            <path d="M0,0 L10,5 L0,10 Z" class="cfg-arrow-head" />
                        </marker>
                    </defs>
                    ${edgeMarkup}
                    ${nodes}
                </svg>
            </div>
            <div class="cfg-legend">
                <span>→ Control-flow edge</span>
                <span>True/false labels are shown only for conditional branches.</span>
            </div>
        </div>
    `;
}

/* =========================================================
   OPTIMIZER
   ========================================================= */

function tacRowsHTML(instructions) {
    return instructions.map(function(instruction, index) {
        return `
            <tr>
                <td>${String(index).padStart(3, "0")}</td>
                <td><code>${escapeHTML(tacInstructionText(instruction))}</code></td>
            </tr>
        `;
    }).join("");
}


function showOptimizer(result) {
    const statistics = result.statistics || {};
    const transformations = result.transformations || [];
    const status = result.changed
        ? `✓ Optimized TAC differs in ${transformations.length} sequence segment(s).`
        : "✓ No optimization opportunities found — the TAC is unchanged";
    const statisticItems = [
        ["Original instructions", statistics.original_instruction_count],
        ["Optimized instructions", statistics.optimized_instruction_count],
        ["Instructions removed", statistics.instructions_removed],
        ["Transformation segments", statistics.transformation_count],
        ["Instruction reduction", statistics.optimization_percentage === undefined
            ? undefined
            : `${statistics.optimization_percentage}%`],
    ].filter(([, value]) => value !== undefined);
    const transformationMarkup = transformations.length
        ? transformations.map(function(transformation) {
            const before = (transformation.before || []).map(
                instruction => `<code>${escapeHTML(instruction)}</code>`
            ).join("<br>");
            const after = (transformation.after || []).map(
                instruction => `<code>${escapeHTML(instruction)}</code>`
            ).join("<br>");
            return `
                <div class="optimization-transformation">
                    <strong>${escapeHTML(transformation.kind)} TAC segment</strong>
                    ${before ? `<div><span>Before</span>${before}</div>` : ""}
                    ${after ? `<div><span>After</span>${after}</div>` : ""}
                </div>
            `;
        }).join("")
        : `<p class="optimization-no-transformations">No instruction changes were reported by the optimizer.</p>`;

    visualization.innerHTML = `
        <div class="panel">
            <h2>Optimization</h2>
            <p>Existing passes: constant folding, constant propagation, and arithmetic identity simplification.</p>
            <div class="semantic-status success">${status}</div>
            <div class="optimization-statistics">
                <strong>Optimization Statistics</strong>
                ${statisticItems.map(([label, value]) => `<span>${label}: ${escapeHTML(value)}</span>`).join("")}
            </div>
            <div class="optimization-flow" aria-label="TAC optimization flow">
                <span>Original TAC</span><b>→</b><span>Optimizer</span><b>→</b><span>Optimized TAC</span>
            </div>
            <div class="tac-compare">
                <div class="tac-table-wrapper">
                    <div class="tac-title">Original TAC</div>
                    <table><thead><tr><th>#</th><th>Instruction</th></tr></thead><tbody>${tacRowsHTML(result.original)}</tbody></table>
                </div>
                <div class="tac-table-wrapper">
                    <div class="tac-title">Optimized TAC</div>
                    <table><thead><tr><th>#</th><th>Instruction</th></tr></thead><tbody>${tacRowsHTML(result.optimized)}</tbody></table>
                </div>
            </div>
            <section class="optimization-transformations">
                <h3>Observed Transformations</h3>
                ${transformationMarkup}
            </section>
        </div>
    `;
}

/* =========================================================
   VM
   ========================================================= */

function showVM(result) {

    const program = result.instructions.map(function(instruction) {

        return `
            <tr>
                <td>${String(instruction.index).padStart(3, "0")}</td>
                <td><code>${escapeHTML(instruction.opcode)}</code></td>
                <td>${escapeHTML(instruction.operand1 === null ? "—" : JSON.stringify(instruction.operand1))}</td>
                <td>${escapeHTML(instruction.operand2 === null ? "—" : JSON.stringify(instruction.operand2))}</td>
                <td><code>${escapeHTML(instruction.text)}</code></td>
            </tr>
        `;
    }).join("");


    const trace = result.trace.map(function(entry) {
        const memorySnapshot = (entry.memory || []).map(
            cell => `${cell.name}: ${cell.value}`
        ).join(", ");

        return `
            <tr${entry.error ? ' class="vm-trace-error"' : ""}>
                <td>${entry.step}</td>
                <td>${String(entry.pc).padStart(3, "0")}</td>
                <td><code>${escapeHTML(entry.instruction)}</code></td>
                <td><code>[${escapeHTML((entry.stack_before || []).join(", "))}]</code></td>
                <td><code>[${escapeHTML((entry.stack || []).join(", "))}]</code></td>
                <td><code>{${escapeHTML(memorySnapshot)}}</code></td>
                <td><code>${escapeHTML(entry.output || "")}</code></td>
                <td>${entry.error ? escapeHTML(entry.error) : ""}</td>
            </tr>
        `;
    }).join("");


    const memory = result.memory.map(function(cell) {

        return `
            <tr>
                <td><code>${escapeHTML(cell.name)}</code></td>
                <td><code>${escapeHTML(cell.value)}</code></td>
            </tr>
        `;
    }).join("");


    const status = result.status === "execution_limit"
        ? `<div class="semantic-status error"><strong>EXECUTION LIMIT REACHED</strong><br>Execution stopped.<br>Reason: ${escapeHTML(result.runtime_error)}</div>`
        : result.status === "runtime_error" || result.runtime_error
            ? `<div class="semantic-status error"><strong>RUNTIME ERROR</strong><br>Execution failed.<br>Reason: ${escapeHTML(result.runtime_error)}</div>`
            : `<div class="semantic-status success"><strong>SUCCESS</strong><br>Execution completed successfully. ${result.steps} instruction(s) executed.</div>`;

    const truncated = result.trace_truncated
        ? `<p>Trace recording is capped; showing the first ${result.trace.length} entries for ${result.steps} completed VM steps.</p>`
        : "";
    const statistics = result.statistics || {};
    const statisticItems = [
        ["Target instructions", statistics.target_instruction_count],
        ["Labels", statistics.label_count],
        ["Loads", statistics.load_count],
        ["Stack pushes", statistics.push_count],
        ["Stores", statistics.store_count],
        ["Memory operations", statistics.memory_operation_count],
        ["Arithmetic", statistics.arithmetic_count],
        ["Comparisons", statistics.comparison_count],
        ["Jumps", statistics.jump_count],
        ["Conditional branches", statistics.conditional_branch_count],
        ["Prints", statistics.print_count],
        ["Halts", statistics.halt_count],
    ].filter(([, value]) => value !== undefined);
    const stack = result.stack || [];
    const stackMarkup = stack.length
        ? stack.slice().reverse().map(function(value, index) {
            return `<div class="vm-stack-cell">${index === 0 ? "<strong>TOP</strong> " : ""}<code>${escapeHTML(value)}</code></div>`;
        }).join("")
        : `<div class="vm-empty-state">Empty</div>`;
    const outputMarkup = result.output
        ? escapeHTML(result.output)
        : "(the program printed nothing)";


    visualization.innerHTML = `
        <div class="panel">

            <h2>Virtual Machine</h2>

            <p>
                The code generator turns the optimized TAC into
                stack-machine instructions, which the VM executes.
            </p>

            ${status}

            <section class="vm-statistics">
                <h3>Backend Statistics</h3>
                <div class="vm-statistics-items">
                    ${statisticItems.map(([label, value]) => `<span>${label}: ${escapeHTML(value)}</span>`).join("")}
                </div>
            </section>

            <div class="tac-compare">

                <div class="tac-table-wrapper">
                    <div class="tac-title">Target Code</div>
                    <table>
                        <thead>
                            <tr><th>PC</th><th>Opcode</th><th>Operand 1</th><th>Operand 2</th><th>Instruction</th></tr>
                        </thead>
                        <tbody>${program}</tbody>
                    </table>
                </div>

                <div class="tac-table-wrapper">
                    <div class="tac-title">Final Memory</div>
                    <table>
                        <thead>
                            <tr><th>Variable</th><th>Value</th></tr>
                        </thead>
                        <tbody>${memory}</tbody>
                    </table>
                </div>

            </div>

            <section class="vm-stack-panel">
                <h3>Final VM Stack</h3>
                ${stackMarkup}
                ${stack.length ? "<div class=\"vm-stack-bottom\">BOTTOM</div>" : ""}
            </section>

            <div class="tac-table-wrapper">
                <div class="tac-title">Execution Trace</div>
                ${truncated}
                <table>
                    <thead>
                        <tr><th>Step</th><th>PC</th><th>Instruction</th><th>Stack before</th><th>Stack after</th><th>Memory after</th><th>Output</th><th>Error</th></tr>
                    </thead>
                    <tbody>${trace}</tbody>
                </table>
            </div>

            <section class="vm-output-panel">
                <h3>Program Output</h3>
                <pre class="tac-code program-output">${outputMarkup}</pre>
            </section>

        </div>
    `;
}


/* =========================================================
   OUTPUT
   ========================================================= */

function showOutput(result) {

    const output = result.output;

    const status = result.status === "execution_limit"
        ? `<div class="semantic-status error"><strong>EXECUTION LIMIT REACHED</strong><br>Execution stopped.<br>Reason: ${escapeHTML(result.runtime_error)}</div>`
        : result.status === "runtime_error" || result.runtime_error
            ? `<div class="semantic-status error"><strong>RUNTIME ERROR</strong><br>Execution failed.<br>Reason: ${escapeHTML(result.runtime_error)}</div>`
            : `<div class="semantic-status success"><strong>SUCCESS</strong><br>Execution completed successfully.</div>`;

    visualization.innerHTML = `
        <div class="panel">

            <h2>Execution Result</h2>

            <p>
                Output printed by the program while running on the VM.
            </p>

            ${status}

            <h3>Program Output</h3>
            <pre class="tac-code program-output">${
                output
                    ? escapeHTML(output)
                    : "(the program printed nothing)"
            }</pre>

        </div>
    `;
}


function showExecutionUnavailable(error) {
    const message = error.message || String(error);
    const backendFailure = message.startsWith("Backend Generation Failed:");
    const title = backendFailure
        ? "Backend Generation Failed"
        : "Execution Unavailable";
    const reason = backendFailure
        ? message.slice("Backend Generation Failed:".length).trim()
        : message;

    visualization.innerHTML = `
        <div class="panel">
            <h2>${title}</h2>
            <div class="semantic-status error">✕ ${title}</div>
            <div class="semantic-error">
                <strong>Reason:</strong>
                <p>${escapeHTML(reason)}</p>
            </div>
        </div>
    `;
}


/* =========================================================
   PIPELINE BUTTONS
   ========================================================= */

const pipelineStages = {
    source: {
        nextStep: 0,
        show: async function() {
            showSource();
        },
    },
    lexer: {
        nextStep: 1,
        show: async function() {
            state.tokens = await getTokens();
            showLexer(state.tokens);
        },
    },
    parser: {
        nextStep: 2,
        show: async function() {
            const parseResult = await loadAST();
            showParser(parseResult);
        },
    },
    precedence: {
        nextStep: 3,
        show: async function() {
            if (!state.ast) {
                await loadAST();
            }
            showPrecedence(state.ast);
        },
    },
    ast: {
        nextStep: 4,
        show: async function() {
            if (!state.ast) {
                await loadAST();
            }
            showAST(state.ast, state.astStatistics);
        },
    },
    semantic: {
        nextStep: 5,
        show: async function() {
            showSemantic(await getSemantic());
        },
    },
    tac: {
        nextStep: 6,
        show: async function() {
            state.tac = await getTAC();
            showTAC(state.tac);
        },
    },
    cfg: {
        nextStep: 7,
        show: async function() {
            state.cfg = await getCFG();
            showCFG(state.cfg);
        },
    },
    optimizer: {
        nextStep: 8,
        show: async function() {
            showOptimizer(await getOptimized());
        },
    },
    vm: {
        nextStep: 9,
        show: async function() {
            state.run = await getRun();
            showVM(state.run);
        },
    },
    output: {
        nextStep: 10,
        show: async function() {
            state.run = await getRun();
            showOutput(state.run);
        },
    },
};

const nextStepStages = {
    0: "lexer",
    1: "parser",
    2: "precedence",
    3: "ast",
    4: "semantic",
    5: "tac",
    6: "cfg",
    7: "optimizer",
    8: "vm",
    9: "output",
    10: "output",
};

function setActiveStage(stageKey) {
    stageButtons.forEach(function(button) {
        const isActive = button.dataset.stage === stageKey;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-current", isActive ? "step" : "false");
    });
}

async function runStage(stageKey) {
    const stage = pipelineStages[stageKey];
    if (!stage) {
        return;
    }

    setActiveStage(stageKey);
    state.step = stage.nextStep;
    nextButton.disabled = false;
    nextButton.style.display = "inline-block";
    compileButton.disabled = true;

    const stageButton = document.querySelector(
        `.stage[data-stage="${stageKey}"]`
    );
    if (stageButton) {
        stageButton.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
            inline: "center",
        });
    }

    try {
        await stage.show();
    } catch (error) {
        nextButton.disabled = true;
        compileButton.disabled = false;

        if (error.details?.type === "Syntax Error") {
            showSyntaxError(error);
            return;
        }
        if (stageKey === "tac" && error.message.startsWith("Semantic Error:")) {
            showTACUnavailable(error);
            return;
        }
        if (stageKey === "vm" || stageKey === "output") {
            showExecutionUnavailable(error);
            return;
        }

        visualization.innerHTML = `
            <div class="panel">

                <h2>Compilation Error</h2>

                <div class="semantic-status error">
                    ✕ ${escapeHTML(error.message)}
                </div>

            </div>
        `;
    }
}


/* =========================================================
   MANUAL WALKTHROUGH
   ========================================================= */

nextButton.addEventListener(
    "click",
    async function() {

        try {
            setActiveStage(nextStepStages[state.step] || "output");

            if (state.step === 0) {

                state.tokens =
                    await getTokens();

                showLexer(state.tokens);

                state.step = 1;

                return;
            }


            if (state.step === 1) {

                const parseResult = await loadAST();

                showParser(parseResult);

                state.step = 2;

                return;
            }


            if (state.step === 2) {

                showPrecedence(
                    state.ast
                );

                state.step = 3;

                return;
            }


            if (state.step === 3) {

                showAST(
                    state.ast,
                    state.astStatistics
                );

                state.step = 4;

                return;
            }


            if (state.step === 4) {

                showSemantic(
                    await getSemantic()
                );

                state.step = 5;

                return;
            }


            if (state.step === 5) {

                state.tac =
                    await getTAC();

                showTAC(state.tac);

                state.step = 6;

                return;
            }


            if (state.step === 6) {

                state.cfg =
                    await getCFG();

                showCFG(state.cfg);

                state.step = 7;

                return;
            }


            if (state.step === 7) {

                showOptimizer(
                    await getOptimized()
                );

                state.step = 8;

                return;
            }


            if (state.step === 8) {

                state.run =
                    await getRun();

                showVM(state.run);

                state.step = 9;

                return;
            }


            if (state.step === 9) {

                showOutput(state.run);

                state.step = 10;

                return;
            }


            if (state.step === 10) {

                nextButton.style.display =
                    "none";

                compileButton.disabled =
                    false;

                visualization.innerHTML += `
                    <div class="semantic-status success">
                        ✓ All compiler stages completed
                    </div>
                `;

                return;
            }

        } catch (error) {

            if (error.details?.type === "Syntax Error") {
                showSyntaxError(error);
                nextButton.style.display = "none";
                compileButton.disabled = false;
                return;
            }
            if (state.step === 5 && error.message.startsWith("Semantic Error:")) {
                showTACUnavailable(error);
                nextButton.style.display = "none";
                compileButton.disabled = false;
                return;
            }
            if (state.step === 8 || state.step === 9) {
                showExecutionUnavailable(error);
                nextButton.style.display = "none";
                compileButton.disabled = false;
                return;
            }

            visualization.innerHTML = `
                <div class="panel">

                    <h2>Compilation Error</h2>

                    <div class="semantic-status error">
                        ✕ ${escapeHTML(error.message)}
                    </div>

                </div>
            `;

            nextButton.style.display =
                "none";

            compileButton.disabled =
                false;
        }
    }
);


/* =========================================================
   COMPILE
   ========================================================= */

compileButton.addEventListener(
    "click",
    function() {

        state = {
            step: 0,
            tokens: null,
            ast: null,
            astStatistics: null,
            tac: null,
            cfg: null,
            run: null
        };

        compileButton.disabled = true;
        nextButton.disabled = false;

        nextButton.textContent =
            "Next Step →";

        nextButton.style.display =
            "inline-block";
        nextButton.disabled = false;

        setActiveStage("source");
        showSource();
    }
);


/* =========================================================
   PIPELINE
   ========================================================= */

document
    .querySelectorAll(".stage[data-stage]")
    .forEach(function(stageButton) {

        stageButton.addEventListener(
            "click",
            async function() {

                await runStage(stageButton.dataset.stage);

            }
        );

    });


sourceBox.addEventListener("input", function() {
    state = {
        step: 0,
        tokens: null,
        ast: null,
        astStatistics: null,
        tac: null,
        cfg: null,
        run: null,
    };
    compileButton.disabled = false;
    nextButton.disabled = false;
    nextButton.style.display = "none";
    setActiveStage("source");
    showSource();
});


setActiveStage("source");
showSource();
