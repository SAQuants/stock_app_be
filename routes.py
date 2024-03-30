from fastapi import FastAPI, Request, HTTPException
# $ uvicorn routes:app --reload
from fastapi.templating import Jinja2Templates
import json
import pandas as pd

from services.market_data import get_supported_symbols, get_symbol_ts, get_symbol_info
from services.backtest_launcher import execute_backtest

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_response_type(request: Request):
    accept = request.headers["accept"]
    # print(f'accept: {accept}, len(accept.split(",")): {len(accept.split(","))}')
    if len(accept.split(",")) > 1:
        print('response_type: html')
        return 'html'
    else:
        print('response_type: data')
        return 'data'


@app.get("/")
def get_symbol_list(request: Request):
    # print(dir(request))
    # print(request.headers)
    symbol_info_list = get_supported_symbols()
    if get_response_type(request) == 'html':
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"supported_symbols": symbol_info_list})
    else:
        return symbol_info_list


@app.get("/symbol/{symbol}")
def get_details(request: Request, symbol):
    # print(request.headers)

    backtest = request.query_params.get('backtest', None)
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    print(f'get_details params: {symbol}, {backtest}, {start_date}, {end_date}')
    if backtest is None:
        return get_symbol_data(request, symbol)
    else:
        return get_backtest_results(request, symbol, backtest, start_date, end_date)


def get_symbol_data(request, symbol):
    symbol_info = get_symbol_info(symbol)
    stock_ts = get_symbol_ts(symbol)
    if get_response_type(request) == 'html':
        return templates.TemplateResponse(
            request=request,
            name="symbol_price.html",
            context={
                "time_series": stock_ts.to_dict('records'),
                "symbol_info": symbol_info
            }
        )
    else:
        return stock_ts.to_json()


def get_backtest_results(request, symbol, backtest_name, start_date, end_date):
    backtest_results = execute_backtest(symbol, backtest_name,  start_date, end_date)
    # print(f'get_backtest_results::{backtest_results}')
    if backtest_results["status"] != 200:
        print(f'get_backtest_results --> HTTPException')
        raise HTTPException(status_code=backtest_results["status"],
                            detail=backtest_results)
    else:
        print(f'get_backtest_results --> Success')
        return backtest_results
