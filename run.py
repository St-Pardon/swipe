import os

from app import create_app

app = create_app()


def run_dev_server():
    app.run(debug=True)


def run_prod_server():
    from waitress import serve

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    serve(app, host=host, port=port)


if __name__ == '__main__':
    environment = os.getenv('FLASK_ENV', os.getenv('ENV', 'development')).lower()
    if environment == 'development':
        run_dev_server()
    else:
        run_prod_server()
