from app.db.clickhouse import get_clickhouse_client
from app.repositories.analytics_repository import AnalyticsRepository


def main() -> None:
    client = get_clickhouse_client()

    try:
        repository = AnalyticsRepository(client)

        healthcheck_result = repository.healthcheck()

        if healthcheck_result != 1:
            raise RuntimeError("ClickHouse healthcheck failed")

        repository.create_tables()

        result = client.query("SHOW TABLES")

        print("ClickHouse tables:")
        for row in result.result_rows:
            print(f"- {row[0]}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
