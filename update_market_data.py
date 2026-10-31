from project_structure.data.pipeline import run_data_pipeline




if __name__ == "__main__":
    print("Starting FinSight market data update...")

    updated_data = run_data_pipeline(
        start="2010-01-01",
    )

    print("\nMarket data updated successfully!")

    for ticker, history in updated_data.items():
        print(
            f"{ticker}: "
            f"{history.index.min().date()} to "
            f"{history.index.max().date()} "
            f"({len(history)} observations)"
        )