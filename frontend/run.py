from app.app import run_app
from constant import Constants

# run App
app = run_app()

if __name__ == "__main__":
    app.run(debug=True, host=Constants.HOST, port=Constants.PORT)
