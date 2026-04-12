import json
import csv
import pandas as pd

from src.client import Client
from src.sale import Sale
from src.client_collection import ClientCollection
from src.sales_collection import SalesCollection
from src.functional_utils import filter_sales_by_category


def load_clients(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    clients = []
    for item in data:
        client = Client(
            item["client_id"],
            item["name"],
            item["country"],
            item["signup_date"]
        )
        clients.append(client)

    return clients


def load_sales(path):
    sales = []
    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            sale = Sale(
                row["sale_id"],
                int(row["client_id"]),
                row["product"],
                row["category"],
                float(row["amount"]),
                row["date"]
            )
            sales.append(sale)

    return sales


def generate_report():
    clients = load_clients("data/clients.json")
    sales = load_sales("data/sales.csv")

    client_collection = ClientCollection(clients)
    sales_collection = SalesCollection(sales)

    total_clients = len(clients)
    total_sales = len(sales)
    total_revenue = sum(sale.amount for sale in sales)

    clients_report = []
    for client in clients:
        total_spent = sales_collection.total_amount_by_client(client.client_id)
        sale_count = len(sales_collection.sales_by_client(client.client_id))
        average_sale = sales_collection.average_sale_by_client(client.client_id)

        clients_report.append({
            "client_id": client.client_id,
            "name": client.name,
            "total_spent": total_spent,
            "sale_count": sale_count,
            "average_sale": average_sale
        })

    countries = set(client.country for client in clients)
    top_client_by_country = {}

    for country in countries:
        country_clients = client_collection.clients_by_country(country)
        top_client = None
        max_spent = -1

        for client in country_clients:
            spent = sales_collection.total_amount_by_client(client.client_id)
            if spent > max_spent:
                max_spent = spent
                top_client = client.name

        top_client_by_country[country] = top_client

    df = pd.read_csv("data/sales.csv")

    sales_by_category = df.groupby("category")["amount"].sum().to_dict()

    minimum_spending = 500
    high_spending_clients = []

    for client in clients:
        total_spent = sales_collection.total_amount_by_client(client.client_id)
        if total_spent > minimum_spending:
            high_spending_clients.append(client.name)

    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    monthly_sales = df.groupby("year_month")["amount"].sum().to_dict()

    specific_category = "Electronics"
    sales_in_category = filter_sales_by_category(sales, specific_category)
    category_counts = {}

    for sale in sales_in_category:
        if sale.client_id not in category_counts:
            category_counts[sale.client_id] = 0
        category_counts[sale.client_id] += 1

    top_client_in_category = None
    max_count = -1

    for client_id, count in category_counts.items():
        if count > max_count:
            max_count = count
            client = client_collection.get_client_by_id(client_id)
            top_client_in_category = client.name

    report = {
        "summary": {
            "total_clients": total_clients,
            "total_sales": total_sales,
            "total_revenue": total_revenue
        },
        "clients": clients_report,
        "top_client_by_country": top_client_by_country,
        "sales_by_category": sales_by_category,
        "top_client_in_category": {
            specific_category: top_client_in_category
        },
        "high_spending_clients": high_spending_clients,
        "monthly_sales": monthly_sales
    }
    return report

def main():
    report = generate_report()

    with open("report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()