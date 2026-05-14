from modules import (
    Constants,
    Flask,
    render_template,
)


def run_app():
    app = Flask(
        __name__,
        static_folder="static/",  # static folder of app.py
        template_folder="templates/daisyUI",  # templates folder of app.py
    )

    # App secret key
    app.secret_key = Constants.APP_SECRET_KEY

    ## Context processors
    from utils.context_processors.constants import constants
    from utils.context_processors.dateTime import dateTime

    ## Register context processors
    app.context_processor(dateTime)
    app.context_processor(constants)

    # Register Index page
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def index(path):
        return render_template("base.html")

    return app
