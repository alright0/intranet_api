from flask import Blueprint, render_template
from werkzeug.exceptions import HTTPException

error_handlers = Blueprint("handlers", __name__)


@error_handlers.app_errorhandler(HTTPException)
def default_errhandler(e):
    return render_template("errors/error.html", error=e), e.code
