def format_currency(value):
    return f"R$ {value:,.2f}"

def calculate_percentage_change(old_value, new_value):
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100

def format_date(date):
    return date.strftime("%d/%m/%Y")

def extract_sector_data(stock_data):
    sectors = {}
    for stock in stock_data:
        sector = stock['setor']
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(stock)
    return sectors

def get_last_n_months_data(stock_data, n):
    return stock_data[-n:] if len(stock_data) >= n else stock_data

def prepare_comparison_data(selected_stock, comparison_stock):
    return {
        'selected_stock': selected_stock,
        'comparison_stock': comparison_stock
    }