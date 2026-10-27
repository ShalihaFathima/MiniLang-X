const sourceBox = document.getElementById("source-code");
const compileButton = document.getElementById("compile-button");
const runButton = document.getElementById("run-button");
const resetButton = document.getElementById("reset-button");
const visualization = document.getElementById("visualization");
const previousButton = document.getElementById("previous-step-button");
const runAllButton = document.getElementById("run-all-button");
const lineNumbers = document.getElementById("line-numbers");
const compilerStatus = document.getElementById("compiler-status");
const stepIndicator = document.getElementById("step-indicator");
const activeStageLabel = document.getElementById("active-stage-label");
const analysisHeading = document.getElementById("analysis-heading");
const phaseMetaDesc = document.getElementById("phase-meta-desc");
const editorCompileBtn = document.getElementById("editor-compile-btn");

let nextButton = document.getElementById("next-step-button");
const stageButtons = document.querySelectorAll(".stage[data-stage]");
const stageOrder = [
    "source", "lexer", "parser", "precedence", "ast", "semantic",
    "tac", "cfg", "optimizer", "backend", "vm", "output",
];
let navigationRequest = 0;

let state = {
    step: 0,
    currentStage: "source",
    completedStages: {},
    diagnostic: null,
    navigationBlocked: false,
    tokens: null,
    ast: null,
    astStatistics: null,
    semantic: null,
    tac: null,
    cfg: null,
    optimized: null,
    run: null,
};

const stageLabels = {
    source: "Source Program",
    lexer: "Lexical Analysis",
    parser: "Syntax Analysis (Parser)",
    precedence: "Operator Precedence",
    ast: "Abstract Syntax Tree (AST)",
    semantic: "Semantic Analysis",
    tac: "Three-Address Code (TAC)",
    cfg: "Control Flow Graph (CFG)",
    optimizer: "Intermediate Code Optimization",
    backend: "Target Code Generation",
    vm: "Virtual Machine Execution",
    output: "Program Output",
};

const phaseTransformations = {
    source: {
        category: "FRONT-END",
        input: "MiniLang-X Source Text",
        mechanism: "Source Buffer & Line Indexer",
        output: "Raw Character Stream",
        desc: "MiniLang-X source program enters the compiler pipeline to undergo lexical, syntactic, semantic, and intermediate transformations."
    },
    lexer: {
        category: "FRONT-END",
        input: "Character Stream",
        mechanism: "Regular Expression Scanning & Tokenizer",
        output: "Ordered Token Stream (Type, Value, Line:Col)",
        desc: "Lexical analysis strips comments, ignores whitespace, and categorizes character sequences into language tokens (keywords, identifiers, literals, operators)."
    },
    parser: {
        category: "FRONT-END",
        input: "Token Stream",
        mechanism: "Recursive Descent LL(1) Grammar Parsing",
        output: "Concrete Grammar Parse Structure",
        desc: "Syntax analysis validates token sequences against the MiniLang-X context-free grammar and builds syntax hierarchies."
    },
    precedence: {
        category: "FRONT-END",
        input: "Infix Expression Tokens",
        mechanism: "Precedence Climbing & Associativity Resolution",
        output: "Binary Expression Tree",
        desc: "Demonstrates how operator precedence (* and / over + and -) and left-associativity govern operand grouping."
    },
    ast: {
        category: "FRONT-END",
        input: "Concrete Parse Structure",
        mechanism: "Syntax Tree Normalization & Pruning",
        output: "Hierarchical Abstract Syntax Tree",
        desc: "Constructs a clean hierarchical tree capturing program semantics without concrete syntax noise like semicolons and punctuation."
    },
    semantic: {
        category: "FRONT-END",
        input: "Abstract Syntax Tree",
        mechanism: "Symbol Table Construction & Type Checking",
        output: "Type-Checked & Scope-Annotated AST",
        desc: "Verifies type compatibility in expressions, checks variable declaration before use, and manages lexical scopes."
    },
    tac: {
        category: "MIDDLE-END",
        input: "Type-Checked AST",
        mechanism: "Intermediate Linearization & Temp Allocation",
        output: "Three-Address Code (TAC) Quadruple Stream",
        desc: "Flattens tree structures into elementary instructions with at most two operands and one result variable, introducing temporaries (t1, t2...) and jump labels."
    },
    cfg: {
        category: "MIDDLE-END",
        input: "Linear Three-Address Code",
        mechanism: "Leader Identification & Basic Block Partitioning",
        output: "Directed Control Flow Graph (Blocks & Edges)",
        desc: "Partitions TAC instructions into single-entry, single-exit basic blocks and adds directed control edges for branches and loops."
    },
    optimizer: {
        category: "MIDDLE-END",
        input: "Initial TAC & CFG",
        mechanism: "Constant Folding, Propagation & Algebraic Simplification",
        output: "Optimized Three-Address Code",
        desc: "Executes compile-time evaluations of constant expressions, propagates known constants, and eliminates redundant operations."
    },
    backend: {
        category: "BACK-END",
        input: "Optimized TAC",
        mechanism: "Target Instruction Selection for Stack VM",
        output: "Stack Machine Bytecode Instructions",
        desc: "Translates register/temporary-based 3-address instructions into the target stack machine instruction set (PUSH, STORE, LOAD, ADD, etc.)."
    },
    vm: {
        category: "BACK-END",
        input: "Target Bytecode Instructions",
        mechanism: "Fetch-Decode-Execute Cycle on Stack VM",
        output: "Execution Trace, Operand Stack & Memory State",
        desc: "Simulates actual target machine execution, tracking program counter, operand stack transitions, memory state, and runtime output."
    },
    output: {
        category: "BACK-END",
        input: "VM Runtime State",
        mechanism: "Standard Output Capture & Exit Code Evaluation",
        output: "Final Program Console Output",
        desc: "Presents the final stdout results produced by the compiled program along with execution metrics."
    }
};

function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getTransformationBanner(stageKey) {
    const meta = phaseTransformations[stageKey];
    if (!meta) return "";
    return `
        <div class="phase-transformation-card" aria-label="Compiler transformation summary">
            <div class="transform-category">${meta.category} TRANSFORMATION</div>
            <div class="transform-pipeline-flow">
                <div class="transform-box">
                    <span class="transform-box-label">INPUT</span>
                    <span class="transform-box-text">${escapeHTML(meta.input)}</span>
                </div>
                <div class="transform-arrow" aria-hidden="true">→</div>
                <div class="transform-box mechanism">
                    <span class="transform-box-label">MECHANISM</span>
                    <span class="transform-box-text">${escapeHTML(meta.mechanism)}</span>
                </div>
                <div class="transform-arrow" aria-hidden="true">→</div>
                <div class="transform-box">
                    <span class="transform-box-label">OUTPUT</span>
                    <span class="transform-box-text">${escapeHTML(meta.output)}</span>
                </div>
            </div>
            <p class="transform-desc">${escapeHTML(meta.desc)}</p>
        </div>
    `;
}

function updateLineNumbers() {
    const lines = sourceBox.value.split("\n").length;
    lineNumbers.textContent = Array.from(
        {length: lines},
        (_, index) => index + 1
    ).join("\n");
}

function setCompilerStatus(status, text) {
    compilerStatus.classList.remove("is-running", "is-success", "is-error");
    if (status) {
        compilerStatus.classList.add(`is-${status}`);
    }
    const symbols = {running: "●", success: "✓", error: "✕"};
    compilerStatus.innerHTML = `<span class="status-dot" aria-hidden="true"></span>${symbols[status] ? `<span aria-hidden="true">${symbols[status]}</span>` : ""} ${escapeHTML(text)}`;
}

function renderNavigationState() {
    stepIndicator.textContent = `Step ${Math.min(state.step, 11)} / 11`;
    previousButton.disabled = state.currentStage === "source";
    nextButton.textContent = state.step >= 11 ? "Finish" : "Next Step →";
    nextButton.disabled = state.navigationBlocked
        || (state.currentStage === "source" && !state.completedStages.lexer);
    nextButton.style.display = "inline-block";
    activeStageLabel.textContent = state.currentStage.toUpperCase();
    analysisHeading.textContent = stageLabels[state.currentStage] || "Compiler Output";

    if (phaseMetaDesc && phaseTransformations[state.currentStage]) {
        phaseMetaDesc.textContent = phaseTransformations[state.currentStage].desc;
    }

    stageButtons.forEach(function(button) {
        const stageKey = button.dataset.stage;
        button.dataset.stageStatus = state.errorStage === stageKey
            ? "error"
            : state.currentStage === stageKey
                ? "current"
                : state.completedStages[stageKey]
                    ? "complete"
                    : "pending";
        button.setAttribute(
            "aria-label",
            `${stageLabels[stageKey] || stageKey}${state.errorStage === stageKey ? ", failed" : stageKey === state.currentStage ? ", current stage" : state.completedStages[stageKey] ? ", completed" : ", pending"}`
        );
    });
}

async function api(endpoint) {
    const requestId = navigationRequest;
    const requestedSource = sourceBox.value;
    let response;
    let data;

    try {
        response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                source: requestedSource
            })
        });
    } catch (error) {
        if (requestId !== navigationRequest) {
            throw error;
        }
        throw new Error("Could not reach the compiler API. Check that the visualizer server is running.");
    }

    try {
        data = await response.json();
    } catch (error) {
        throw new Error("The compiler API returned an invalid response.");
    }

    if (requestId !== navigationRequest || requestedSource !== sourceBox.value) {
        const error = new Error("A newer source edit or stage selection replaced this result.");
        error.name = "StaleStageResponse";
        throw error;
    }

    if (!data || typeof data !== "object" || Array.isArray(data)) {
        throw new Error("The compiler API returned an invalid response.");
    }

    if (!response.ok || data.success === false) {
        const error = new Error(data.error || "Compiler stage failed");
        error.details = data.details || null;
        throw error;
    }

    return data;
}

/* =========================================================
   API CALLS
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

function normalizeAST(data) {
    if (data && data.ast) {
        return data.ast;
    }
    return data;
}

async function loadAST() {
    const result = await getAST();
    state.ast = normalizeAST(result);
    state.astStatistics = result.statistics || {};
    return result;
}

/* =========================================================
   STAGE 01: SOURCE
   ========================================================= */

function showSource() {
    const lines = sourceBox.value.split("\n").length;
    const chars = sourceBox.value.length;

    visualization.innerHTML = `
        ${getTransformationBanner("source")}
        <div class="semantic-status success">
            ✓ Source Program Loaded (${lines} lines, ${chars} characters)
        </div>
        <p>
            The MiniLang-X program is loaded and ready for compilation. The source code enters the pipeline and is transformed through twelve discrete compiler phases.
        </p>
        <pre class="source-preview">${escapeHTML(sourceBox.value)}</pre>
        <p>
            Click <strong>Compile</strong> (or press <kbd>Ctrl+Enter</kbd>) to begin Lexical Analysis, or select any phase from the pipeline above.
        </p>
    `;
}

/* =========================================================
   STAGE 02: LEXER
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
        const type = token.type?.name || token.type || "";
        const value = token.value ?? token.lexeme ?? "";
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
        ${getTransformationBanner("lexer")}
        <div class="semantic-status success">
            ✓ Lexical analysis completed successfully — ${statistics.total_tokens ?? tokens.length} tokens recognized
        </div>

        <div class="lexer-statistics">
            <strong>Token Statistics</strong>
            <span>Total: ${statistics.total_tokens ?? 0}</span>
            <span>Identifiers: ${statistics.identifiers ?? 0}</span>
            <span>Keywords: ${statistics.keywords ?? 0}</span>
            <span>Literals: ${statistics.literals ?? 0}</span>
            <span>Operators: ${statistics.operators ?? 0}</span>
            <span>Separators: ${statistics.separators ?? 0}</span>
            <span>Comments: ${statistics.comments ?? 0}</span>
        </div>

        <div class="token-filters" aria-label="Filter tokens">
            <button type="button" class="token-filter active" data-filter="all">All Tokens</button>
            <button type="button" class="token-filter" data-filter="keywords">Keywords</button>
            <button type="button" class="token-filter" data-filter="identifiers">Identifiers</button>
            <button type="button" class="token-filter" data-filter="literals">Literals</button>
            <button type="button" class="token-filter" data-filter="operators">Operators</button>
        </div>

        <div class="token-table-scroll">
            <table class="token-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Token Type</th>
                        <th>Lexeme / Value</th>
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
                row.hidden = filter !== "all" && row.dataset.tokenCategory !== filter;
            });
        });
    });
}

/* =========================================================
   STAGE 03: PARSER
   ========================================================= */

function showParser(parseResult) {
    const statistics = parseResult.statistics || {};

    visualization.innerHTML = `
        ${getTransformationBanner("parser")}
        <div class="semantic-status success parser-status">
            ✓ Lexer completed &nbsp;·&nbsp; ✓ Grammar verified &nbsp;·&nbsp; ✓ Parse tree constructed
        </div>

        <div class="parser-flow" aria-label="Parsing derivation flow">
            <div class="parser-item">
                Token Stream
                <small>${statistics.token_count ?? 0} source tokens</small>
            </div>
            <div class="parser-arrow">→</div>
            <div class="parser-item">
                Grammar Rules
                <small>Recursive Descent</small>
            </div>
            <div class="parser-arrow">→</div>
            <div class="parser-item">
                Abstract Syntax Tree
                <small>${statistics.total_nodes ?? 0} AST nodes</small>
            </div>
        </div>

        <div class="ast-statistics">
            <strong>AST Structure Statistics</strong>
            <span>Total Nodes: ${statistics.total_nodes ?? 0}</span>
            <span>Maximum Depth: ${statistics.max_depth ?? 0}</span>
            <span>Statements: ${statistics.statement_count ?? 0}</span>
            <span>Expressions: ${statistics.expression_count ?? 0}</span>
            <span>Identifiers: ${statistics.identifier_count ?? 0}</span>
            <span>Literals: ${statistics.literal_count ?? 0}</span>
            <span>Operators: ${statistics.operator_count ?? 0}</span>
        </div>

        <p>
            Continue to <strong>Operator Precedence</strong> to inspect expression grouping, or proceed directly to <strong>AST</strong> to examine the complete node-and-edge syntax tree.
        </p>
    `;
}

/* =========================================================
   STAGE 04: PRECEDENCE
   ========================================================= */

function findExpression(node) {
    if (!node) return null;
    if (node.type === "BinaryExpression" || node.type === "UnaryExpression") {
        return node;
    }
    const children = node.children || [];
    for (const child of children) {
        const expression = findExpression(child);
        if (expression) return expression;
    }
    return null;
}

function precedenceNodeLabel(node) {
    if (!node) return "";
    if (node.type === "BinaryExpression" || node.type === "UnaryExpression") {
        return node.operator;
    }
    if (node.type === "Literal") {
        return String(node.value);
    }
    if (node.type === "Identifier") {
        return node.name;
    }
    return node.label || node.name || node.value || node.type;
}

function precedenceNodeClass(node) {
    if (node.type === "BinaryExpression" || node.type === "UnaryExpression") {
        return "precedence-svg-operator";
    }
    return "precedence-svg-leaf";
}

function drawPrecedenceTree(root) {
    const width = 760;
    const nodeWidth = 105;
    const nodeHeight = 58;
    const verticalGap = 120;

    const leaves = [];
    let maxDepth = 0;

    function collectLeaves(node, depth = 0) {
        maxDepth = Math.max(maxDepth, depth);
        const children = node.children || [];
        if (!children.length) {
            leaves.push(node);
            return;
        }
        children.forEach(child => collectLeaves(child, depth + 1));
    }

    collectLeaves(root);

    const height = 110 + maxDepth * verticalGap;
    const leafSpacing = width / (leaves.length + 1);
    const positions = new Map();

    function place(node, depth = 0) {
        const children = node.children || [];
        let x;
        if (!children.length) {
            x = leafSpacing * (leaves.indexOf(node) + 1);
        } else {
            children.forEach(child => place(child, depth + 1));
            const childX = children.map(child => positions.get(child).x);
            x = (Math.min(...childX) + Math.max(...childX)) / 2;
        }
        positions.set(node, { x, y: 55 + depth * verticalGap });
    }

    place(root);

    let edges = "";
    let nodes = "";

    function renderEdges(node) {
        const parent = positions.get(node);
        const children = node.children || [];

        children.forEach(function(child) {
            const childPosition = positions.get(child);
            if (!childPosition) return;

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

    positions.forEach(function(position, node) {
        const label = precedenceNodeLabel(node);
        const className = precedenceNodeClass(node);

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
                    y="${position.y + 6}"
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
                    <path d="M0,0 L8,4 L0,8 Z" class="precedence-arrow-head" />
                </marker>
            </defs>
            ${edges}
            ${nodes}
        </svg>
    `;
}

function buildExpressionText(node) {
    if (!node) return "";
    if (node.type === "Literal") return String(node.value);
    if (node.type === "Identifier") return node.name;
    if (node.type === "UnaryExpression") {
        return node.operator + buildExpressionText(node.operand || node.children?.[0]);
    }
    if (node.type === "BinaryExpression") {
        const children = node.children || [];
        if (children.length >= 2) {
            return "(" + buildExpressionText(children[0]) + " " + node.operator + " " + buildExpressionText(children[1]) + ")";
        }
    }
    return node.label || "";
}

function showPrecedence(ast) {
    const expression = findExpression(ast);

    if (!expression) {
        visualization.innerHTML = `
            ${getTransformationBanner("precedence")}
            <div class="semantic-status error">✕ No arithmetic or boolean expressions found in program</div>
        `;
        return;
    }

    const expressionLabel = buildExpressionText(expression);

    visualization.innerHTML = `
        ${getTransformationBanner("precedence")}
        <div class="semantic-status success">
            ✓ Operator precedence parsed successfully
        </div>

        <div class="precedence-expression">
            <strong>Grouped Expression:</strong> <code>${escapeHTML(expressionLabel)}</code>
        </div>

        <div class="precedence-visual">
            ${drawPrecedenceTree(expression)}
        </div>

        <div class="precedence-result">
            <strong>Parser Derivation:</strong>
            <code>${escapeHTML(expressionLabel)}</code>
        </div>
    `;
}

/* =========================================================
   STAGE 05: AST
   ========================================================= */

function astTreeHTML(node) {
    if (!node) return "";

    const children = node.children || [];
    const label = astNodeLabel(node);
    const detail = node.type || "";

    const details = [
        ["type", node.type],
        ["operator", node.operator],
        ["name", node.name],
        ["data_type", node.data_type],
        ["value", node.value],
    ].filter(([, value]) => value !== undefined && value !== null)
        .map(([key, value]) => `data-${key.replace("_", "-")}="${escapeHTML(value)}"`)
        .join(" ");

    let html = `
        <div class="ast-node">
            <button type="button" class="ast-box ${escapeHTML(node.type || "")}" title="${escapeHTML(detail)}" ${details}>
                <span>${escapeHTML(label)}</span>
                ${detail ? `<small>${escapeHTML(detail)}</small>` : ""}
            </button>
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
                return `${node.name} : ${node.data_type}`;
            case "Assignment":
                return `Assign: ${node.name}`;
            case "PrintStatement":
                return "print(...)";
            case "IfStatement":
                return "if";
            case "WhileStatement":
                return "while";
            case "BinaryExpression":
                return `Binary (${node.operator})`;
            case "UnaryExpression":
                return `Unary (${node.operator})`;
            case "Literal":
                return `${node.value} (${node.data_type})`;
            case "Identifier":
                return node.name;
            default:
                return node.label || node.type || "";
        }
    }

    html += `</div>`;
    return html;
}

function showAST(ast, statistics = {}) {
    visualization.innerHTML = `
        ${getTransformationBanner("ast")}
        <div class="semantic-status success">
            ✓ Hierarchical Abstract Syntax Tree generated
        </div>

        <div class="ast-statistics">
            <strong>AST Statistics</strong>
            <span>Total Nodes: ${statistics.total_nodes ?? 0}</span>
            <span>Maximum Depth: ${statistics.max_depth ?? 0}</span>
            <span>Statements: ${statistics.statement_count ?? 0}</span>
            <span>Expressions: ${statistics.expression_count ?? 0}</span>
            <span>Identifiers: ${statistics.identifier_count ?? 0}</span>
            <span>Literals: ${statistics.literal_count ?? 0}</span>
            <span>Operators: ${statistics.operator_count ?? 0}</span>
        </div>

        <div class="ast-container" role="tree" aria-label="Abstract syntax tree">
            ${astTreeHTML(ast)}
        </div>

        <section id="ast-node-details" class="ast-node-details" aria-live="polite">
            <strong>Node Inspector</strong>
            <p>Click any node in the diagram above to inspect its AST fields and attributes.</p>
        </section>
    `;

    visualization.querySelectorAll(".ast-box").forEach(function(nodeButton) {
        nodeButton.addEventListener("click", function() {
            const fields = [
                ["Node Type", nodeButton.dataset.type],
                ["Operator", nodeButton.dataset.operator],
                ["Identifier Name", nodeButton.dataset.name],
                ["Data Type", nodeButton.dataset.dataType],
                ["Literal Value", nodeButton.dataset.value],
            ].filter(([, value]) => value !== undefined && value !== "");

            const details = document.getElementById("ast-node-details");
            details.innerHTML = `
                <strong>Node Inspector: ${escapeHTML(nodeButton.dataset.type || "AST Node")}</strong>
                <dl>${fields.map(([label, value]) => `<dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value)}</dd>`).join("")}</dl>
            `;
        });
    });
}

/* =========================================================
   STAGE 06: SEMANTIC
   ========================================================= */

function showSemantic(result) {
    const statistics = result.statistics || {};
    const symbols = result.symbols || [];
    const errors = result.errors || [];

    let rows = "";

    symbols.forEach(function(symbol) {
        const location = symbol.line && symbol.column
            ? `Line ${symbol.line}, Col ${symbol.column}`
            : "—";

        rows += `
            <tr>
                <td><strong>${escapeHTML(symbol.name)}</strong></td>
                <td><code>${escapeHTML(symbol.data_type)}</code></td>
                <td>${escapeHTML(symbol.scope || `scope ${symbol.scope_level}`)}</td>
                <td>${symbol.initialized ? "✓ Yes" : "No"}</td>
                <td>${location}</td>
            </tr>
        `;
    });

    const errorDetails = result.error_details || errors[0] || {};
    const errorPanel = result.valid
        ? `
            <div class="semantic-status success">
                ✓ Semantic analysis completed successfully — Symbol table verified
            </div>
            <p class="semantic-message">✓ Variable declarations verified · ✓ Type consistency checked · ✓ Scope rules satisfied</p>
        `
        : `
            <div class="semantic-status error">✕ Semantic Verification Failed</div>
            <div class="semantic-error">
                <strong>${escapeHTML(errorDetails.type || "Semantic Error")}</strong>
                <p>${escapeHTML(errorDetails.message || result.error || "Semantic analysis failed.")}</p>
                ${errorDetails.line != null
                    ? `<p>Location: Line ${escapeHTML(errorDetails.line)}${errorDetails.column != null ? `, Column ${escapeHTML(errorDetails.column)}` : ""}</p>`
                    : ""}
                ${errorDetails.source_context
                    ? `<pre class="semantic-source">${escapeHTML(errorDetails.source_context)}</pre>`
                    : ""}
            </div>
        `;

    visualization.innerHTML = `
        ${getTransformationBanner("semantic")}
        <div class="semantic-flow" aria-label="Semantic analysis sequence">
            <span>AST</span><b>→</b>
            <span>Symbol Table Resolution</span><b>→</b>
            <span>Static Type Verification</span><b>→</b>
            <span>Scope Analysis</span>
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
        <div class="token-table-scroll">
            <table class="token-table">
                <thead>
                    <tr>
                        <th>Identifier</th>
                        <th>Declared Type</th>
                        <th>Scope Level</th>
                        <th>Initialized</th>
                        <th>Source Location</th>
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
   STAGE 07: TAC
   ========================================================= */

function tacInstructionText(instruction) {
    const op = instruction.op;
    const arg1 = instruction.arg1;
    const arg2 = instruction.arg2;
    const result = instruction.result;

    if (op === "LABEL") return result + ":";
    if (op === "GOTO") return "goto " + result;
    if (op === "IF_FALSE") return "ifFalse " + arg1 + " goto " + result;
    if (op === "IF_TRUE") return "ifTrue " + arg1 + " goto " + result;
    if (op === "PRINT") return "print " + arg1;
    if (op === "ASSIGN" || op === "UNARY") return result + " = " + arg1;
    if (arg2 !== null) return result + " = " + arg1 + " " + op + " " + arg2;

    return [op, arg1, arg2, result].filter(part => part !== null).join(" ");
}

function showTAC(result) {
    let rows = "";

    result.instructions.forEach(function(instruction, index) {
        rows += `
            <tr>
                <td>${index}</td>
                <td><code>${escapeHTML(instruction.op)}</code></td>
                <td><code>${escapeHTML(instruction.result ?? "—")}</code></td>
                <td><code>${escapeHTML(instruction.arg1 ?? "—")}</code></td>
                <td><code>${escapeHTML(instruction.arg2 ?? "—")}</code></td>
            </tr>
        `;
    });

    const statistics = result.statistics || {};
    const temporaries = result.temporaries || [];
    const labels = result.labels || [];

    visualization.innerHTML = `
        ${getTransformationBanner("tac")}
        <div class="semantic-status success">
            ✓ Three-Address Code generated — ${result.instructions.length} quadruples emitted
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
            <span>Prints: ${statistics.print_count ?? 0}</span>
        </div>

        <div class="tac-names">
            <strong>Temporaries:</strong>
            ${temporaries.length
                ? temporaries.map(name => `<code>${escapeHTML(name)}</code>`).join(" ")
                : "<span>None</span>"}
        </div>

        ${labels.length ? `
            <div class="tac-names">
                <strong>Jump Labels:</strong>
                ${labels.map(name => `<code>${escapeHTML(name)}:</code>`).join(" ")}
            </div>
        ` : ""}

        <div class="tac-table-wrapper">
            <div class="tac-title">Structured Quadruple Instructions</div>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Opcode</th>
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

        <div class="tac-table-wrapper">
            <div class="tac-title">Linear Three-Address Code Listing</div>
            <pre class="tac-code">${escapeHTML(result.text)}</pre>
        </div>
    `;
}

function showTACUnavailable(error) {
    visualization.innerHTML = `
        ${getTransformationBanner("tac")}
        <div class="semantic-status error">✕ TAC Generation Blocked</div>
        <div class="semantic-error">
            <strong>Reason: Semantic analysis must succeed before Intermediate Code can be generated.</strong>
            <p>${escapeHTML(error.message || error)}</p>
        </div>
    `;
}

/* =========================================================
   STAGE 08: CFG
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
            ${getTransformationBanner("cfg")}
            <div class="semantic-status error">✕ No basic blocks generated</div>
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
        const boundaryLabels = [
            ...((block.predecessors || []).length ? [] : ["ENTRY"]),
            ...((block.successors || []).length ? [] : ["EXIT"]),
        ].join(" · ");
        const detailY = position.y + 78 + instructionCount * 25;

        return `
            <g>
                <rect x="${position.x}" y="${position.y}" width="${nodeWidth}" height="${position.height}" rx="10" class="cfg-node-box" />
                <rect x="${position.x}" y="${position.y}" width="${nodeWidth}" height="48" rx="10" class="cfg-node-header" />
                <rect x="${position.x}" y="${position.y + 38}" width="${nodeWidth}" height="10" class="cfg-node-header" />
                <text x="${position.x + nodeWidth / 2}" y="${position.y + 31}" text-anchor="middle" class="cfg-block-title">Block B${escapeHTML(block.id)}</text>
                ${boundaryLabels ? `<text x="${position.x + nodeWidth - 12}" y="${position.y + 18}" text-anchor="end" class="cfg-detail-text">${boundaryLabels}</text>` : ""}
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
        ${getTransformationBanner("cfg")}
        <div class="semantic-status success">
            ✓ Control Flow Graph constructed — ${blocks.length} basic blocks partitioned
        </div>

        <div class="cfg-statistics">
            <strong>CFG Graph Statistics</strong>
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
            <span>➔ Direct Control-flow Edge</span>
            <span>Labels: <strong>true / false</strong> indicate conditional branch targets</span>
        </div>
    `;
}

/* =========================================================
   STAGE 09: OPTIMIZER
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
        ? `✓ Optimized TAC differs in ${transformations.length} transformation segment(s)`
        : "✓ No optimization opportunities found — the TAC is already canonical";

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
                    <strong>${escapeHTML(transformation.kind)} Pass</strong>
                    ${before ? `<div><span>Before:</span> ${before}</div>` : ""}
                    ${after ? `<div><span>After:</span> ${after}</div>` : ""}
                </div>
            `;
        }).join("")
        : `<p class="optimization-no-transformations">No instruction rewrites performed by the optimizer passes.</p>`;

    visualization.innerHTML = `
        ${getTransformationBanner("optimizer")}
        <div class="semantic-status success">${status}</div>

        <div class="optimization-statistics">
            <strong>Optimization Statistics</strong>
            ${statisticItems.map(([label, value]) => `<span>${label}: ${escapeHTML(value)}</span>`).join("")}
        </div>

        <div class="optimization-flow" aria-label="TAC optimization flow">
            <span>Original TAC</span><b>→</b>
            <span>Constant Folding</span><b>→</b>
            <span>Constant Propagation</span><b>→</b>
            <span>Identity Simplification</span><b>→</b>
            <span>Optimized TAC</span>
        </div>

        <div class="tac-compare">
            <div class="tac-table-wrapper">
                <div class="tac-title">Original TAC (Before Optimization)</div>
                <table>
                    <thead><tr><th>#</th><th>Instruction</th></tr></thead>
                    <tbody>${tacRowsHTML(result.original)}</tbody>
                </table>
            </div>
            <div class="tac-table-wrapper">
                <div class="tac-title">Optimized TAC (After Passes)</div>
                <table>
                    <thead><tr><th>#</th><th>Instruction</th></tr></thead>
                    <tbody>${tacRowsHTML(result.optimized)}</tbody>
                </table>
            </div>
        </div>

        <section class="optimization-transformations">
            <h3>Observed Transformations</h3>
            ${transformationMarkup}
        </section>
    `;
}

/* =========================================================
   STAGE 10: BACKEND
   ========================================================= */

function showBackend(result) {
    const instructions = result.instructions || [];
    const statistics = result.statistics || {};

    const rows = instructions.map(function(instruction) {
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

    const labels = [
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

    visualization.innerHTML = `
        ${getTransformationBanner("backend")}
        <div class="semantic-status success">✓ Target stack machine code emitted successfully</div>

        <div class="lexer-statistics">
            <strong>Backend Code Generation Statistics</strong>
            ${labels.map(([label, value]) => `<span>${label}: ${escapeHTML(value)}</span>`).join("")}
        </div>

        <div class="tac-table-wrapper">
            <div class="tac-title">Target Disassembly (Stack Machine Instructions)</div>
            <table>
                <thead>
                    <tr>
                        <th>PC</th>
                        <th>Opcode</th>
                        <th>Operand 1</th>
                        <th>Operand 2</th>
                        <th>Formatted Instruction</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

/* =========================================================
   STAGE 11: VM
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
        ? `<div class="semantic-status error"><strong>EXECUTION LIMIT REACHED</strong> — Stopped after ${result.steps} steps. Reason: ${escapeHTML(result.runtime_error)}</div>`
        : result.status === "runtime_error" || result.runtime_error
            ? `<div class="semantic-status error"><strong>RUNTIME ERROR</strong> — Execution halted. Reason: ${escapeHTML(result.runtime_error)}</div>`
            : `<div class="semantic-status success"><strong>✓ EXECUTION SUCCESSFUL</strong> — Completed in ${result.steps} step(s).</div>`;

    const truncated = result.trace_truncated
        ? `<p>Trace recording is capped; showing the first ${result.trace.length} entries for ${result.steps} completed VM steps.</p>`
        : "";

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
        ${getTransformationBanner("vm")}
        ${status}

        <div class="tac-compare">
            <div class="tac-table-wrapper">
                <div class="tac-title">Target Program</div>
                <table>
                    <thead>
                        <tr><th>PC</th><th>Opcode</th><th>Operand 1</th><th>Operand 2</th><th>Instruction</th></tr>
                    </thead>
                    <tbody>${program}</tbody>
                </table>
            </div>

            <div class="tac-table-wrapper">
                <div class="tac-title">Final VM Memory (Variables)</div>
                <table>
                    <thead>
                        <tr><th>Variable Name</th><th>Runtime Value</th></tr>
                    </thead>
                    <tbody>${memory.length ? memory : "<tr><td colspan='2'>No variables stored.</td></tr>"}</tbody>
                </table>
            </div>
        </div>

        <section class="vm-stack-panel">
            <h3>Final VM Operand Stack</h3>
            ${stackMarkup}
            ${stack.length ? "<div class=\"vm-stack-bottom\">BOTTOM</div>" : ""}
        </section>

        <div class="tac-table-wrapper">
            <div class="tac-title">Step-by-Step Execution Trace</div>
            ${truncated}
            <div class="token-table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Step</th>
                            <th>PC</th>
                            <th>Instruction</th>
                            <th>Stack Before</th>
                            <th>Stack After</th>
                            <th>Memory State</th>
                            <th>Output</th>
                            <th>Error</th>
                        </tr>
                    </thead>
                    <tbody>${trace}</tbody>
                </table>
            </div>
        </div>

        <section class="vm-output-panel">
            <h3>Standard Console Output</h3>
            <pre class="tac-code program-output">${outputMarkup}</pre>
        </section>
    `;
}

/* =========================================================
   STAGE 12: OUTPUT
   ========================================================= */

function showOutput(result) {
    const output = result.output;

    const status = result.status === "execution_limit"
        ? `<div class="semantic-status error"><strong>EXECUTION LIMIT REACHED</strong><br>Execution stopped.<br>Reason: ${escapeHTML(result.runtime_error)}</div>`
        : result.status === "runtime_error" || result.runtime_error
            ? `<div class="semantic-status error"><strong>RUNTIME ERROR</strong><br>Execution failed.<br>Reason: ${escapeHTML(result.runtime_error)}</div>`
            : `<div class="semantic-status success"><strong>✓ PIPELINE EXECUTION SUCCESSFUL</strong> — Program ran to completion.</div>`;

    visualization.innerHTML = `
        ${getTransformationBanner("output")}
        ${status}

        <h3>Program Output (stdout)</h3>
        <pre class="tac-code program-output">${
            output
                ? escapeHTML(output)
                : "(the program completed and printed nothing to stdout)"
        }</pre>

        <p>
            The entire 12-stage compilation and execution pipeline has completed successfully.
        </p>
    `;
}

function showSyntaxError(error) {
    const details = error.details || {};
    const context = details.source_context;

    visualization.innerHTML = `
        ${getTransformationBanner("parser")}
        <div class="semantic-status error">✕ Syntax Analysis Failed</div>
        <div class="semantic-error">
            <strong>Syntax Error: Unexpected ${escapeHTML(details.unexpected || "token")}</strong>
            <p>The parser encountered a syntax error while validating against the MiniLang-X grammar.</p>
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

function showExecutionUnavailable(error) {
    const message = error.message || String(error);
    const backendFailure = message.startsWith("Backend Generation Failed:");
    const compilationFailure = /^(Lexical Error|Syntax Error|Semantic Error|Parser Error|TAC Error|CFG Error|Optimizer Error):/.test(message);
    const title = backendFailure
        ? "Backend Generation Failed"
        : compilationFailure
            ? "Compilation Error"
            : "Execution Unavailable";
    const reason = backendFailure
        ? message.slice("Backend Generation Failed:".length).trim()
        : message;

    visualization.innerHTML = `
        <div class="semantic-status error">✕ ${title}</div>
        <div class="semantic-error">
            <strong>Reason:</strong>
            <p>${escapeHTML(reason)}</p>
        </div>
    `;
}

function showStageError(stageKey, error) {
    const labels = {
        lexer: "Lexical Analysis",
        parser: "Syntax Analysis",
        precedence: "Operator Precedence",
        ast: "AST Generation",
        semantic: "Semantic Analysis",
        tac: "TAC Generation",
        cfg: "CFG Generation",
        optimizer: "Optimization",
    };
    const label = labels[stageKey] || "Compilation";

    visualization.innerHTML = `
        ${getTransformationBanner(stageKey)}
        <div class="semantic-status error">✕ ${escapeHTML(label)} Failed</div>
        <div class="semantic-error">
            <strong>Error Details:</strong>
            <p>${escapeHTML(error.message || "The compiler stage failed.")}</p>
        </div>
    `;
}

/* =========================================================
   PIPELINE STAGE DEFINITIONS & DISPATCH
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
            const result = await getSemantic();
            state.semantic = result;
            if (result.valid) {
                state.diagnostic = null;
            }
            showSemantic(result);
            if (!result.valid) {
                nextButton.disabled = true;
                compileButton.disabled = false;
                runButton.disabled = false;
            }
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
            state.optimized = await getOptimized();
            showOptimizer(state.optimized);
        },
    },
    backend: {
        nextStep: 9,
        show: async function() {
            state.run = state.run || await getRun();
            showBackend(state.run);
        },
    },
    vm: {
        nextStep: 10,
        show: async function() {
            state.run = state.run || await getRun();
            showVM(state.run);
        },
    },
    output: {
        nextStep: 11,
        show: async function() {
            state.run = state.run || await getRun();
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
    8: "backend",
    9: "vm",
    10: "output",
};

function setActiveStage(stageKey) {
    state.currentStage = stageKey;
    stageButtons.forEach(function(button) {
        const isActive = button.dataset.stage === stageKey;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-current", isActive ? "step" : "false");
        button.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    renderNavigationState();
}

async function runStage(stageKey) {
    const stage = pipelineStages[stageKey];
    if (!stage) return;

    const requestId = ++navigationRequest;
    setActiveStage(stageKey);
    state.step = stage.nextStep;
    state.errorStage = null;
    state.navigationBlocked = false;
    setCompilerStatus("running", "Compiling...");
    renderNavigationState();
    nextButton.disabled = false;
    if (stageKey === "source") {
        nextButton.disabled = !state.completedStages.lexer;
    }
    compileButton.disabled = stageKey !== "source";
    runButton.disabled = stageKey !== "source";

    const stageButton = document.querySelector(`.stage[data-stage="${stageKey}"]`);
    if (stageButton) {
        stageButton.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
            inline: "center",
        });
    }

    try {
        await stage.show();
        if (requestId !== navigationRequest) {
            return false;
        }
        state.completedStages[stageKey] = true;
        if (stageKey !== "source") {
            state.completedStages.source = true;
        }
        state.errorStage = stageKey === "semantic" && state.semantic && !state.semantic.valid
            ? "semantic"
            : null;
        if (state.errorStage) {
            state.diagnostic = state.semantic.errors?.[0] || state.semantic.error_details;
            state.navigationBlocked = true;
            setCompilerStatus("error", "Compilation Failed");
        } else if (stageKey === "output" && state.run) {
            const succeeded = state.run.status === "success"
                || state.run.status === "completed"
                || (!state.run.runtime_error && state.run.status !== "execution_limit");
            setCompilerStatus(
                succeeded ? "success" : "error",
                succeeded ? "Compilation Successful" : "Compilation Failed"
            );
        } else if (stageKey === "source") {
            setCompilerStatus(null, "Ready");
        } else {
            setCompilerStatus(null, `${stageLabels[stageKey]} ready`);
        }
        compileButton.disabled = false;
        runButton.disabled = false;
        renderNavigationState();
        return !nextButton.disabled;
    } catch (error) {
        if (requestId !== navigationRequest || error.name === "StaleStageResponse") {
            return false;
        }
        state.errorStage = stageKey;
        state.navigationBlocked = true;
        state.diagnostic = {
            type: error.details?.type || `${stageLabels[stageKey] || "Compiler"} Error`,
            message: error.message || "The compiler stage failed.",
            line: error.details?.line,
            column: error.details?.column,
            source_context: error.details?.source_context,
        };
        nextButton.disabled = true;
        compileButton.disabled = false;
        runButton.disabled = false;
        setCompilerStatus("error", "Compilation Failed");

        if (error.details?.type === "Syntax Error") {
            showSyntaxError(error);
        } else if (stageKey === "tac" && error.message.startsWith("Semantic Error:")) {
            showTACUnavailable(error);
        } else if (["backend", "vm", "output"].includes(stageKey)) {
            showExecutionUnavailable(error);
        } else {
            showStageError(stageKey, error);
        }
        renderNavigationState();
        const button = document.querySelector(`.stage[data-stage="${stageKey}"]`);
        if (button) {
            button.dataset.stageStatus = "error";
        }
        return false;
    }
}

/* =========================================================
   WALKTHROUGH & CONTROLS
   ========================================================= */

nextButton.addEventListener("click", async function() {
    if (state.step >= 11) {
        nextButton.style.display = "none";
        nextButton.disabled = true;
        compileButton.disabled = false;
        visualization.innerHTML += `
            <div class="semantic-status success">
                ✓ All compiler pipeline stages completed successfully
            </div>
        `;
        return;
    }

    const nextStage = nextStepStages[state.step];
    if (nextStage) {
        await runStage(nextStage);
    }
});

previousButton.addEventListener("click", async function() {
    const currentIndex = stageOrder.indexOf(state.currentStage);
    if (currentIndex > 0) {
        await runStage(stageOrder[currentIndex - 1]);
    }
});

compileButton.addEventListener("click", async function() {
    resetCompilation();
    await runStage("lexer");
});

if (editorCompileBtn) {
    editorCompileBtn.addEventListener("click", async function() {
        compileButton.click();
    });
}

runButton.addEventListener("click", async function() {
    resetCompilation();
    await runStage("output");
});

runAllButton.addEventListener("click", async function() {
    resetCompilation();
    for (const stageKey of stageOrder.slice(1)) {
        const succeeded = await runStage(stageKey);
        if (!succeeded) {
            return;
        }
    }
});

function resetCompilation() {
    navigationRequest += 1;
    state = {
        step: 0,
        currentStage: "source",
        completedStages: {},
        diagnostic: null,
        navigationBlocked: false,
        tokens: null,
        ast: null,
        astStatistics: null,
        semantic: null,
        tac: null,
        cfg: null,
        optimized: null,
        run: null,
    };
    compileButton.disabled = false;
    runButton.disabled = false;
    nextButton.disabled = false;
    nextButton.textContent = "Next Step →";
    nextButton.style.display = "inline-block";
    setActiveStage("source");
    showSource();
    setCompilerStatus(null, "Ready");
    renderNavigationState();
}

resetButton.addEventListener("click", function() {
    resetCompilation();
});

sourceBox.addEventListener("scroll", function() {
    lineNumbers.scrollTop = sourceBox.scrollTop;
});

document.addEventListener("keydown", function(event) {
    if (event.ctrlKey && event.key === "Enter") {
        event.preventDefault();
        compileButton.click();
    } else if (event.key === "F5") {
        event.preventDefault();
        runButton.click();
    } else if (event.key === "F10") {
        event.preventDefault();
        nextButton.click();
    } else if (event.key === "Escape") {
        event.preventDefault();
        resetButton.click();
    }
});

document.querySelectorAll(".stage[data-stage]").forEach(function(stageButton) {
    stageButton.addEventListener("click", async function() {
        await runStage(stageButton.dataset.stage);
    });
});

sourceBox.addEventListener("input", function() {
    navigationRequest += 1;
    state = {
        step: 0,
        currentStage: "source",
        completedStages: {},
        diagnostic: null,
        navigationBlocked: false,
        tokens: null,
        ast: null,
        astStatistics: null,
        semantic: null,
        tac: null,
        cfg: null,
        optimized: null,
        run: null,
    };
    compileButton.disabled = false;
    runButton.disabled = false;
    nextButton.disabled = false;
    nextButton.style.display = "inline-block";
    setActiveStage("source");
    showSource();
    updateLineNumbers();
    setCompilerStatus(null, "Ready");
    renderNavigationState();
});

/* Initialize */
setActiveStage("source");
showSource();
updateLineNumbers();
renderNavigationState();
