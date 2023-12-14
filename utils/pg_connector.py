from prisma import Prisma


def main() -> None:
    db = Prisma()
    db.connect()

    # write your queries here

    db.disconnect()


if __name__ == "__main__":
    main()
