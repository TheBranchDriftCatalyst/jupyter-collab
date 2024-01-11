import requests
from icecream import ic


class NotionConnector:
    # Shared map across all instances. we are going to want to probably store this in redis eventually.
    database_registry = {}

    def __init__(self, api_key, database_id, database_name) -> None:
        self.api_key = api_key
        self.database_id = database_id
        self.database_name = database_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json",
        }
        # Register the database name and hash to the shared map
        self.register_database()

    def get_database(self, db_name=None):
        # Retrieve the database ID from the registry using the provided db_name or the instance's database_name
        db_id = self.database_registry.get(db_name or self.database_name)

        # Ensure the database ID was found; otherwise, raise an error
        if db_id is None:
            raise ValueError(f"Database '{db_name or self.database_name}' not found.")

        # Initialize the response variable before entering the loop
        response = {"has_more": True, "next_cursor": None}
        records = []
        while response["has_more"]:
            response = requests.post(
                f"https://api.notion.com/v1/databases/{db_id}/query",
                json={}
                if response["next_cursor"] is None
                else {"start_cursor": response["next_cursor"]},
                headers=self.headers,
            ).json()
            # ic("response", response)
            # Ensure that 'results' key exists in the response
            if "results" in response:
                # TODO: need to fix this here, its getting an array
                records += list(
                    map(self.extract_all_property_values, response["results"])
                )
                # records.extend(self.extract_all_property_values(response["results"]))
            else:
                print("eof reached")
                break  # Break the loop if there are no results, avoiding an infinite loop

        return records

    def register_database(self):
        # Using the database ID as a unique identifier for the map
        NotionConnector.database_registry[self.database_name] = self.database_id

    @classmethod
    def get_registered_databases(cls):
        """Return all registered databases."""
        return cls.database_registry

    @staticmethod
    def extract_all_property_values(page_data):
        """
        Extracts values for all properties from a Notion page object.

        :param page_data: A dictionary representing a Notion page object.
        :return: A dictionary with property names and their corresponding values.
        """
        ic(f"page_data: {page_data}")
        properties = page_data.get("properties", {})
        values = {}

        for name, prop in properties.items():
            prop_type = prop.get("type")

            if prop_type == "checkbox":
                values[name] = prop.get("checkbox")
            elif prop_type == "multi_select":
                values[name] = [item["name"] for item in prop.get("multi_select", [])]
            elif prop_type == "formula":
                values[name] = prop["formula"].get(prop["formula"]["type"])
            elif prop_type == "date":
                values[name] = prop["date"]
            # elif prop_type == "rich_text":
                # ic(prop, name)
                # values[name] = prop
            elif prop_type == "title":
                values[name] = "".join([text["plain_text"] for text in prop["title"]])
            else:
                values[name] = f"unsupported {name} type {prop_type}"

        return values
