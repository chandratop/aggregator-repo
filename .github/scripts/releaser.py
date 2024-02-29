import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Get action')
    parser.add_argument('action', help='update or release')
    args = parser.parse_args()

    if args.action == "update":
        pass