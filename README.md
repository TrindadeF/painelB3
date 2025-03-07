# Brazil Stocks Dashboard

This project is a dashboard application built using Python, Tkinter, and the InvestPy library. It provides users with the ability to view and compare stock prices of Brazilian companies, along with their performance metrics over various time frames.

## Features

- Display stock information including sector, stock code, and stock name.
- Show performance metrics for stocks over different periods: year, last 12 months, month, week, and day.
- Compare stock performance visually through interactive charts.
- User-friendly interface built with Tkinter.

## Project Structure

```
brazil-stocks-dashboard
├── src
│   ├── main.py               # Entry point of the application
│   ├── dashboard              # Contains UI and chart components
│   │   ├── __init__.py
│   │   ├── ui.py             # UI components for the dashboard
│   │   └── charts.py         # Chart generation and updates
│   ├── data                  # Data fetching and processing
│   │   ├── __init__.py
│   │   ├── stock_data.py     # Functions to fetch stock data using InvestPy
│   │   └── market_sectors.py  # Functions to categorize stocks by sector
│   └── utils                 # Utility functions
│       ├── __init__.py
│       └── helpers.py        # Helper functions for data processing
├── requirements.txt          # Project dependencies
├── config.json               # Configuration settings
└── README.md                 # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/brazil-stocks-dashboard.git
   cd brazil-stocks-dashboard
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python src/main.py
   ```

2. Use the dashboard to select stocks and view their performance metrics. You can also compare different stocks using the provided charts.

## Dependencies

- Python 3.x
- Tkinter
- InvestPy
- Other libraries as specified in `requirements.txt`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.