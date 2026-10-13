"""
Currency Service for Sales Correlation & Regression Forecaster.
Provides comprehensive multi-currency definitions, symbols, and formatting
without altering underlying numeric data or calculations.
"""

class CurrencyService:
    SUPPORTED_CURRENCIES = {
        'USD': {
            'code': 'USD',
            'symbol': '$',
            'name': 'US Dollar ($)',
            'flag': '🇺🇸',
            'position': 'prefix',
            'decimals': 2
        },
        'EUR': {
            'code': 'EUR',
            'symbol': '€',
            'name': 'Euro (€)',
            'flag': '🇪🇺',
            'position': 'prefix',
            'decimals': 2
        },
        'GBP': {
            'code': 'GBP',
            'symbol': '£',
            'name': 'British Pound (£)',
            'flag': '🇬🇧',
            'position': 'prefix',
            'decimals': 2
        },
        'JPY': {
            'code': 'JPY',
            'symbol': '¥',
            'name': 'Japanese Yen (¥)',
            'flag': '🇯🇵',
            'position': 'prefix',
            'decimals': 2
        },
        'INR': {
            'code': 'INR',
            'symbol': '₹',
            'name': 'Indian Rupee (₹)',
            'flag': '🇮🇳',
            'position': 'prefix',
            'decimals': 2
        },
        'CAD': {
            'code': 'CAD',
            'symbol': 'CA$',
            'name': 'Canadian Dollar (CA$)',
            'flag': '🇨🇦',
            'position': 'prefix',
            'decimals': 2
        },
        'AUD': {
            'code': 'AUD',
            'symbol': 'A$',
            'name': 'Australian Dollar (A$)',
            'flag': '🇦🇺',
            'position': 'prefix',
            'decimals': 2
        },
        'CHF': {
            'code': 'CHF',
            'symbol': 'CHF',
            'name': 'Swiss Franc (CHF)',
            'flag': '🇨🇭',
            'position': 'prefix',
            'decimals': 2
        },
        'CNY': {
            'code': 'CNY',
            'symbol': 'CN¥',
            'name': 'Chinese Yuan (CN¥)',
            'flag': '🇨🇳',
            'position': 'prefix',
            'decimals': 2
        },
        'BRL': {
            'code': 'BRL',
            'symbol': 'R$',
            'name': 'Brazilian Real (R$)',
            'flag': '🇧🇷',
            'position': 'prefix',
            'decimals': 2
        },
        'MXN': {
            'code': 'MXN',
            'symbol': 'Mex$',
            'name': 'Mexican Peso (Mex$)',
            'flag': '🇲🇽',
            'position': 'prefix',
            'decimals': 2
        },
        'SGD': {
            'code': 'SGD',
            'symbol': 'S$',
            'name': 'Singapore Dollar (S$)',
            'flag': '🇸🇬',
            'position': 'prefix',
            'decimals': 2
        },
        'AED': {
            'code': 'AED',
            'symbol': 'AED',
            'name': 'UAE Dirham (AED)',
            'flag': '🇦🇪',
            'position': 'prefix',
            'decimals': 2
        },
        'KRW': {
            'code': 'KRW',
            'symbol': '₩',
            'name': 'South Korean Won (₩)',
            'flag': '🇰🇷',
            'position': 'prefix',
            'decimals': 2
        },
        'SEK': {
            'code': 'SEK',
            'symbol': 'kr',
            'name': 'Swedish Krona (kr)',
            'flag': '🇸🇪',
            'position': 'suffix',
            'decimals': 2
        },
        'NZD': {
            'code': 'NZD',
            'symbol': 'NZ$',
            'name': 'New Zealand Dollar (NZ$)',
            'flag': '🇳🇿',
            'position': 'prefix',
            'decimals': 2
        },
        'ZAR': {
            'code': 'ZAR',
            'symbol': 'R',
            'name': 'South African Rand (R)',
            'flag': '🇿🇦',
            'position': 'prefix',
            'decimals': 2
        }
    }

    DEFAULT_CURRENCY = 'USD'

    @classmethod
    def get_supported_currencies(cls):
        """Returns dictionary of all supported currencies."""
        return cls.SUPPORTED_CURRENCIES

    @classmethod
    def get_currency(cls, code):
        """Returns details for a given currency code, falling back to default."""
        if not code or not isinstance(code, str):
            return cls.SUPPORTED_CURRENCIES[cls.DEFAULT_CURRENCY]
        return cls.SUPPORTED_CURRENCIES.get(code.upper(), cls.SUPPORTED_CURRENCIES[cls.DEFAULT_CURRENCY])

    @classmethod
    def get_symbol(cls, code):
        """Returns currency symbol for given code."""
        return cls.get_currency(code)['symbol']

    @classmethod
    def format(cls, value, currency_code=None):
        """
        Formats a numeric value using the selected currency's symbol and rules.
        Does not convert the underlying value.
        """
        info = cls.get_currency(currency_code)
        try:
            val = float(value)
        except (ValueError, TypeError):
            val = 0.0

        is_negative = val < 0
        abs_val = abs(val)
        formatted_num = f"{abs_val:,.2f}"

        symbol = info['symbol']
        pos = info.get('position', 'prefix')

        if pos == 'suffix':
            res = f"{formatted_num} {symbol}"
        else:
            sep = " " if len(symbol) >= 3 and not symbol.endswith('$') else ""
            res = f"{symbol}{sep}{formatted_num}"

        return f"-{res}" if is_negative else res

    @classmethod
    def format_short(cls, value, currency_code=None):
        """
        Formats large numbers for compact axis ticks (e.g. $10k, €5M).
        """
        info = cls.get_currency(currency_code)
        symbol = info['symbol']
        pos = info.get('position', 'prefix')
        sep = " " if len(symbol) >= 3 and not symbol.endswith('$') else ""

        try:
            val = float(value)
        except (ValueError, TypeError):
            val = 0.0

        is_negative = val < 0
        abs_val = abs(val)

        if abs_val >= 1_000_000:
            num_str = f"{abs_val / 1_000_000:.1f}M".replace('.0M', 'M')
        elif abs_val >= 1_000:
            num_str = f"{abs_val / 1_000:.0f}k"
        else:
            num_str = f"{abs_val:g}"

        if pos == 'suffix':
            res = f"{num_str} {symbol}"
        else:
            res = f"{symbol}{sep}{num_str}"

        return f"-{res}" if is_negative else res
