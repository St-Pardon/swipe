from flask import Blueprint, render_template

base_bp = Blueprint('base', __name__)

@base_bp.route("/", methods=["GET"])
def home():
    return render_template('index.html')
