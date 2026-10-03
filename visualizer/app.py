from flask import Flask, render_template, request, jsonify

from visualizer.compiler_bridge import (
    tokenize_source,
    parse_source,
    semantic_source,
    tac_source,
)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tokens", methods=["POST"])
def api_tokens():

    data = request.get_json()
    source = data.get("source", "")

    try:

        tokens = tokenize_source(source)

        return jsonify({
            "success": True,
            "tokens": tokens,
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error),
        }), 400


@app.route("/api/parse", methods=["POST"])
def api_parse():

    data = request.get_json()
    source = data.get("source", "")

    try:

        ast = parse_source(source)

        return jsonify({
            "success": True,
            "ast": ast,
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error),
        }), 400


@app.route("/api/semantic", methods=["POST"])
def api_semantic():

    data = request.get_json()
    source = data.get("source", "")

    try:

        result = semantic_source(source)

        return jsonify(result)

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error),
        }), 400


@app.route("/api/tac", methods=["POST"])
def api_tac():
    data = request.get_json()
    source = data.get("source", "")

    try:
        result = tac_source(source)
        return jsonify(result)

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

@app.route("/api/cfg", methods=["POST"])
def api_cfg():
    from visualizer.compiler_bridge import cfg_source

    data = request.get_json()
    source = data.get("source", "")

    try:
        return jsonify(cfg_source(source))
    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    from visualizer.compiler_bridge import optimize_source

    data = request.get_json()
    source = data.get("source", "")

    try:
        return jsonify(optimize_source(source))
    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


@app.route("/api/run", methods=["POST"])
def api_run():
    from visualizer.compiler_bridge import run_source

    data = request.get_json()
    source = data.get("source", "")

    try:
        return jsonify(run_source(source))
    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
