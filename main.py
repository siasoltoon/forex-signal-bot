from app import create_app


def main() -> None:
    app = create_app()
    app.start()


if __name__ == "__main__":
    main()
