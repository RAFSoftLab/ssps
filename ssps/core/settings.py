from decouple import config


class Settings:
    pass
    # DB_ADAPTER = config("SSPS_DB_ADAPTER", default="") # TODO: implement default memory db?


settings = Settings()
