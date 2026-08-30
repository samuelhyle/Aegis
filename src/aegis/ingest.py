import argparse

from .store import SyntheaStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    store = SyntheaStore(args.directory)
    tables = store.load()
    print("Loaded Synthea tables:")
    for name, df in tables.items():
        print(f"  {name:16} {len(df):>8} rows")
