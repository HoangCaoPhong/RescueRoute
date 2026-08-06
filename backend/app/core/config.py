from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173"
    
    # Dataset Settings
    GRAPH_NODES_PATH: str = "../data/samples/nodes.csv"
    GRAPH_EDGES_PATH: str = "../data/samples/edges.csv"
    
    # External Services
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    OPENROUTESERVICE_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
