from analytics.engine import AnalyticsEngine
def test_overview():
    x=AnalyticsEngine().overview();assert x["revenue"]>=0
def test_sales():
    x=AnalyticsEngine().sales_performance();assert len(x["top_products"])>0
