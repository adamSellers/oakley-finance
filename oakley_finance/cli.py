"""Unified CLI dispatcher for all oakley-finance commands."""

import argparse
import sys


def cmd_brief(args):
    from oakley_finance import daily_briefing
    print(daily_briefing.build_briefing())


def cmd_forex(args):
    from oakley_finance import market_data
    if args.dashboard:
        dashboard = market_data.get_forex_dashboard()
        from oakley_finance.common.formatting import format_section_header
        print(format_section_header("Forex Dashboard"))
        for pair in dashboard:
            print(market_data.format_forex_output(pair))
            print()
    else:
        pair = args.pair or None
        data = market_data.get_forex(pair=pair, period=args.period)
        print(market_data.format_forex_output(data))


def cmd_news(args):
    from oakley_finance import news_scanner
    news = news_scanner.scan_news(category=args.category, limit=args.limit)
    print(news_scanner.format_news_output(news, verbose=args.verbose))


def cmd_portfolio(args):
    from oakley_finance import portfolio

    if args.action == "show":
        holdings = portfolio.get_portfolio_with_prices()
        print(portfolio.format_portfolio_output(holdings))
    elif args.action == "add":
        if not args.symbol or args.shares is None or args.price is None:
            print("Usage: portfolio add <symbol> <shares> <price>")
            sys.exit(1)
        result = portfolio.add_holding(args.symbol, args.shares, args.price)
        print(result)
    elif args.action == "remove":
        if not args.symbol:
            print("Usage: portfolio remove <symbol> [shares]")
            sys.exit(1)
        result = portfolio.remove_holding(args.symbol, args.shares)
        print(result)
    elif args.action == "sectors":
        sectors = portfolio.get_sector_allocation()
        print(portfolio.format_sector_output(sectors))
    elif args.action == "performance":
        holdings = portfolio.get_portfolio_with_prices()
        print(portfolio.format_portfolio_output(holdings))
    else:
        holdings = portfolio.get_portfolio_with_prices()
        print(portfolio.format_portfolio_output(holdings))


def cmd_alerts(args):
    from oakley_finance import alerts

    if args.action == "list":
        all_alerts = alerts.list_alerts()
        print(alerts.format_alerts_list(all_alerts))
    elif args.action == "add":
        if args.alert_type == "price":
            if not args.symbol or not args.condition or args.target is None:
                print("Usage: alerts add price <symbol> <above|below> <target>")
                sys.exit(1)
            result = alerts.add_price_alert(args.symbol, args.condition, args.target)
            print(result)
        elif args.alert_type == "news":
            if not args.keywords:
                print("Usage: alerts add news <keyword1> [keyword2] ...")
                sys.exit(1)
            result = alerts.add_news_alert(args.keywords)
            print(result)
        elif args.alert_type == "volatility":
            if not args.symbol or args.threshold is None:
                print("Usage: alerts add volatility <symbol> <threshold_pct>")
                sys.exit(1)
            result = alerts.add_volatility_alert(args.symbol, args.threshold)
            print(result)
        else:
            print("Alert types: price, news, volatility")
    elif args.action == "remove":
        if args.alert_id is None:
            print("Usage: alerts remove <id>")
            sys.exit(1)
        result = alerts.remove_alert(args.alert_id)
        print(result)
    elif args.action == "check":
        triggered = alerts.check_alerts()
        if triggered:
            print(alerts.format_triggered_output(triggered))
        else:
            print("No alerts triggered.")
    else:
        all_alerts = alerts.list_alerts()
        print(alerts.format_alerts_list(all_alerts))


def cmd_calendar(args):
    from oakley_finance import economic_calendar
    events = economic_calendar.get_upcoming_events(
        days=args.days, country=args.country
    )
    from oakley_finance.common.formatting import format_section_header
    print(format_section_header(f"Economic Calendar (next {args.days} days)"))
    print(economic_calendar.format_calendar_output(events))


def cmd_movers(args):
    from oakley_finance import market_data
    from oakley_finance.common.formatting import format_section_header
    movers = market_data.get_movers(market=args.market, limit=args.limit)
    print(format_section_header(f"Market Movers — {args.market.upper()}"))
    print(market_data.format_movers_output(movers))


def cmd_commodities(args):
    from oakley_finance import market_data
    from oakley_finance.common.formatting import format_section_header
    commodities = market_data.get_commodities()
    print(format_section_header("Commodities"))
    print(market_data.format_commodities_output(commodities))


def main():
    parser = argparse.ArgumentParser(
        prog="oakley-finance",
        description="Oakley Finance — market data, news, portfolio & alerts",
    )
    subparsers = parser.add_subparsers(dest="command")

    # brief
    subparsers.add_parser("brief", help="Full morning briefing")

    # forex
    forex_p = subparsers.add_parser("forex", help="Forex data")
    forex_p.add_argument("--pair", type=str, default=None, help="Forex pair symbol")
    forex_p.add_argument("--period", type=str, default="5d", help="History period")
    forex_p.add_argument("--dashboard", action="store_true", help="Show all pairs")

    # news
    news_p = subparsers.add_parser("news", help="Financial news")
    news_p.add_argument("--category", type=str, default=None, help="Filter by category")
    news_p.add_argument("--limit", type=int, default=10, help="Number of items")
    news_p.add_argument("--verbose", action="store_true", help="Show links and scores")

    # portfolio
    port_p = subparsers.add_parser("portfolio", help="Portfolio management")
    port_p.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "add", "remove", "sectors", "performance"],
    )
    port_p.add_argument("symbol", nargs="?", default=None)
    port_p.add_argument("shares", nargs="?", type=float, default=None)
    port_p.add_argument("price", nargs="?", type=float, default=None)

    # alerts
    alert_p = subparsers.add_parser("alerts", help="Alert management")
    alert_p.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "add", "remove", "check"],
    )
    alert_p.add_argument("alert_type", nargs="?", default=None, help="price|news|volatility")
    alert_p.add_argument("symbol", nargs="?", default=None)
    alert_p.add_argument("condition", nargs="?", default=None, help="above|below")
    alert_p.add_argument("target", nargs="?", type=float, default=None)
    alert_p.add_argument("--keywords", nargs="+", default=None)
    alert_p.add_argument("--threshold", type=float, default=None)
    alert_p.add_argument("--alert-id", type=int, default=None)

    # calendar
    cal_p = subparsers.add_parser("calendar", help="Economic calendar")
    cal_p.add_argument("--days", type=int, default=7, help="Days ahead")
    cal_p.add_argument("--country", type=str, default=None, help="Filter by country (AU, US, EU, CN)")

    # movers
    mov_p = subparsers.add_parser("movers", help="Top market movers")
    mov_p.add_argument("--market", type=str, default="asx", help="Market")
    mov_p.add_argument("--limit", type=int, default=5, help="Number of movers")

    # commodities
    subparsers.add_parser("commodities", help="Commodity prices")

    args = parser.parse_args()

    commands = {
        "brief": cmd_brief,
        "forex": cmd_forex,
        "news": cmd_news,
        "portfolio": cmd_portfolio,
        "alerts": cmd_alerts,
        "calendar": cmd_calendar,
        "movers": cmd_movers,
        "commodities": cmd_commodities,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
