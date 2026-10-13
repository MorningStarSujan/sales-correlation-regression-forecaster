import os
from flask import Flask, render_template, request, session, g
from config import Config
from database.db import init_db
from database.models import SettingsModel
from services.currency_service import CurrencyService
from routes import (
    dashboard_bp,
    upload_bp,
    analysis_bp,
    regression_bp,
    forecast_bp,
    history_bp,
    export_bp
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize SQLite database schema
    init_db()
    
    # Register Route Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(regression_bp)
    app.register_blueprint(forecast_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(export_bp)
    
    @app.before_request
    def resolve_currency():
        currency_code = (
            request.args.get('currency') or
            request.cookies.get('selected_currency') or
            session.get('selected_currency') or
            SettingsModel.get('selected_currency', 'USD')
        )
        supported = CurrencyService.get_supported_currencies()
        if not currency_code or currency_code.upper() not in supported:
            currency_code = 'USD'
        else:
            currency_code = currency_code.upper()

        g.currency_code = currency_code
        g.currency = CurrencyService.get_currency(currency_code)
        session['selected_currency'] = currency_code

    @app.context_processor
    def inject_currency_context():
        curr_code = getattr(g, 'currency_code', 'USD')
        return {
            'current_currency': getattr(g, 'currency', CurrencyService.get_currency(curr_code)),
            'current_currency_code': curr_code,
            'available_currencies': CurrencyService.get_supported_currencies()
        }

    # Custom Jinja filters
    @app.template_filter('currency')
    def currency_filter(value, currency_code=None):
        code = currency_code or getattr(g, 'currency_code', 'USD')
        return CurrencyService.format(value, code)

    @app.template_filter('number_fmt')
    def number_filter(value):
        try:
            val = float(value)
            return f"{int(val):,}" if val.is_integer() else f"{val:,.2f}"
        except (ValueError, TypeError):
            return "0"

    @app.template_filter('pct_fmt')
    def pct_filter(value):
        try:
            return f"{float(value):+.2f}%"
        except (ValueError, TypeError):
            return "N/A"
            
    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html', error=str(e)), 500
        
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_DEBUG') == '1'
    )
