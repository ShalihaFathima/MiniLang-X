const sourceBox = document.getElementById("source-code");
const compileButton = document.getElementById("compile-button");
const visualization = document.getElementById("visualization");

let nextButton = document.getElementById("next-step-button");

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
        throw new Error(data.error || "Compiler stage failed");
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

    const tokens = data.tokens || data;

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

        rows += `
            <tr>
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

            <h2>Lexer</h2>

            <p>
                The lexer converts source characters into tokens.
            </p>

            <div class="semantic-status success">
                ✓ Lexical analysis completed
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
}


/* =========================================================
   PARSER
   ========================================================= */

function showParser() {

    visualization.innerHTML = `
        <div class="panel">

            <h2>Parser</h2>

            <p>
                The parser checks the token sequence against the
                MiniLang-X grammar and builds a structured tree.
            </p>

            <div class="semantic-status success">
                ✓ Parsing successful
            </div>

            <div class="parser-flow">

                <div class="parser-item">Tokens</div>

                <div class="parser-arrow">→</div>

                <div class="parser-item">Grammar</div>

                <div class="parser-arrow">→</div>

                <div class="parser-item">AST</div>

            </div>

            <p>
                Next, the expression tree demonstrates
                operator precedence.
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
                    ✗ No expression found
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

    const label =
        node.label ||
        node.operator ||
        node.name ||
        node.value ||
        node.type;


    let html = `
        <div class="ast-node">

            <div class="ast-box ${escapeHTML(node.type || "")}">
                ${escapeHTML(label)}
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


    html += `
        </div>
    `;

    return html;
}


function drawASTTree(root) {

    const width = 900;
    const height = 620;

    const nodeWidth = 125;
    const nodeHeight = 58;

    const positions = new Map();


    function getLeaves(node, result = []) {

        const children = node.children || [];

        if (children.length === 0) {
            result.push(node);
            return result;
        }

        children.forEach(child => {
            getLeaves(child, result);
        });

        return result;
    }


    const leaves = getLeaves(root);

    const leafSpacing =
        Math.min(
            170,
            (width - 100) /
            Math.max(leaves.length, 1)
        );


    function getDepth(node) {

        const children = node.children || [];

        if (!children.length) {
            return 0;
        }

        return 1 +
            Math.max(
                ...children.map(getDepth)
            );
    }


    const depth = getDepth(root);

    const verticalSpacing =
        Math.min(
            125,
            (height - 100) /
            Math.max(depth + 1, 1)
        );


    function assign(node, level) {

        const children = node.children || [];

        if (!children.length) {

            const index =
                leaves.indexOf(node);

            positions.set(node, {
                x: 50 + index * leafSpacing,
                y: 55 + depth * verticalSpacing
            });

            return;
        }


        children.forEach(child => {
            assign(child, level + 1);
        });


        const childPositions =
            children.map(child =>
                positions.get(child)
            );


        const minX =
            Math.min(
                ...childPositions.map(p => p.x)
            );

        const maxX =
            Math.max(
                ...childPositions.map(p => p.x)
            );


        positions.set(node, {
            x: (minX + maxX) / 2,
            y: 55 + level * verticalSpacing
        });
    }


    assign(root, 0);


    let edges = "";
    let nodes = "";


    function nodeLabel(node) {

        if (node.type === "Program") {
            return "Program";
        }

        if (node.type === "Block") {
            return "Block";
        }

        if (node.type === "VarDeclaration") {
            return node.label || node.name;
        }

        if (node.type === "PrintStatement") {
            return "Print";
        }

        if (node.type === "Assignment") {
            return node.label || node.name;
        }

        if (node.type === "BinaryExpression") {
            return node.operator;
        }

        if (node.type === "UnaryExpression") {
            return node.operator;
        }

        if (node.type === "Literal") {
            return node.value;
        }

        if (node.type === "Identifier") {
            return node.name;
        }

        return node.label || node.type;
    }


    function nodeClass(node) {

        if (node.type === "Program") {
            return "ast-svg-program";
        }

        if (node.type === "VarDeclaration") {
            return "ast-svg-declaration";
        }

        if (node.type === "PrintStatement") {
            return "ast-svg-print";
        }

        if (
            node.type === "BinaryExpression" ||
            node.type === "UnaryExpression"
        ) {
            return "ast-svg-operator";
        }

        return "ast-svg-leaf";
    }


    function renderEdges(node) {

        const parent =
            positions.get(node);

        const children =
            node.children || [];


        children.forEach(child => {

            const childPosition =
                positions.get(child);


            edges += `
                <line
                    x1="${parent.x}"
                    y1="${parent.y + nodeHeight / 2}"
                    x2="${childPosition.x}"
                    y2="${childPosition.y - nodeHeight / 2}"
                    class="ast-svg-edge"
                    marker-end="url(#ast-arrow)"
                />
            `;


            renderEdges(child);
        });
    }


    renderEdges(root);


    positions.forEach((position, node) => {

        const label =
            nodeLabel(node);

        nodes += `
            <g>

                <rect
                    x="${position.x - nodeWidth / 2}"
                    y="${position.y - nodeHeight / 2}"
                    width="${nodeWidth}"
                    height="${nodeHeight}"
                    rx="10"
                    class="${nodeClass(node)}"
                />

                <text
                    x="${position.x}"
                    y="${position.y + 7}"
                    text-anchor="middle"
                    class="ast-svg-text"
                >
                    ${escapeHTML(label)}
                </text>

            </g>
        `;
    });


    return `
        <svg
            class="ast-svg-tree"
            viewBox="0 0 ${width} ${height}"
            preserveAspectRatio="xMidYMid meet"
        >

            <defs>

                <marker
                    id="ast-arrow"
                    markerWidth="8"
                    markerHeight="8"
                    refX="7"
                    refY="4"
                    orient="auto"
                >

                    <path
                        d="M0,0 L8,4 L0,8 Z"
                        class="ast-arrow-head"
                    />

                </marker>

            </defs>

            ${edges}

            ${nodes}

        </svg>
    `;
}


function showAST(ast) {

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

            <div class="ast-svg-wrapper">

                ${drawASTTree(ast)}

            </div>

        </div>
    `;
}


/* =========================================================
   SEMANTIC
   ========================================================= */

function showSemantic(result) {

    if (!result.valid) {

        visualization.innerHTML = `
            <div class="panel">

                <h2>Semantic Analysis</h2>

                <div class="semantic-status error">
                    ✗ Semantic analysis failed
                </div>

                <div class="semantic-error">
                    ${escapeHTML(result.error)}
                </div>

            </div>
        `;

        return;
    }


    let rows = "";

    (result.symbols || []).forEach(function(symbol) {

        rows += `
            <tr>
                <td>${escapeHTML(symbol.name)}</td>
                <td>${escapeHTML(symbol.data_type)}</td>
                <td>${symbol.scope_level}</td>
                <td>${symbol.initialized ? "Yes" : "No"}</td>
            </tr>
        `;
    });


    visualization.innerHTML = `
        <div class="panel">

            <h2>Semantic Analysis</h2>

            <p>
                The semantic analyzer verifies declarations,
                scopes, types, and valid operations.
            </p>

            <div class="semantic-status success">
                ✓ Semantic analysis completed successfully
            </div>

            <table class="token-table">

                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Type</th>
                        <th>Scope</th>
                        <th>Initialized</th>
                    </tr>
                </thead>

                <tbody>
                    ${rows}
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

            const tac =
                tacInstructionText(instruction);


            rows += `
                <tr>

                    <td>
                        ${String(index).padStart(3, "0")}
                    </td>

                    <td>
                        <code>
                            ${escapeHTML(tac)}
                        </code>
                    </td>

                </tr>
            `;
        }
    );


    visualization.innerHTML = `
        <div class="panel">

            <h2>Three Address Code (TAC)</h2>

            <p>
                The AST is translated into an intermediate
                representation where each instruction performs
                a simple operation.
            </p>

            <div class="semantic-status success">
                ✓ TAC generation successful
            </div>


            <div class="tac-table-wrapper">

                <table>

                    <thead>

                        <tr>
                            <th>#</th>
                            <th>Instruction</th>
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


/* =========================================================
   CFG GRAPH
   ========================================================= */

function cfgHeight(block) {

    return 75 +
        Math.max(
            1,
            block.instructions.length
        ) * 32;
}


function cfgLayout(blocks) {

    const positions = {};

    if (blocks.length === 1) {

        positions[blocks[0].id] = {
            x: 400,
            y: 60
        };

        return positions;
    }


    /*
       Typical while-loop:

                     B0
                      ↓
                     B1
                   ↙    ↘
                 B2      B3
                  ↖
                   ┘
    */

    if (
        blocks.some(b => b.id === 0) &&
        blocks.some(b => b.id === 1) &&
        blocks.some(b => b.id === 2) &&
        blocks.some(b => b.id === 3)
    ) {

        positions[0] = {
            x: 330,
            y: 30
        };

        positions[1] = {
            x: 330,
            y: 230
        };

        positions[2] = {
            x: 100,
            y: 470
        };

        positions[3] = {
            x: 560,
            y: 470
        };

        return positions;
    }


    blocks.forEach(function(block, index) {

        positions[block.id] = {
            x: 300 + (index % 2) * 280,
            y: 50 + Math.floor(index / 2) * 220
        };

    });


    return positions;
}


function showCFG(result) {

    const blocks = result.blocks || [];

    if (!blocks.length) {

        visualization.innerHTML = `
            <div class="panel">

                <h2>Control Flow Graph (CFG)</h2>

                <div class="semantic-status error">
                    ✗ No basic blocks generated
                </div>

            </div>
        `;

        return;
    }


    /*
     * Special layout for the common while-loop structure:
     *
     *                 B0
     *                 ↓
     *                 B1
     *               ↙    ↘
     *             B2      B3
     *              ↖
     *               ┘
     */

    const isFourBlockLoop =
        blocks.length === 4 &&
        blocks.some(b => b.id === 0) &&
        blocks.some(b => b.id === 1) &&
        blocks.some(b => b.id === 2) &&
        blocks.some(b => b.id === 3);


    const positions = {};

    if (isFourBlockLoop) {

        positions[0] = {
            x: 450,
            y: 70
        };

        positions[1] = {
            x: 450,
            y: 260
        };

        positions[2] = {
            x: 200,
            y: 500
        };

        positions[3] = {
            x: 700,
            y: 500
        };

    } else {

        blocks.forEach(function(block, index) {

            positions[block.id] = {
                x: 450,
                y: 70 + index * 180
            };

        });

    }


    const nodeWidth = 260;


    function blockHeight(block) {

        return 70 +
            Math.max(
                1,
                block.instructions.length
            ) * 30;

    }


    const svgWidth = 900;
    const svgHeight =
        isFourBlockLoop ? 700 :
        Math.max(
            500,
            blocks.length * 180 + 100
        );


    let edges = "";


    /*
     * Draw every real CFG edge.
     */

    blocks.forEach(function(block) {

        const source =
            positions[block.id];

        if (!source) {
            return;
        }


        const sourceHeight =
            blockHeight(block);


        (block.successors || [])
            .forEach(function(targetId) {

                const target =
                    positions[targetId];

                if (!target) {
                    return;
                }


                /*
                 * Loop-back edge:
                 *
                 * B2 → B1
                 *
                 * Draw it around the left side.
                 */

                if (targetId === 1 && block.id === 2) {

                    const startX =
                        source.x - nodeWidth / 2;

                    const startY =
                        source.y + sourceHeight / 2;


                    const endX =
                        target.x - nodeWidth / 2;

                    const endY =
                        target.y + blockHeight(
                            blocks.find(
                                b => b.id === targetId
                            )
                        ) / 2;


                    edges += `
                        <path
                            d="
                                M ${startX} ${startY}
                                C 40 ${startY},
                                  40 ${endY},
                                  ${endX} ${endY}
                            "
                            class="cfg-loop-edge"
                            marker-end="url(#cfg-loop-arrow)"
                        />
                    `;

                    return;
                }


                /*
                 * B1 → B2
                 */

                if (block.id === 1 && targetId === 2) {

                    const startX =
                        source.x - nodeWidth / 2 + 20;

                    const startY =
                        source.y +
                        blockHeight(block);


                    const endX =
                        target.x;

                    const endY =
                        target.y;


                    edges += `
                        <path
                            d="
                                M ${startX} ${startY}
                                C ${startX - 40} ${startY + 70},
                                  ${endX} ${endY - 70},
                                  ${endX} ${endY}
                            "
                            class="cfg-edge"
                            marker-end="url(#cfg-arrow)"
                        />

                        <text
                            x="${(startX + endX) / 2 - 30}"
                            y="${(startY + endY) / 2}"
                            class="cfg-edge-label"
                        >
                            true
                        </text>
                    `;

                    return;
                }


                /*
                 * B1 → B3
                 */

                if (block.id === 1 && targetId === 3) {

                    const startX =
                        source.x + nodeWidth / 2 - 20;

                    const startY =
                        source.y +
                        blockHeight(block);


                    const endX =
                        target.x;

                    const endY =
                        target.y;


                    edges += `
                        <path
                            d="
                                M ${startX} ${startY}
                                C ${startX + 40} ${startY + 70},
                                  ${endX} ${endY - 70},
                                  ${endX} ${endY}
                            "
                            class="cfg-edge"
                            marker-end="url(#cfg-arrow)"
                        />

                        <text
                            x="${(startX + endX) / 2 + 15}"
                            y="${(startY + endY) / 2}"
                            class="cfg-edge-label"
                        >
                            false
                        </text>
                    `;

                    return;
                }


                /*
                 * Normal edge.
                 */

                const startX =
                    source.x;

                const startY =
                    source.y +
                    blockHeight(block);

                const endX =
                    target.x;

                const endY =
                    target.y;


                edges += `
                    <path
                        d="
                            M ${startX} ${startY}
                            C ${startX} ${startY + 60},
                              ${endX} ${endY - 60},
                              ${endX} ${endY}
                        "
                        class="cfg-edge"
                        marker-end="url(#cfg-arrow)"
                    />
                `;

            });

    });


    let nodes = "";


    blocks.forEach(function(block) {

        const position =
            positions[block.id];

        const height =
            blockHeight(block);


        const instructionHTML =
            block.instructions
                .map(function(instruction) {

                    return `
                        <div class="cfg-instruction">
                            ${escapeHTML(instruction)}
                        </div>
                    `;

                })
                .join("");


        nodes += `
            <g>

                <rect
                    x="${position.x - nodeWidth / 2}"
                    y="${position.y}"
                    width="${nodeWidth}"
                    height="${height}"
                    rx="12"
                    class="cfg-node"
                />

                <rect
                    x="${position.x - nodeWidth / 2}"
                    y="${position.y}"
                    width="${nodeWidth}"
                    height="48"
                    rx="12"
                    class="cfg-header"
                />

                <rect
                    x="${position.x - nodeWidth / 2}"
                    y="${position.y + 36}"
                    width="${nodeWidth}"
                    height="12"
                    class="cfg-header"
                />

                <text
                    x="${position.x}"
                    y="${position.y + 31}"
                    text-anchor="middle"
                    class="cfg-header-text"
                >
                    B${block.id}
                </text>

                ${block.instructions.map(
                    function(instruction, index) {

                        return `
                            <text
                                x="${position.x - nodeWidth / 2 + 15}"
                                y="${
                                    position.y +
                                    75 +
                                    index * 30
                                }"
                                class="cfg-instruction-text"
                            >
                                ${escapeHTML(instruction)}
                            </text>
                        `;

                    }
                ).join("")}

            </g>
        `;

    });


    visualization.innerHTML = `
        <div class="panel">

            <h2>Control Flow Graph (CFG)</h2>

            <p>
                Each node is a basic block. Arrows show the
                possible execution paths between blocks.
            </p>

            <div class="semantic-status success">
                ✓ Control Flow Graph generated successfully
            </div>

            <div class="cfg-graph-container">

                <svg
                    class="cfg-graph-svg"
                    viewBox="0 0 ${svgWidth} ${svgHeight}"
                    preserveAspectRatio="xMidYMid meet"
                >

                    <defs>

                        <marker
                            id="cfg-arrow"
                            markerWidth="10"
                            markerHeight="10"
                            refX="8"
                            refY="5"
                            orient="auto"
                        >
                            <path
                                d="M0,0 L10,5 L0,10 Z"
                                class="cfg-arrow-head"
                            />
                        </marker>


                        <marker
                            id="cfg-loop-arrow"
                            markerWidth="10"
                            markerHeight="10"
                            refX="8"
                            refY="5"
                            orient="auto"
                        >
                            <path
                                d="M0,0 L10,5 L0,10 Z"
                                class="cfg-loop-arrow-head"
                            />
                        </marker>

                    </defs>

                    ${edges}

                    ${nodes}

                </svg>

            </div>

            <div class="cfg-legend">

                <span>
                    <i class="legend-normal"></i>
                    Normal / branch flow
                </span>

                <span>
                    <i class="legend-loop"></i>
                    Loop-back edge
                </span>

            </div>

        </div>
    `;
}


/* =========================================================
   OPTIMIZER
   ========================================================= */

function tacRowsHTML(instructions, highlighted) {

    return instructions.map(function(instruction, index) {

        const cls =
            highlighted && highlighted.includes(index)
                ? ' class="tac-changed"'
                : "";

        return `
            <tr${cls}>
                <td>${String(index).padStart(3, "0")}</td>
                <td><code>${escapeHTML(tacInstructionText(instruction))}</code></td>
            </tr>
        `;
    }).join("");
}


function showOptimizer(result) {

    const status = result.changed
        ? `✓ Optimization changed ${result.changed_indices.length} instruction(s)
           (${result.original.length} → ${result.optimized.length} instructions)`
        : "✓ No optimization opportunities found — the TAC is unchanged";

    visualization.innerHTML = `
        <div class="panel">

            <h2>Optimizer</h2>

            <p>
                The optimizer applies constant folding, constant
                propagation and algebraic simplification to the TAC.
                Changed instructions are highlighted.
            </p>

            <div class="semantic-status success">
                ${status}
            </div>

            <div class="tac-compare">

                <div class="tac-table-wrapper">
                    <div class="tac-title">Original TAC</div>
                    <table>
                        <thead>
                            <tr><th>#</th><th>Instruction</th></tr>
                        </thead>
                        <tbody>
                            ${tacRowsHTML(result.original)}
                        </tbody>
                    </table>
                </div>

                <div class="tac-table-wrapper">
                    <div class="tac-title">Optimized TAC</div>
                    <table>
                        <thead>
                            <tr><th>#</th><th>Instruction</th></tr>
                        </thead>
                        <tbody>
                            ${tacRowsHTML(result.optimized, result.changed_indices)}
                        </tbody>
                    </table>
                </div>

            </div>

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
                <td><code>${escapeHTML(instruction.text)}</code></td>
            </tr>
        `;
    }).join("");


    const trace = result.trace.map(function(entry) {

        return `
            <tr>
                <td>${entry.step}</td>
                <td>${String(entry.pc).padStart(3, "0")}</td>
                <td><code>${escapeHTML(entry.instruction)}</code></td>
                <td><code>[${escapeHTML(entry.stack.join(", "))}]</code></td>
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


    const status = result.runtime_error
        ? `<div class="semantic-status error">✗ ${escapeHTML(result.runtime_error)}</div>`
        : `<div class="semantic-status success">
               ✓ Executed ${result.steps} instruction(s) and halted
           </div>`;

    const truncated = result.trace_truncated
        ? `<p>Showing the first ${result.trace.length} of ${result.steps} steps.</p>`
        : "";


    visualization.innerHTML = `
        <div class="panel">

            <h2>Virtual Machine</h2>

            <p>
                The code generator turns the optimized TAC into
                stack-machine instructions, which the VM executes.
            </p>

            ${status}

            <div class="tac-compare">

                <div class="tac-table-wrapper">
                    <div class="tac-title">Target Program</div>
                    <table>
                        <thead>
                            <tr><th>#</th><th>Instruction</th></tr>
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

            <div class="tac-table-wrapper">
                <div class="tac-title">Execution Trace</div>
                ${truncated}
                <table>
                    <thead>
                        <tr><th>Step</th><th>PC</th><th>Instruction</th><th>Stack after</th></tr>
                    </thead>
                    <tbody>${trace}</tbody>
                </table>
            </div>

        </div>
    `;
}


/* =========================================================
   OUTPUT
   ========================================================= */

function showOutput(result) {

    const output = result.output;

    const status = result.runtime_error
        ? `<div class="semantic-status error">✗ ${escapeHTML(result.runtime_error)}</div>`
        : `<div class="semantic-status success">✓ Program finished</div>`;

    visualization.innerHTML = `
        <div class="panel">

            <h2>Program Output</h2>

            <p>
                Output printed by the program while running on the VM.
            </p>

            ${status}

            <pre class="tac-code program-output">${
                output
                    ? escapeHTML(output)
                    : "(the program printed nothing)"
            }</pre>

        </div>
    `;
}


/* =========================================================
   PIPELINE BUTTONS
   ========================================================= */

async function runStage(name) {

    const stage =
        name.toLowerCase();


    try {

        if (stage.includes("source")) {

            showSource();
            return;
        }


        if (stage.includes("lexer")) {

            state.tokens =
                await getTokens();

            showLexer(state.tokens);
            return;
        }


        if (stage.includes("parser")) {

            state.ast =
                normalizeAST(
                    await getAST()
                );

            showParser();
            return;
        }


        if (stage.includes("precedence")) {

            if (!state.ast) {

                state.ast =
                    normalizeAST(
                        await getAST()
                    );
            }

            showPrecedence(state.ast);
            return;
        }


        if (
            stage === "ast" ||
            stage.includes("abstract syntax")
        ) {

            if (!state.ast) {

                state.ast =
                    normalizeAST(
                        await getAST()
                    );
            }

            showAST(state.ast);
            return;
        }


        if (stage.includes("semantic")) {

            showSemantic(
                await getSemantic()
            );

            return;
        }


        if (stage.includes("tac")) {

            state.tac =
                await getTAC();

            showTAC(state.tac);
            return;
        }


        if (stage.includes("cfg")) {

            state.cfg =
                await getCFG();

            showCFG(state.cfg);
            return;
        }


        if (stage.includes("optimizer")) {

            showOptimizer(
                await getOptimized()
            );

            return;
        }


        if (stage === "vm") {

            state.run =
                await getRun();

            showVM(state.run);
            return;
        }


        if (stage.includes("output")) {

            state.run =
                await getRun();

            showOutput(state.run);
            return;
        }


        visualization.innerHTML = `
            <div class="panel">

                <h2>${escapeHTML(name)}</h2>

                <p>
                    No visualization is available for this stage.
                </p>

            </div>
        `;

    } catch (error) {

        visualization.innerHTML = `
            <div class="panel">

                <h2>Compilation Error</h2>

                <div class="semantic-status error">
                    ✗ ${escapeHTML(error.message)}
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

            if (state.step === 0) {

                state.tokens =
                    await getTokens();

                showLexer(state.tokens);

                state.step = 1;

                return;
            }


            if (state.step === 1) {

                state.ast =
                    normalizeAST(
                        await getAST()
                    );

                showParser();

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
                    state.ast
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

            visualization.innerHTML = `
                <div class="panel">

                    <h2>Compilation Error</h2>

                    <div class="semantic-status error">
                        ✗ ${escapeHTML(error.message)}
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
            tac: null,
            cfg: null,
            run: null
        };

        compileButton.disabled = true;

        nextButton.textContent =
            "Next Step →";

        nextButton.style.display =
            "inline-block";

        showSource();
    }
);


/* =========================================================
   PIPELINE
   ========================================================= */

document
    .querySelectorAll(".stage")
    .forEach(function(stageButton) {

        stageButton.addEventListener(
            "click",
            async function() {

                const stageName =
                    stageButton.textContent
                        .trim()
                        .replace(/\s+/g, " ");

                console.log(
                    "Selected compiler stage:",
                    stageName
                );

                await runStage(stageName);

            }
        );

    });


showSource();
