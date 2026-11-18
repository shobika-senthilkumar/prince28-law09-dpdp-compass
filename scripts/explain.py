from dotenv import load_dotenv
from sqlalchemy import text

from dpdpcompass.db.session import engine


def main() -> None:
    load_dotenv()

    with engine.connect() as connection:
        connection.execute(text("SET enable_seqscan = off"))

        result = connection.execute(
            text(
                """
                EXPLAIN
                SELECT id
                FROM documents
                WHERE metadata @> '{"source": "India Code"}'::jsonb;
                """
            )
        )

        for row in result:
            print(row[0])


if __name__ == "__main__":
    main()
